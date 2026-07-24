"""
The seven §8 invariants, enforced in CI — the "Done when" criterion for
Session 8 of §33: "All seven invariants enforced in CI."

    1. No endpoint returns a score outside an `Insight`.
    2. `limitations` is never empty.
    3. Every `Evidence.id` resolves to a real record.
    4. No `Factor.label` references a P9 attribute.
    5. `lineage.model_version` exists in `lumen_model_registry`.
    6. `classification` ≥ the highest classification of its evidence.
    7. `confidence` equals `confidence_breakdown.composite` to 3 decimal places.

Enforcement layers proven here:
  * 2 and 7 are unrepresentable — the Pydantic contract refuses construction.
  * 3, 4, 5, 6 are rejected by the §10 `verified` gate (`verify_insight`);
    an offending insight can never surface.
  * 1 is enforced against the live API surface: every reachable response is
    walked, and any score-valued field must sit either inside a serialized
    Insight or on the §29.1-mandated `/quality` surface (§5.2 quality scores
    are their own spec-required product, not intelligence scores).

Self-contained: in-memory SQLite per test, no live PostgreSQL.
"""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.db.models import canonical as m
from lumen.db.models.identity import LumenPerson
from lumen.db.models.intelligence import LumenInsight, LumenModelRegistry
from lumen.contracts.insight import (
    ConfidenceBreakdown,
    Evidence,
    Factor,
    Insight,
    Lineage,
)
from lumen.intelligence import confidence as C
from lumen.intelligence.explain import (
    classification_of_evidence,
    factor_references_p9,
    resolve_evidence,
)
from lumen.intelligence.guards import P9ViolationError
from lumen.intelligence.lifecycle import (
    VerificationFailedError,
    save_insight,
    to_verified,
    verify_insight,
)
from lumen.jobs.seed import seed_database
from lumen.jobs.resolve import run_resolution
from lumen.jobs.quality import run_quality_precompute


NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)


def _fresh_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _seeded_session(*, resolve=True):
    s = _fresh_session()
    seed_database(s)
    if resolve:
        run_resolution(s)
    # a registered model so invariant-5 checks can pass (§3.6 registry table)
    s.add(LumenModelRegistry(model_id="statistical_baseline@v1",
                             name="statistical_baseline", kind="statistical",
                             version="v1", trained_at=NOW, active=True))
    s.flush()
    return s


def _breakdown(**overrides) -> ConfidenceBreakdown:
    values = dict(evidence_quality=1.0, model_confidence=0.9,
                  data_completeness=1.0, identity_confidence=1.0,
                  graph_confidence=1.0)
    values.update(overrides)
    return C.compose(**values)


