"""
Session 10 — §13 prediction engine.

Covers all six §13 model rows against the deterministic seed, the §13 rules
as CI invariants (feature importances → factors; NO P9 attribute consumed —
enforced and tested; training window stated in limitations; batch-score into
tables, API reads), §3.6 persistence (lumen_district_risk, lumen_hotspot),
PredictionContract validation/serialization, deterministic + idempotent
re-runs, and integration: predictions become Session 8 Insights (factors,
counterfactuals field, limitations) that pass the verified gate where
applicable.

Self-contained: in-memory SQLite, no live PostgreSQL, no Catalyst services.
"""
from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.contracts.insight import Factor
from lumen.contracts.prediction import PredictionContract
from lumen.db.models import canonical as m
from lumen.db.models.intelligence import LumenInsight, LumenModelRegistry
from lumen.db.models.prediction import LumenDistrictRisk, LumenHotspot
from lumen.intelligence import anomaly as anomaly_mod
from lumen.intelligence import engine as engine_mod
from lumen.intelligence import hotspots as hotspots_mod
from lumen.intelligence import linkage as linkage_mod
from lumen.intelligence import outcome as outcome_mod
from lumen.intelligence import risk as risk_mod
from lumen.intelligence.guards import P9ViolationError
from lumen.graph.projection import run_projection
from lumen.jobs.resolve import run_resolution
from lumen.jobs.seed import seed_database

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)


def _fresh_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


@pytest.fixture(scope="module")
def s():
    session = _fresh_session()
    seed_database(session)
    run_resolution(session)
    run_projection(session, now=NOW)          # linkage reads the precomputed graph
    engine_mod.run_predictions(session, now=NOW)
    return session


# ── district risk (§13 row 1) ──────────────────────────────────────────────

def test_risk_bands_persisted_with_score_and_factors(s):
    rows = s.query(LumenDistrictRisk).all()
    assert rows and {r.district_id for r in rows} >= {1, 2, 3}
    for r in rows:
        assert r.band in risk_mod.BANDS
        assert 0.0 <= r.score <= 1.0
        assert r.factors and all("label" in f and "weight" in f for f in r.factors)
        assert r.model_version == "v1"
    # the seeded district-2 spike week banded High
    assert any(r.district_id == 2 and r.band == "High" for r in rows)


# ── hotspots (§13 row 2) ───────────────────────────────────────────────────

def test_hotspot_dbscan_persisted(s):
    rows = s.query(LumenHotspot).all()
    assert rows
    for h in rows:
        assert h.method == "dbscan_haversine"
        assert h.weight >= 5                    # min_samples floor
        assert h.window_start is not None and h.window_end is not None


def test_hotspot_detects_seed_guarantee_g1():
    """§32 g1's 'visually obvious hotspot' (district 1, ~10 cases within a
    few hundred metres of 12.9716/77.5946) is detected when the scoring
    window covers it."""
    session = _fresh_session()
    seed_database(session)
    contracts = hotspots_mod.score_hotspots(session, window_days=400, now=NOW)
    assert contracts
    hit = [c for c in contracts
           if abs(c.output["centroid"][0] - 12.9716) < 0.01
           and abs(c.output["centroid"][1] - 77.5946) < 0.01]
    assert hit and hit[0].output["weight"] >= 10


# ── volume anomaly (§13 row 3 — both detectors reported) ───────────────────

def test_volume_anomaly_detects_g6_spike_both_detectors(s):
    spikes = [i for i in s.query(LumenInsight).all() if i.kind == "anomaly"
              and "spiked" in i.headline]
    assert spikes                                # §32 g6 district-week ≥3σ
    # both detectors reported on the contract output → check via re-score
    contracts = anomaly_mod.score_volume_anomaly(s, now=NOW)
    assert contracts
    for c in contracts:
        out = c.output
        assert out["sigma"] >= 3.0 and "baseline_mean" in out and "count" in out
        assert "isolation_forest_flag" in out and "isolation_forest_score" in out
        assert out["zscore_flag"] is True


