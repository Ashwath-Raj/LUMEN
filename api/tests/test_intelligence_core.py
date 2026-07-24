"""
Session 8 core behaviour — §8 models, §9 confidence, §10 lifecycle,
serialization and §3.6 persistence. (The seven CI invariants themselves are
`test_insight_invariants.py`; this file covers everything else Session 8
requires: construction, explainability structures, confidence computation,
every lifecycle transition, lineage, validation, serialization, persistence,
contract rules.)

Self-contained: in-memory SQLite per test, no live PostgreSQL.
"""
from datetime import datetime, timezone
from itertools import product

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.db.models.identity import LumenPerson
from lumen.db.models.intelligence import LumenInsight, LumenModelRegistry
from lumen.db.models.quality import LumenQualityScore
from lumen.contracts.insight import (
    ConfidenceBreakdown,
    Evidence,
    Factor,
    Insight,
    InsightContract,
    Lineage,
)
from lumen.intelligence import confidence as C
from lumen.intelligence import lifecycle as L
from lumen.jobs.seed import seed_database
from lumen.jobs.resolve import run_resolution
from lumen.jobs.quality import run_quality_precompute

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)


def _fresh_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _seeded_session():
    s = _fresh_session()
    seed_database(s)
    run_resolution(s)
    s.add(LumenModelRegistry(model_id="statistical_baseline@v1",
                             name="statistical_baseline", kind="statistical",
                             version="v1", trained_at=NOW, active=True))
    s.flush()
    return s


def _lineage(**overrides) -> Lineage:
    values = dict(method="statistical_baseline", model_version="v1",
                  prompt_version=None, features_used=["case_count@v1"],
                  query_ids=["q1"], source_row_count=10, quality_score=0.87,
                  computed_at=NOW)
    values.update(overrides)
    return Lineage(**values)


def _insight(session, **overrides) -> Insight:
    bd = overrides.pop("breakdown", None) or C.compose(model_confidence=0.9)
    person = session.query(LumenPerson).order_by(LumenPerson.person_id).first()
    kwargs = dict(
        id="insight-core-1",
        kind="anomaly",
        subject_type="district",
        subject_id="1",
        headline="District 1 case volume is above its weekly baseline.",
        score=0.7,
        confidence=bd.composite,
        confidence_breakdown=bd,
        factors=[Factor(label="weekly case volume", weight=0.6, detail="3σ")],
        counterfactuals=["If the spike week is excluded, volume is at baseline."],
        evidence=[
            Evidence(entity="case", id="1000", label="Case 1000", url="/cases/1000"),
            Evidence(entity="person", id=person.person_id,
                     label=person.canonical_name, url=f"/persons/{person.person_id}"),
        ],
        limitations=["Not valid for districts with fewer than 50 records."],
        lineage=_lineage(),
        lifecycle_state="generated",
        classification="RESTRICTED",
        generated_at=NOW,
        expires_at=None,
    )
    kwargs.update(overrides)
    return Insight(**kwargs)


# ── §8 construction + §7 contract rules ────────────────────────────────────

def test_insight_constructs_with_all_spec_fields():
    session = _seeded_session()
    ins = _insight(session)
    assert ins.contract_version == "v1"           # §7 rule 2
    assert ins.kind == "anomaly" and ins.subject_type == "district"
    assert ins.confidence_breakdown.composite == ins.confidence
    assert ins.lineage.features_used == ["case_count@v1"]
    assert InsightContract is Insight             # §7 name for the same contract


def test_vocabularies_are_closed():
    session = _seeded_session()
    with pytest.raises(ValidationError):
        _insight(session, kind="prophecy")
    with pytest.raises(ValidationError):
        _insight(session, subject_type="galaxy")
    with pytest.raises(ValidationError):
        _insight(session, classification="TOP_SECRET")
    with pytest.raises(ValidationError):
        _insight(session, lifecycle_state="quarantined")
    with pytest.raises(ValidationError):
        Evidence(entity="rumour", id="1", label="x", url="/x")


def test_serialization_round_trip():
    session = _seeded_session()
    ins = _insight(session)
    again = Insight.model_validate_json(ins.model_dump_json())
    assert again == ins


# ── §9 confidence components ───────────────────────────────────────────────

def test_evidence_quality_ratio_cap_and_na():
    assert C.evidence_quality(3, 6) == 0.5
    assert C.evidence_quality(12, 6) == 1.0                     # capped at 1
    assert C.evidence_quality(None, 6) == 1.0                   # N/A → 1.0
    assert C.evidence_quality(3, None) == 1.0
    # classification weights are caller-supplied (values undefined by spec)
    assert C.evidence_quality(2, 4, weights=[1.0, 0.5]) == pytest.approx(0.375)
    with pytest.raises(ValueError):
        C.evidence_quality(2, 4, weights=[1.0])


def test_model_confidence_probability_anomaly_and_na():
    assert C.model_confidence(0.82) == 0.82
    assert C.model_confidence(normalised_anomaly_distance=0.3) == pytest.approx(0.7)
    assert C.model_confidence() == 1.0                          # N/A → 1.0


def test_data_completeness_reads_quality_score_and_na():
    session = _seeded_session()
    assert C.data_completeness(session, "state", "karnataka") == 1.0   # no rows yet → N/A
    run_quality_precompute(session)
    row = (session.query(LumenQualityScore)
           .filter_by(scope_type="state", scope_id="karnataka", dimension="completeness")
           .first())
    assert C.data_completeness(session, "state", "karnataka") == pytest.approx(row.score)
    assert C.data_completeness(session, "district", "no-such-scope") == 1.0