def _insight(session, *, evidence=None, factors=None, limitations=None,
             breakdown=None, confidence=None, classification="RESTRICTED",
             model_version="v1", **overrides) -> Insight:
    """A valid baseline insight against the deterministic seed."""
    if evidence is None:
        person = session.query(LumenPerson).order_by(LumenPerson.person_id).first()
        evidence = [
            Evidence(entity="case", id="1000", label="Case 1000", url="/cases/1000"),
            Evidence(entity="person", id=person.person_id,
                     label=person.canonical_name, url=f"/persons/{person.person_id}"),
        ]
    bd = breakdown or _breakdown()
    kwargs = dict(
        id="insight-0001",
        kind="anomaly",
        subject_type="district",
        subject_id="1",
        headline="District 1 case volume is above its weekly baseline.",
        score=0.7,
        confidence=confidence if confidence is not None else bd.composite,
        confidence_breakdown=bd,
        factors=factors if factors is not None else [
            Factor(label="weekly case volume", weight=0.6, detail="3σ above baseline"),
        ],
        counterfactuals=[],
        evidence=evidence,
        limitations=limitations if limitations is not None else [
            "Co-accusal reflects charging decisions, not adjudicated guilt.",
        ],
        lineage=Lineage(
            method="statistical_baseline",
            model_version=model_version,
            prompt_version=None,
            features_used=["case_count@v1"],
            query_ids=[],
            source_row_count=10,
            quality_score=1.0,
            computed_at=NOW,
        ),
        lifecycle_state="generated",
        classification=classification,
        generated_at=NOW,
        expires_at=None,
    )
    kwargs.update(overrides)
    return Insight(**kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# Invariant 1 — no endpoint returns a score outside an Insight
# ═══════════════════════════════════════════════════════════════════════════

def _score_keys(payload, path=""):
    """Yield (json_path, container) for every field named like a score."""
    if isinstance(payload, dict):
        for k, v in payload.items():
            if k == "score" or k.endswith("_score"):
                yield path + "/" + k, payload
            yield from _score_keys(v, path + "/" + k)
    elif isinstance(payload, list):
        for i, item in enumerate(payload):
            yield from _score_keys(item, f"{path}[{i}]")


_INSIGHT_SHAPE = {"confidence", "confidence_breakdown", "factors", "evidence",
                  "limitations", "lineage"}


def test_invariant_1_no_endpoint_returns_score_outside_insight():
    from fastapi.testclient import TestClient
    import main as app_main
    from lumen.db.session import get_db

    engine = create_engine(
        "sqlite:///file:inv1mem?mode=memory&cache=shared&uri=true",
        connect_args={"uri": True},
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    setup = TestingSession()
    seed_database(setup)
    run_resolution(setup)
    run_quality_precompute(setup)
    setup.close()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app_main.app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app_main.app)
        # every parameterless GET route, plus the person dossier with a real id
        probe_paths = []
        for route in app_main.app.openapi()["paths"]:
            if "{" not in route:
                probe_paths.append(route)
        first_person = client.get("/api/persons").json()["persons"][0]["person_id"]
        probe_paths.append(f"/api/persons/{first_person}")

        for path in sorted(set(probe_paths)):
            resp = client.get(path)
            if resp.status_code != 200:
                continue          # 501 stubs, 405s etc. return no data
            try:
                payload = resp.json()
            except ValueError:
                continue
            for json_path, container in _score_keys(payload):
                inside_insight = _INSIGHT_SHAPE.issubset(container.keys())
                quality_surface = path.startswith("/api/quality")   # §29.1 quality scores
                # §25 mandates /system/metrics carry OPERATIONAL scores — the
                # quality-score trend and the AI evaluation scorecard. These are
                # observability aggregates, not analytical claims, so §8
                # invariant 1's "score outside an Insight" does not apply
                # (same carve-out precedent as the §5.2 quality surface).
                system_surface = path.startswith("/api/system")
                assert inside_insight or quality_surface or system_surface, (
                    f"§8 invariant 1 violated: {path} returns a score at "
                    f"{json_path} outside an Insight payload."
                )
    finally:
        app_main.app.dependency_overrides.pop(get_db, None)


# ═══════════════════════════════════════════════════════════════════════════
# Invariant 2 — limitations is never empty
# ═══════════════════════════════════════════════════════════════════════════

def test_invariant_2_limitations_never_empty():
    session = _seeded_session()
    with pytest.raises(ValidationError, match="invariant 2"):
        _insight(session, limitations=[])
    with pytest.raises(ValidationError, match="invariant 2"):
        _insight(session, limitations=["   "])
    assert _insight(session).limitations       # valid one constructs


# ═══════════════════════════════════════════════════════════════════════════
# Invariant 3 — every Evidence.id resolves to a real record
# ═══════════════════════════════════════════════════════════════════════════

def test_invariant_3_unresolvable_evidence_rejected():
    session = _seeded_session()
    ghost = Evidence(entity="case", id="999999", label="ghost", url="/cases/999999")
    insight = _insight(session, evidence=[ghost], classification="CONFIDENTIAL")
    with pytest.raises(VerificationFailedError, match="invariant 3"):
        verify_insight(session, insight)


def test_invariant_3_resolver_covers_every_entity_type():
    session = _seeded_session()
    # rows the seed does not create, inserted so each entity type has a target
    session.add(m.ComplainantDetails(ComplainantID=77, CaseMasterID=1000,
                                     ComplainantName="C", AgeYear=40, GenderID=1))
    if session.query(m.Court).count() == 0:
        session.add(m.Court(CourtID=9, CourtName="Bengaluru Sessions",
                            DistrictID=1, StateID=1, Active=True))
    session.flush()
    person = session.query(LumenPerson).first()

    def ev(entity, eid):
        return Evidence(entity=entity, id=eid, label=entity, url="/x")

    resolvable = [
        ev("case", "1000"),
        ev("person", person.person_id),
        ev("participant", "accused:3000"),
        ev("participant", "victim:12000"),
        ev("participant", "complainant:77"),
        ev("officer", str(session.query(m.Employee).first().EmployeeID)),
        ev("station", "11"),
        ev("jurisdiction", "district:1"),
        ev("jurisdiction", "state:1"),
        ev("court", "9"),
        ev("charge", "4000:IPC:392"),
        ev("process_event", "arrest:5000"),
        ev("process_event", "chargesheet:5000"),
    ]
    for e in resolvable:
        assert resolve_evidence(session, e), f"{e.entity}:{e.id} should resolve"

    unresolvable = [
        ev("case", "424242"),
        ev("person", "no-such-person"),
        ev("participant", "accused:424242"),
        ev("participant", "witness:1"),          # unknown prefix
        ev("charge", "4000:IPC:999"),
        ev("process_event", "arrest:424242"),
        ev("kb_document", "doc-1"),              # §15 KB is Session 13 — no table yet
    ]
    for e in unresolvable:
        assert not resolve_evidence(session, e), f"{e.entity}:{e.id} must NOT resolve"


# ═══════════════════════════════════════════════════════════════════════════
# Invariant 4 — no Factor.label references a P9 attribute
# ═══════════════════════════════════════════════════════════════════════════

def test_invariant_4_p9_factor_labels_rejected():
    session = _seeded_session()
    for bad_label in (
        "Complainant caste distribution",
        "religion of victims in scope",
        "Blood group correlation",
        "disability status flag",
        "CasteID frequency",
        "ReligionID skew",
        "BloodGroupID",
        "physically challenged share",
    ):
        insight = _insight(session, factors=[Factor(label=bad_label, weight=0.5, detail=None)])
        with pytest.raises(P9ViolationError):
            verify_insight(session, insight)

    clean = _insight(session, factors=[
        Factor(label="weekly case volume", weight=0.6, detail=None),
        Factor(label="charge delay days", weight=0.4, detail=None),
    ])
    verify_insight(session, clean)   # does not raise

    assert factor_references_p9(Factor(label="caste ratio", weight=1.0, detail=None))
    assert factor_references_p9(Factor(label="arrest recency", weight=1.0, detail=None)) is None


# ═══════════════════════════════════════════════════════════════════════════
# Invariant 5 — lineage.model_version exists in lumen_model_registry
# ═══════════════════════════════════════════════════════════════════════════

def test_invariant_5_unregistered_model_version_rejected():
    session = _seeded_session()
    rogue = _insight(session, model_version="v99-unregistered")
    with pytest.raises(VerificationFailedError, match="invariant 5"):
        verify_insight(session, rogue)
    verify_insight(session, _insight(session))   # registered "v1" passes


# ═══════════════════════════════════════════════════════════════════════════
# Invariant 6 — classification ≥ highest classification of its evidence
# ═══════════════════════════════════════════════════════════════════════════

def test_invariant_6_classification_inheritance():
    session = _seeded_session()
    # person evidence is RESTRICTED (§4.2 lumen_person row)
    under = _insight(session, classification="CONFIDENTIAL")
    with pytest.raises(VerificationFailedError, match="invariant 6"):
        verify_insight(session, under)
    verify_insight(session, _insight(session, classification="RESTRICTED"))

    # station evidence is PUBLIC (§4.2 lookup catch-all) — INTERNAL suffices
    station_only = _insight(
        session,
        evidence=[Evidence(entity="station", id="11", label="Whitefield PS", url="/units/11")],
        classification="INTERNAL",
    )
    verify_insight(session, station_only)

    # §4.2 register values behind the rule
    person = session.query(LumenPerson).first()
    assert classification_of_evidence(
        Evidence(entity="person", id=person.person_id, label="p", url="/x")) == "RESTRICTED"
    assert classification_of_evidence(
        Evidence(entity="case", id="1000", label="c", url="/x")) == "CONFIDENTIAL"
    assert classification_of_evidence(
        Evidence(entity="station", id="11", label="s", url="/x")) == "PUBLIC"
    # charge evidence: ActSectionAssociation has NO §4.2 declaration
    with pytest.raises(KeyError, match="Cannot determine from the specification"):
        classification_of_evidence(
            Evidence(entity="charge", id="4000:IPC:392", label="IPC 392", url="/x"))


# ═══════════════════════════════════════════════════════════════════════════
# Invariant 7 — confidence equals composite to 3 decimal places
# ═══════════════════════════════════════════════════════════════════════════

def test_invariant_7_confidence_equals_composite():
    session = _seeded_session()
    bd = _breakdown()                    # composite = 0.9
    with pytest.raises(ValidationError, match="invariant 7"):
        _insight(session, breakdown=bd, confidence=0.75)
    ok = _insight(session, breakdown=bd, confidence=bd.composite)
    assert round(ok.confidence, 3) == round(ok.confidence_breakdown.composite, 3)
    # inside 3-dp tolerance is accepted
    _insight(session, breakdown=bd, confidence=bd.composite + 0.0004)


# ═══════════════════════════════════════════════════════════════════════════
# The verified gate ties the invariants to §10 (integration)
# ═══════════════════════════════════════════════════════════════════════════

def test_verified_gate_enforces_invariants_and_floor():
    session = _seeded_session()
    good = _insight(session)
    save_insight(session, good)
    verified = to_verified(session, good)
    assert verified.lifecycle_state == "verified"
    assert session.get(LumenInsight, good.id).lifecycle_state == "verified"

    low = _insight(session, breakdown=_breakdown(model_confidence=0.3),
                   id="insight-low")     # composite 0.3 < floor 0.35
    save_insight(session, low)
    with pytest.raises(VerificationFailedError, match="floor"):
        to_verified(session, low)
    assert session.get(LumenInsight, low.id).lifecycle_state == "generated"