# ── case linkage (§13 row 4) ───────────────────────────────────────────────

def test_linkage_ranks_seed_signature_pair(s):
    contracts = linkage_mod.score_case_linkage(s, now=NOW)
    by_subject = {c.subject_id: c for c in contracts}
    assert "4000" in by_subject                  # §32 g4 shared-signature case
    ranked = by_subject["4000"].output["ranked_linked_cases"]
    assert ranked[0]["case_id"] == "4001" or any(r["case_id"] == "4001" for r in ranked)
    linked_4001 = next(r for r in ranked if r["case_id"] == "4001")
    assert linked_4001["components"].get("signature_jaccard", 0) >= 0.6
    # ranked descending
    sims = [r["similarity"] for r in ranked]
    assert sims == sorted(sims, reverse=True)


# ── case outcome (§13 row 5) ───────────────────────────────────────────────

def test_outcome_probabilities_over_abc(s):
    contracts = outcome_mod.score_case_outcome(s, now=NOW)
    assert contracts                             # open cases scored
    for c in contracts:
        probs = c.output["probabilities"]
        assert set(probs) == {"A", "B", "C"}
        assert abs(sum(probs.values()) - 1.0) < 0.01
        assert c.factors                          # feature importances
    # trained on the §32 g10 cstype distribution: subjects exclude labelled cases
    labelled = {cs.CaseMasterID for cs in s.query(m.ChargesheetDetails).all()}
    assert all(int(c.subject_id) not in labelled for c in contracts)


# ── reporting-delay outlier (§13 row 6) ────────────────────────────────────

def test_reporting_delay_outlier_unit_flagged():
    session = _fresh_session()
    seed_database(session)
    # a z-score of one outlying unit against n units is capped near sqrt(n−1),
    # so a 3σ detection needs a reasonably wide fleet of normal units
    next_id = 80000
    for unit in range(200, 220):                  # 20 units, ~2h normal delay
        session.add(m.CaseMaster(
            CaseMasterID=next_id, CrimeNo=f"CN{next_id}", PoliceStationID=unit,
            CrimeRegisteredDate=date(2026, 6, 1),
            IncidentFromDate=datetime(2026, 6, 1, 0, 0),
            InfoReceivedPSDate=datetime(2026, 6, 1, 2, 0)))
        next_id += 1
    session.add(m.CaseMaster(
        CaseMasterID=next_id, CrimeNo=f"CN{next_id}", PoliceStationID=999,
        CrimeRegisteredDate=date(2026, 6, 1),
        IncidentFromDate=datetime(2026, 6, 1, 0, 0),
        InfoReceivedPSDate=datetime(2026, 6, 20, 0, 0)))    # ~456h outlier
    session.flush()
    contracts = anomaly_mod.score_reporting_delay(session, now=NOW)
    assert any(c.subject_id == "999" for c in contracts)
    flagged = next(c for c in contracts if c.subject_id == "999")
    assert flagged.output["zscore"] >= 3.0


# ── §13 rules as CI invariants ─────────────────────────────────────────────

def test_no_model_consumes_p9_attribute(monkeypatch):
    """§13: 'No model consumes a P9 attribute (enforced, tested).'"""
    session = _fresh_session()
    seed_database(session)
    for mod, fn in ((risk_mod, lambda: risk_mod.score_district_risk(session)),
                    (hotspots_mod, lambda: hotspots_mod.score_hotspots(session)),
                    (anomaly_mod, lambda: anomaly_mod.score_volume_anomaly(session)),
                    (linkage_mod, lambda: linkage_mod.score_case_linkage(session)),
                    (outcome_mod, lambda: outcome_mod.score_case_outcome(session))):
        monkeypatch.setattr(mod, "FEATURE_COLUMNS",
                            [("ComplainantDetails", "CasteID")])
        with pytest.raises(P9ViolationError):
            fn()
        monkeypatch.undo()


