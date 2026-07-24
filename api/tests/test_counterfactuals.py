"""
Session 11 — counterfactual generation (§8 field · §33 row 10 done-when ·
§30.4/§30.8 surfaces).

Covers: generation from factors (ordering, top_k, template config), kind
eligibility (risk/forecast per the UI surfaces; others empty by default,
configurable), determinism, validation (non-blank, P9 guard on generated
text), persistence into lumen_insight.counterfactuals JSON + round-trip,
serialization, lifecycle/verified-gate integration, edge cases (no factors),
and the §33 row 10 criterion as a CI invariant: every risk/forecast
prediction insight carries factors, counterfactuals, limitations.

Self-contained: in-memory SQLite, no live PostgreSQL.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.contracts.insight import Factor, Insight
from lumen.db.models.intelligence import LumenInsight
from lumen.intelligence import counterfactual as cf
from lumen.intelligence import engine as engine_mod
from lumen.intelligence.guards import P9ViolationError
from lumen.graph.projection import run_projection
from lumen.jobs.resolve import run_resolution
from lumen.jobs.seed import seed_database

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)

FACTORS = [
    Factor(label="weekly case volume", weight=0.55, detail=None),
    Factor(label="charge delay days", weight=0.30, detail=None),
    Factor(label="gravity mean", weight=0.15, detail=None),
    Factor(label="charge count", weight=0.05, detail=None),
]


def _fresh_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


@pytest.fixture(scope="module")
def predicted():
    s = _fresh_session()
    seed_database(s)
    run_resolution(s)
    run_projection(s, now=NOW)
    engine_mod.run_predictions(s, now=NOW)
    return s


# ── generation ─────────────────────────────────────────────────────────────

def test_generation_from_factors_top_k_and_ordering():
    out = cf.generate_counterfactuals(FACTORS)
    assert len(out) == cf.DEFAULT_TOP_K
    # ordered by |weight| descending — top factor grounds the first sentence
    assert "weekly case volume" in out[0]
    assert "charge delay days" in out[1]
    assert "gravity mean" in out[2]
    assert all(s.strip() for s in out)                     # never blank
    # top_k is configuration
    assert len(cf.generate_counterfactuals(FACTORS, top_k=1)) == 1
    assert len(cf.generate_counterfactuals(FACTORS, top_k=10)) == len(FACTORS)


def test_generation_is_deterministic():
    a = cf.generate_counterfactuals(FACTORS)
    b = cf.generate_counterfactuals(list(reversed(FACTORS)))   # input order irrelevant
    assert a == b


def test_template_is_configuration():
    out = cf.generate_counterfactuals(FACTORS, top_k=1,
                                      template="Absent {label} ({weight}), weaker.")
    assert out == ["Absent weekly case volume (0.55), weaker."]


def test_no_factors_yields_no_counterfactuals():
    assert cf.generate_counterfactuals([]) == []           # §8 allows empty


def test_blank_template_rejected():
    with pytest.raises(ValueError, match="blank"):
        cf.generate_counterfactuals(FACTORS, top_k=1, template="   ")


# ── kind eligibility (§30.4 risk · §30.8 forecast) ─────────────────────────

def test_kind_eligibility_defaults_and_config():
    assert cf.counterfactuals_for("risk", FACTORS)
    assert cf.counterfactuals_for("forecast", FACTORS)
    assert cf.counterfactuals_for("anomaly", FACTORS) == []
    assert cf.counterfactuals_for("linkage", FACTORS) == []
    # eligibility is configuration
    assert cf.counterfactuals_for("anomaly", FACTORS, kinds=("anomaly",))


# ── validation: P9 never reaches generated display text ────────────────────

def test_p9_factor_label_fails_generation():
    poisoned = [Factor(label="complainant caste ratio", weight=0.9, detail=None)]
    with pytest.raises(P9ViolationError):
        cf.generate_counterfactuals(poisoned)


# ── §33 row 10 done-when, enforced in CI ───────────────────────────────────

def test_row10_criterion_insights_carry_factors_counterfactuals_limitations(predicted):
    rows = [i for i in predicted.query(LumenInsight).all()
            if i.kind in ("risk", "forecast")]
    assert rows
    for i in rows:
        assert i.factors, f"{i.insight_id} missing factors"
        assert i.counterfactuals, f"{i.insight_id} missing counterfactuals"
        assert i.limitations, f"{i.insight_id} missing limitations"


def test_non_mandated_kinds_carry_empty_field(predicted):
    others = [i for i in predicted.query(LumenInsight).all()
              if i.kind in ("anomaly", "linkage")]
    assert others
    assert all(i.counterfactuals == [] for i in others)


# ── persistence, serialization, lifecycle integration ──────────────────────

def test_persistence_round_trip(predicted):
    from lumen.intelligence.lifecycle import load_insight

    row = next(i for i in predicted.query(LumenInsight).all() if i.kind == "risk")
    assert isinstance(row.counterfactuals, list) and row.counterfactuals
    loaded = load_insight(predicted, row.insight_id, classification="INTERNAL")
    assert loaded.counterfactuals == row.counterfactuals
    again = Insight.model_validate_json(loaded.model_dump_json())
    assert again.counterfactuals == loaded.counterfactuals


def test_regeneration_is_stable_upsert(predicted):
    row = next(i for i in predicted.query(LumenInsight).all() if i.kind == "risk")
    before = list(row.counterfactuals)
    engine_mod.run_predictions(predicted, now=NOW)         # re-run batch
    after = predicted.get(LumenInsight, row.insight_id).counterfactuals
    assert after == before                                  # deterministic, no dupes


def test_insight_with_counterfactuals_passes_verified_gate(predicted):
    from lumen.intelligence.lifecycle import load_insight, to_verified

    row = next(i for i in predicted.query(LumenInsight).all()
               if i.kind == "risk" and i.confidence >= 0.35)
    insight = load_insight(predicted, row.insight_id, classification="INTERNAL")
    assert insight.counterfactuals
    assert to_verified(predicted, insight).lifecycle_state == "verified"
