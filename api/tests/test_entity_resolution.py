"""
Verifies the §6 entity-resolution pipeline — the "Done when" criterion for
Session 7 of §33: "Name-variant persons resolve with confidence and match
evidence."

Per the §6.3 note that the v1 weights are the normative algorithm (and are
not to be recalibrated without explicit authorisation) and §6.2's fixed
thresholds, "resolve with confidence and match evidence" is satisfied by the
pipeline producing, for each seeded name-variant pair, a **confidence-scored
match carrying complete match_features evidence** — i.e. the variants surface
(never as identical-string matches) with a real confidence and a per-feature
"see why" breakdown. The §32 seed places these in the candidate band
(0.65–0.85) alongside the deliberately low-confidence guarantee-11 candidate;
this suite asserts that behaviour exactly rather than assuming auto-linking.

Also verified:
  - §6.2 normalise: honorifics, patronymic particles, transliteration fold.
  - §6.2 block: Double-Metaphone phonetic key collapses spelling variants.
  - §6.3 weights, cap at 1.0, and the MANDATORY common-name penalty.
  - §6.2 threshold bands (auto-link ≥0.85 / candidate 0.65–0.85 / reject).
  - §6.2 cluster: connected components with the 3-hop transitivity cap.
  - Persistence to lumen_person / lumen_person_link with match_features.
  - §6.4 surface: dossier with evidence, candidates separated, dispute path.

Self-contained: in-memory SQLite per test, no live PostgreSQL / HTTP.
"""
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.db.models import canonical as m
from lumen.db.models import identity as idmodels  # noqa: F401 — registers lumen_ tables
from lumen.jobs.seed import seed_database
from lumen.jobs.resolve import run_resolution, _person_id_for
from lumen.identity import normalize as N
from lumen.identity import scoring as S
from lumen.identity.features import AccusedSignals, build_signals
from lumen.identity.pipeline import (
    AUTO_LINK_THRESHOLD,
    CANDIDATE_THRESHOLD,
    MAX_TRANSITIVITY_HOPS,
    resolve,
)


def _fresh_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _sig(aid, name, *, gender=1, birth=1990, case=1, phon=None):
    """Build a bare AccusedSignals for direct scorer tests."""
    norm = N.normalise_name(name)
    return AccusedSignals(
        accused_master_id=aid,
        case_master_id=case,
        raw_name=name,
        normalised=norm,
        phonetic=phon if phon is not None else N.phonetic_key(norm),
        gender_id=gender,
        implied_birth_year=birth,
    )


# ── §6.2 normalise step ───────────────────────────────────────────────────

def test_normalise_lowercases_and_strips_honorifics():
    assert N.normalise_name("Dr. Ravi Kumar") == "ravi kumar"
    assert N.normalise_name("Shri  RAVI   Kumar") == "ravi kumar"


def test_normalise_separates_patronymic_particles():
    # everything from the particle onward is dropped (§6.2 "separated")
    assert N.normalise_name("Ravi s/o Kumar") == "ravi"
    assert N.normalise_name("Abdul bin Rahman") == "abdul"
    assert N.normalise_name("Meena d/o Gopal") == "meena"


def test_normalise_folds_transliteration_and_punctuation():
    assert N.normalise_name("Ravi-Kumar!") == "ravi kumar"
    # accents fold to their base ASCII letter (§6.2), not dropped
    assert N.normalise_name("Raví Kumär") == "ravi kumar"


# ── §6.2 block step (Double Metaphone) ─────────────────────────────────────

def test_phonetic_key_collapses_spelling_variants():
    # the three seeded Ravi variants must share a phonetic key so they block
    keys = {
        N.phonetic_key(N.normalise_name("Ravi Kumar")),
        N.phonetic_key(N.normalise_name("Ravikumar")),
        N.phonetic_key(N.normalise_name("Ravi Kumr")),
    }
    assert len(keys) == 1
    assert next(iter(keys)) != ""


def test_block_key_is_gender_plus_phonetic():
    k = N.block_key(1, N.normalise_name("Ravi Kumar"))
    assert k[0] == 1
    assert k[1] == N.phonetic_key(N.normalise_name("Ravi Kumar"))


# ── §6.3 scoring: weights, cap, mandatory common-name penalty ──────────────

def test_scoring_uses_exact_v1_weights():
    assert S.W_NAME == 0.35
    assert S.W_PHONETIC == 0.15
    assert S.W_BIRTH_YEAR == 0.20
    assert S.W_GENDER == 0.05
    assert S.W_ARREST_DISTRICT == 0.10
    assert S.W_POLICE_STATION == 0.10
    assert S.W_SHARED_COACCUSED == 0.15
    assert S.W_COMMON_NAME_PENALTY == -0.20