def test_every_prediction_states_training_window(s):
    for contracts in (risk_mod.score_district_risk(s, now=NOW),
                      anomaly_mod.score_volume_anomaly(s, now=NOW),
                      outcome_mod.score_case_outcome(s, now=NOW)):
        for c in contracts:
            assert any("window" in l.lower() or "trained on" in l.lower()
                       for l in c.limitations)


def test_contract_rejects_missing_training_window():
    with pytest.raises(ValidationError, match="training window"):
        PredictionContract(
            model="district_risk", kind="Classification",
            subject_type="district", subject_id="1", output={},
            factors=[Factor(label="x", weight=1.0, detail=None)],
            limitations=["insufficient data for this district"],
            model_version="v1", computed_at=NOW)


def test_contract_serialization_round_trip(s):
    c = risk_mod.score_district_risk(s, now=NOW)[0]
    again = PredictionContract.model_validate_json(c.model_dump_json())
    assert again == c


# ── batch-score into tables; API reads (no request-time scoring) ───────────

def test_rerun_is_deterministic_and_idempotent(s):
    before_risk = [(r.district_id, r.band, r.score) for r in
                   s.query(LumenDistrictRisk).order_by(LumenDistrictRisk.district_id)]
    before_insights = s.query(LumenInsight).count()
    summary1 = engine_mod.run_predictions(s, now=NOW)
    summary2 = engine_mod.run_predictions(s, now=NOW)
    assert summary1 == summary2
    after_risk = [(r.district_id, r.band, r.score) for r in
                  s.query(LumenDistrictRisk).order_by(LumenDistrictRisk.district_id)]
    assert before_risk == after_risk              # deterministic (seeded models)
    assert s.query(LumenInsight).count() == before_insights   # upserts, no dupes


# ── §33 done-when + Session 8/9 integration ────────────────────────────────

def test_prediction_insights_carry_factors_counterfactuals_limitations(s):
    """§33 Session 10: 'Insights carry factors, counterfactuals, limitations.'
    (Counterfactual GENERATION is excluded from this session by instruction;
    the field is carried.)"""
    insights = [i for i in s.query(LumenInsight).all()
                if i.kind in {"risk", "anomaly", "linkage", "forecast"}]
    assert insights
    for i in insights:
        assert i.factors, f"{i.insight_id} missing factors"
        assert i.limitations, f"{i.insight_id} missing limitations"
        assert i.counterfactuals is not None      # field carried (empty allowed)
        assert i.lifecycle_state == "generated"   # §10: nothing surfaces unverified


def test_model_versions_registered_for_invariant_5(s):
    names = {r.name for r in s.query(LumenModelRegistry).all()}
    assert set(engine_mod.ALL_MODELS) <= names


def test_prediction_insight_passes_verified_gate(s):
    """A risk insight (no evidence chips, registered version, INTERNAL,
    confidence above floor) clears the Session 8 verified gate."""
    from lumen.intelligence.lifecycle import to_verified
    from lumen.intelligence.lifecycle import load_insight

    row = next(i for i in s.query(LumenInsight).all()
               if i.kind == "risk" and i.confidence >= 0.35)
    insight = load_insight(s, row.insight_id, classification="INTERNAL")
    verified = to_verified(s, insight)
    assert verified.lifecycle_state == "verified"


def test_engine_summary_covers_all_six_models(s):
    summary = engine_mod.run_predictions(s, now=NOW)
    assert summary["predictions"] == summary["insights"] >= 1
    # reporting_delay may legitimately be zero on the seed; the other five fire
    for model in ("district_risk", "hotspots", "volume_anomaly",
                  "case_linkage", "case_outcome"):
        assert summary.get(model, 0) >= 1, f"{model} produced nothing on the seed"