def test_identity_confidence_minimum_and_na():
    session = _seeded_session()
    persons = session.query(LumenPerson).limit(2).all()
    ev = [Evidence(entity="person", id=p.person_id, label="p", url="/x") for p in persons]
    expected = min(p.resolution_confidence for p in persons)
    assert C.identity_confidence(session, ev) == pytest.approx(expected)
    assert C.identity_confidence(session, []) == 1.0            # no persons → N/A
    case_only = [Evidence(entity="case", id="1000", label="c", url="/x")]
    assert C.identity_confidence(session, case_only) == 1.0


def test_graph_confidence_edge_support_and_na():
    assert C.graph_confidence(None) == 1.0                      # no graph (Session 9) → N/A
    assert C.graph_confidence(0) == 0.0
    assert C.graph_confidence(1) == pytest.approx(0.5)
    assert C.graph_confidence(9) == pytest.approx(0.9)
    # staleness damping factor is caller-supplied (formula undefined by spec)
    assert C.graph_confidence(9, staleness_damping=0.5) == pytest.approx(0.45)


def test_composite_is_multiplicative():
    bd = C.compose(evidence_quality=0.8, model_confidence=0.9,
                   data_completeness=0.7, identity_confidence=0.66,
                   graph_confidence=1.0)
    assert bd.composite == pytest.approx(0.8 * 0.9 * 0.7 * 0.66)
    assert C.compose().composite == 1.0                         # all N/A → 1.0


def test_bands_and_weakest_component_sentence():
    assert C.band(0.80) == "High"
    assert C.band(0.95) == "High"
    assert C.band(0.79) == "Moderate"
    assert C.band(0.55) == "Moderate"
    assert C.band(0.549) == "Low"
    bd = C.compose(model_confidence=0.9, identity_confidence=0.61)
    name, value = C.weakest_component(bd)
    assert name == "identity_confidence" and value == pytest.approx(0.61)
    assert C.limitation_sentence(bd) == "limited by identity match confidence (0.61)"


# ── §10 lifecycle: every transition ────────────────────────────────────────

def test_full_legal_chain_with_persistence_and_approval_record():
    session = _seeded_session()
    ins = _insight(session)
    L.save_insight(session, ins)

    ins = L.to_verified(session, ins)
    assert ins.lifecycle_state == "verified"
    ins = L.to_approved(session, ins, approver="District SP Rao", when=NOW)
    row = session.get(LumenInsight, ins.id)
    assert row.approved_by == "District SP Rao"                 # §10 approval record
    assert row.approved_at == NOW.replace(tzinfo=None) or row.approved_at == NOW
    ins = L.to_operational(session, ins)
    ins = L.to_expired(session, ins)
    ins = L.to_archived(session, ins)
    ins = L.to_deleted(session, ins)
    assert ins.lifecycle_state == "deleted"
    assert session.get(LumenInsight, ins.id).lifecycle_state == "deleted"


def test_expiry_reachable_from_every_surfaced_state():
    for start in ("verified", "approved", "operational"):
        L.assert_transition(start, "expired")


def test_every_illegal_transition_is_rejected():
    for a, b in product(L.STATES, L.STATES):
        if (a, b) in L.LEGAL_TRANSITIONS:
            L.assert_transition(a, b)
        else:
            with pytest.raises(L.IllegalTransitionError):
                L.assert_transition(a, b)


def test_insight_never_skips_verified():
    for target in ("approved", "operational", "expired", "archived", "deleted"):
        with pytest.raises(L.IllegalTransitionError):
            L.assert_transition("generated", target)


def test_confidence_floor_keeps_insight_generated():
    session = _seeded_session()
    bd = C.compose(model_confidence=0.34)
    low = _insight(session, breakdown=bd, confidence=bd.composite, id="low-1")
    L.save_insight(session, low)
    with pytest.raises(L.VerificationFailedError, match="floor"):
        L.to_verified(session, low)
    assert session.get(LumenInsight, "low-1").lifecycle_state == "generated"
    # exactly at the floor passes it
    at_floor = C.compose(model_confidence=C.CONFIDENCE_FLOOR)
    ok = _insight(session, breakdown=at_floor, confidence=at_floor.composite, id="floor-1")
    L.save_insight(session, ok)
    assert L.to_verified(session, ok).lifecycle_state == "verified"


# ── §3.6 persistence round-trip ────────────────────────────────────────────

def test_persistence_round_trip_preserves_contract():
    session = _seeded_session()
    ins = _insight(session)
    row = L.save_insight(session, ins)
    assert row.contract_version == "v1"
    assert row.confidence_components["composite"] == ins.confidence
    assert row.limitations == ins.limitations
    assert row.factors[0]["label"] == "weekly case volume"
    assert row.lineage["model_version"] == "v1"

    loaded = L.load_insight(session, ins.id, classification=ins.classification)
    assert loaded.headline == ins.headline
    assert loaded.confidence == ins.confidence
    assert loaded.confidence_breakdown == ins.confidence_breakdown
    assert loaded.factors == ins.factors
    assert loaded.evidence == ins.evidence
    assert loaded.limitations == ins.limitations
    assert loaded.lineage == ins.lineage
    assert loaded.lifecycle_state == ins.lifecycle_state

    # save is an upsert — re-saving does not duplicate
    L.save_insight(session, ins)
    assert session.query(LumenInsight).filter_by(insight_id=ins.id).count() == 1


def test_load_missing_insight_raises():
    session = _seeded_session()
    with pytest.raises(KeyError):
        L.load_insight(session, "nope", classification="INTERNAL")