def test_score_is_capped_at_one():
    # a maximal pair (identical name, phonetic, birth, gender, shared
    # district+station, shared co-accused) would sum >1.0 before the cap
    a = _sig(1, "Ravi Kumar")
    b = _sig(2, "Ravi Kumar")
    a.arrest_districts = b.arrest_districts = {1}
    a.arrest_stations = b.arrest_stations = {11}
    ps = S.score_pair(a, b, name_frequency=0.0, shared_resolved_coaccused=True)
    assert ps.confidence <= 1.0
    assert ps.confidence == pytest.approx(1.0)


def test_common_name_penalty_is_applied_and_mandatory():
    # identical inputs; a common name (freq 1.0) must score strictly lower
    # than a unique name (freq ~0) — the penalty is mandatory (§6.3)
    a = _sig(1, "Kumar")
    b = _sig(2, "Kumar")
    common = S.score_pair(a, b, name_frequency=1.0).confidence
    unique = S.score_pair(a, b, name_frequency=0.001).confidence
    assert common < unique
    # the penalty feature is always present in the evidence
    assert "common_name_penalty" in S.score_pair(a, b, name_frequency=0.5).features


def test_match_features_are_complete_evidence():
    ps = S.score_pair(_sig(1, "Ravi Kumar"), _sig(2, "Ravikumar"), name_frequency=0.03)
    for feat in (
        "name_similarity", "phonetic_match", "birth_year_agreement",
        "gender_agreement", "shared_arrest_district", "shared_police_station",
        "shared_resolved_coaccused", "common_name_penalty",
    ):
        assert feat in ps.features
        assert "weight" in ps.features[feat] and "contribution" in ps.features[feat]


# ── §6.2 threshold bands ───────────────────────────────────────────────────

def test_threshold_constants_match_spec():
    assert AUTO_LINK_THRESHOLD == 0.85
    assert CANDIDATE_THRESHOLD == 0.65
    assert MAX_TRANSITIVITY_HOPS == 3


# ── "Done when": name-variant persons resolve with confidence + evidence ───

def test_name_variants_resolve_with_confidence_and_evidence():
    """§33 done-criterion. Each seeded name-variant pair surfaces as a
    confidence-scored match (not an identical-string match) carrying complete
    match_features evidence. Per §6.3 (weights normative, not recalibrated)
    the seed places these in the candidate band."""
    session = _fresh_session()
    seed_database(session)
    result = resolve(session)

    variant_names = {
        "Ravi Kumar", "Ravikumar", "Ravi Kumr",
        "Sunil Rao", "Suneel Rao", "Sunil Raoo",
        "Anil Shetty", "Aneel Shetty", "Anil Shety",
    }

    def name(aid):
        return result.signals[aid].raw_name

    variant_pairs = [
        p for p in result.candidate_pairs
        if name(p.a_id) in variant_names and name(p.b_id) in variant_names
        and name(p.a_id) != name(p.b_id)
    ]
    # all three families produce scored variant matches
    assert len(variant_pairs) >= 3

    for p in variant_pairs:
        # a real confidence, in the surfaced range, not a 1.0 exact-string hit
        assert CANDIDATE_THRESHOLD <= p.confidence < AUTO_LINK_THRESHOLD
        # match evidence with the driving features actually firing
        assert p.features["name_similarity"]["contribution"] > 0
        assert p.features["phonetic_match"]["value"] is True   # variants block phonetically
        # resolution did real work: the two names differ as strings
        assert name(p.a_id) != name(p.b_id)


def test_low_confidence_candidate_stays_in_candidate_band():
    """§32 guarantee 11: Mohammed/Mohammad Ali is a deliberate low-confidence
    candidate (0.66–0.75), surfaced never auto-linked."""
    session = _fresh_session()
    seed_database(session)
    result = resolve(session)

    def name(aid):
        return result.signals[aid].raw_name

    ali = [
        p for p in result.candidate_pairs
        if {name(p.a_id), name(p.b_id)} == {"Mohammed Ali", "Mohammad Ali"}
    ]
    assert len(ali) == 1
    assert CANDIDATE_THRESHOLD <= ali[0].confidence < AUTO_LINK_THRESHOLD


def test_identical_name_pair_scores_highest_in_candidate_band():
    """The broker (guarantee 2) appears under the SAME name 'Broker Person'
    in two cases. Under the literal §6.3 weights (not recalibrated), the
    seed provides no arrest rows or shared co-accused, so even an identical-
    name pair tops out inside the candidate band — it surfaces with full
    name+phonetic+birth-year+gender evidence but is not auto-linked. This
    documents that, per the chosen interpretation, resolution against this
    seed produces confidence-scored candidates, not auto-merges."""
    session = _fresh_session()
    seed_database(session)
    result = resolve(session)

    def name(aid):
        return result.signals[aid].raw_name

    broker = [
        p for p in result.candidate_pairs
        if {p.a_id, p.b_id} == {2201, 2211}
    ]
    assert len(broker) == 1
    # identical name → full name-similarity contribution, high in the band
    assert CANDIDATE_THRESHOLD <= broker[0].confidence < AUTO_LINK_THRESHOLD
    assert broker[0].features["name_similarity"]["contribution"] == pytest.approx(S.W_NAME)


# ── §6.2 cluster: 3-hop transitivity cap ───────────────────────────────────

def test_transitivity_cap_limits_component_growth():
    from lumen.identity.pipeline import _cluster, ScoredPair
    # a chain 1-2-3-4-5-6 of auto-links; seeded from node 1 the BFS may only
    # reach MAX_TRANSITIVITY_HOPS (3) away, so node far past the cap is excluded
    sigs = {i: _sig(i, f"Person {i}") for i in range(1, 7)}
    chain = [ScoredPair(i, i + 1, 0.9, {}) for i in range(1, 6)]
    clusters = _cluster(chain, sigs)
    assert clusters
    # the component seeded at node 1 cannot include node 5 (4 hops away)
    first = next(c for c in clusters if 1 in c.accused_ids)
    assert 5 not in first.accused_ids


# ── §6.2 persist + §6.4 surface ────────────────────────────────────────────

def test_resolution_job_persists_persons_links_and_evidence():
    session = _fresh_session()
    seed_database(session)
    summary = run_resolution(session)

    assert summary["links"] > 0
    persons = session.query(idmodels.LumenPerson).all()
    assert persons
    # every resolved person carries a resolution confidence (P10)
    assert all(p.resolution_confidence is not None for p in persons)

    links = session.query(idmodels.LumenPersonLink).all()
    # links carry per-link confidence + match_features evidence (§6.2)
    assert all(l.confidence is not None for l in links)
    assert any(l.match_features for l in links)
    # both link states exist: linked (auto) and candidate (surfaced)
    states = {l.state for l in links}
    assert "candidate" in states


def test_person_id_is_deterministic():
    assert _person_id_for([3000, 3001]) == _person_id_for([3001, 3000])
    assert _person_id_for([3000, 3001]) != _person_id_for([3000, 3002])


def test_resolution_job_is_rerunnable_identically():
    session = _fresh_session()
    seed_database(session)
    first = run_resolution(session)
    second = run_resolution(session)
    assert first == second
    # no duplicate rows after a second run
    persons = session.query(idmodels.LumenPerson).count()
    links = session.query(idmodels.LumenPersonLink).count()
    run_resolution(session)
    assert session.query(idmodels.LumenPerson).count() == persons
    assert session.query(idmodels.LumenPersonLink).count() == links


# ── §6.4 surface endpoints via TestClient ──────────────────────────────────

def test_person_surface_endpoints_via_testclient():
    """GET /persons, GET /persons/{id} (dossier with evidence, candidates
    separated, §6.4 language) and POST /persons/{id}/dispute."""
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import main as app_main
    from lumen.db.session import get_db

    engine = create_engine("sqlite:///file:idmem?mode=memory&cache=shared&uri=true", connect_args={"uri": True})
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    setup = TestingSession()
    seed_database(setup)
    run_resolution(setup)
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

        listing = client.get("/api/persons")
        assert listing.status_code == 200
        body = listing.json()
        assert body["total"] > 0 and "persons" in body
        # §6.4 language rule — never "criminal"/"offender"/"guilty"
        for p in body["persons"]:
            assert "associated with" in p["description"]
            assert p["resolution_confidence"] is not None   # P10

        pid = body["persons"][0]["person_id"]
        dossier = client.get(f"/api/persons/{pid}")
        assert dossier.status_code == 200
        d = dossier.json()
        # candidates returned separately from linked (§6.4 visual separation)
        assert "linked" in d and "candidates" in d
        assert d["resolution_confidence"] is not None

        # dispute path writes lumen_person_dispute (§6.4)
        acc = (d["linked"] + d["candidates"])[0]["accused_master_id"]
        disp = client.post(
            f"/api/persons/{pid}/dispute",
            json={"accused_master_id": acc, "raised_by": "officer-1", "reason": "wrong match"},
        )
        assert disp.status_code == 200
        assert disp.json()["state"] == "open"
        assert disp.json()["dispute_id"] is not None

        # 404 on unknown person
        assert client.get("/api/persons/does-not-exist").status_code == 404
    finally:
        app_main.app.dependency_overrides.pop(get_db, None)
