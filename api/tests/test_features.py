"""
Session 19 — feature store (§12).

Covers: each §12 feature definition computed from upstream (resolution §6,
graph §14, quality §5, canonical §3.5) without recomputing it; the single
loader (get/list); versioned persistence + re-run invalidation; that
crime_density_km2 is deliberately absent (no District.area column); the
"one table" shape; determinism; and edge cases.

The pipeline seeds → resolves → projects → scores quality → precomputes
features, then asserts against the deterministic §32 seed.

Self-contained: in-memory SQLite, no live PostgreSQL.
"""
from datetime import date, datetime, timezone

import math
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.db.models import canonical as m
from lumen.db.models.feature import LumenFeature
from lumen.intelligence import features as F
from lumen.jobs.feature_precompute import run_feature_precompute
from lumen.graph.projection import run_projection
from lumen.jobs.quality import run_quality_precompute
from lumen.jobs.resolve import run_resolution
from lumen.jobs.seed import seed_database

NOW = datetime(2026, 7, 25, 0, 0, tzinfo=timezone.utc)

# §12's fourteen features; crime_density_km2 is the one that cannot be computed.
SPEC_FEATURES = {
    "repeat_offender_score", "mobility_index", "network_influence",
    "community_size", "arrest_delay_days", "report_delay_hours",
    "charge_delay_days", "gravity_weight", "signature_rarity",
    "crime_density_km2", "detection_rate", "officer_load",
    "repeat_victim_flag", "quality_completeness",
}
COMPUTABLE = SPEC_FEATURES - {"crime_density_km2"}


def _fresh():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


@pytest.fixture()
def fs():
    s = _fresh()
    seed_database(s)
    run_resolution(s)
    run_projection(s, now=NOW)
    run_quality_precompute(s, now=NOW)
    run_feature_precompute(s, now=NOW)
    return s


def _names(session):
    return {r.feature_name for r in F.list_features(session)}


# ── §12 coverage ────────────────────────────────────────────────────────────

def test_all_thirteen_computable_features_present(fs):
    present = _names(fs)
    assert COMPUTABLE <= present, f"missing: {COMPUTABLE - present}"


def test_crime_density_is_absent_no_area_column(fs):
    """§12 crime_density_km2 = 'cases ÷ area' — District has no area column,
    so it is never computed or persisted (Cannot determine)."""
    assert "crime_density_km2" not in _names(fs)
    assert "area" not in {c.name for c in m.District.__table__.columns}


# ── person features ─────────────────────────────────────────────────────────

def test_repeat_offender_score_is_log_scaled_linked_case_count(fs):
    rows = F.list_features(fs, entity_type="person", feature_name="repeat_offender_score")
    assert rows
    for r in rows:
        assert r.value >= 0.0                     # log1p(n) ≥ 0
    # a person linked to k cases scores log1p(k)
    from lumen.db.models.identity import LumenPersonLink
    from lumen.db.models.canonical import Accused
    # pick a person with links and verify the formula
    link = fs.query(LumenPersonLink).filter_by(state="linked").first()
    if link is not None:
        cases = {a.CaseMasterID for a in fs.query(Accused).filter(
            Accused.AccusedMasterID.in_(
                [l.accused_master_id for l in fs.query(LumenPersonLink)
                 .filter_by(person_id=link.person_id, state="linked")]))}
        feat = F.get_feature(fs, "person", link.person_id, "repeat_offender_score")
        assert feat.value == pytest.approx(math.log1p(len(cases)))


def test_network_influence_reads_eigenvector(fs):
    from lumen.db.models.graph import LumenPersonMetrics
    met = fs.query(LumenPersonMetrics).filter(LumenPersonMetrics.eigenvector.isnot(None)).first()
    if met is not None:
        feat = F.get_feature(fs, "person", met.person_id, "network_influence")
        assert feat.value == pytest.approx(float(met.eigenvector))


def test_community_size_reads_louvain(fs):
    from lumen.db.models.graph import LumenCommunity, LumenPersonMetrics
    met = fs.query(LumenPersonMetrics).filter(LumenPersonMetrics.community_id.isnot(None)).first()
    if met is not None:
        comm = fs.get(LumenCommunity, met.community_id)
        feat = F.get_feature(fs, "person", met.person_id, "community_size")
        assert feat.value == pytest.approx(float(comm.size))


def test_mobility_index_in_unit_interval(fs):
    rows = F.list_features(fs, entity_type="person", feature_name="mobility_index")
    assert rows
    for r in rows:
        assert 0.0 <= r.value <= 1.0              # distinct districts ÷ cases


# ── case features ───────────────────────────────────────────────────────────

def test_charge_delay_matches_lifecycle_seed(fs):
    """§32 g5 lifecycle case 5000 has a ~9-month charge delay."""
    feat = F.get_feature(fs, "case", "5000", "charge_delay_days")
    assert feat is not None and feat.value > 250    # registered Jan, cs Oct


def test_gravity_weight_is_gravity_offence_id(fs):
    cases = {c.CaseMasterID: c for c in fs.query(m.CaseMaster).all()}
    for r in F.list_features(fs, entity_type="case", feature_name="gravity_weight"):
        assert r.value == float(cases[int(r.entity_id)].GravityOffenceID)


def test_signature_rarity_is_inverse_frequency(fs):
    """§32 g4: cases 4000 and 4001 share an act-section signature → rarity 0.5."""
    r = F.get_feature(fs, "case", "4000", "signature_rarity")
    assert r is not None and r.value == pytest.approx(0.5)


def test_repeat_victim_flag_is_binary():
    s = _fresh()
    seed_database(s)
    # two cases, same victim (name+age), the second registered later
    s.add(m.CaseMaster(CaseMasterID=70001, CrimeNo="C70001", PoliceStationID=11,
                       CrimeRegisteredDate=date(2026, 1, 1)))
    s.add(m.CaseMaster(CaseMasterID=70002, CrimeNo="C70002", PoliceStationID=11,
                       CrimeRegisteredDate=date(2026, 3, 1)))
    s.add(m.Victim(VictimMasterID=70001, CaseMasterID=70001, VictimName="Repeat V", AgeYear=40))
    s.add(m.Victim(VictimMasterID=70002, CaseMasterID=70002, VictimName="Repeat V", AgeYear=40))
    s.flush()
    run_feature_precompute(s, now=NOW)
    first = F.get_feature(s, "case", "70001", "repeat_victim_flag")
    second = F.get_feature(s, "case", "70002", "repeat_victim_flag")
    assert first.value == 0.0                     # no prior case
    assert second.value == 1.0                    # matched the earlier one
    assert {r.value for r in F.list_features(s, feature_name="repeat_victim_flag")} <= {0.0, 1.0}


# ── district / unit features ────────────────────────────────────────────────

def test_detection_rate_ratio(fs):
    rows = F.list_features(fs, feature_name="detection_rate")
    assert rows
    for r in rows:
        assert 0.0 <= r.value <= 1.0              # cstype='A' ÷ chargesheeted
        assert r.entity_type in ("district", "unit")


def test_officer_load_cases_over_employees(fs):
    rows = F.list_features(fs, entity_type="unit", feature_name="officer_load")
    for r in rows:
        assert r.value >= 0.0


def test_quality_completeness_from_section_5_2(fs):
    from lumen.db.models.quality import LumenQualityScore
    rows = F.list_features(fs, feature_name="quality_completeness")
    assert rows
    for r in rows:
        assert r.entity_type in ("district", "unit")
        score = (fs.query(LumenQualityScore)
                 .filter_by(scope_type=r.entity_type, scope_id=r.entity_id,
                            dimension="completeness").first())
        assert score is not None and r.value == pytest.approx(float(score.score))


# ── §12 "one table, versioned" persistence ─────────────────────────────────

def test_every_feature_row_carries_version_and_computed_at(fs):
    for r in F.list_features(fs):
        assert r.version == "v1"
        assert r.computed_at is not None


def test_loader_get_and_list(fs):
    one = F.get_feature(fs, "case", "5000", "gravity_weight")
    assert one is not None and one.feature_name == "gravity_weight"
    assert F.get_feature(fs, "case", "5000", "no_such_feature") is None
    person_feats = F.list_features(fs, entity_type="person")
    assert person_feats and all(r.entity_type == "person" for r in person_feats)


def test_rerun_invalidates_and_rewrites_same_version(fs):
    before = fs.query(LumenFeature).count()
    run_feature_precompute(fs, now=NOW)           # re-run same version
    after = fs.query(LumenFeature).count()
    assert after == before                        # replaced, not duplicated
    # no duplicate composite keys
    seen = {(r.entity_type, r.entity_id, r.feature_name, r.version)
            for r in fs.query(LumenFeature).all()}
    assert len(seen) == after


def test_versions_coexist():
    s = _fresh()
    seed_database(s); run_resolution(s); run_projection(s, now=NOW)
    run_quality_precompute(s, now=NOW)
    run_feature_precompute(s, version="v1", now=NOW)
    run_feature_precompute(s, version="v2", now=NOW)
    v1 = F.list_features(s, version="v1")
    v2 = F.list_features(s, version="v2")
    assert v1 and v2 and len(v1) == len(v2)       # both versions persisted
    assert F.get_feature(s, "case", "5000", "gravity_weight", version="v2") is not None


# ── determinism ─────────────────────────────────────────────────────────────

def test_feature_computation_is_deterministic():
    def snapshot():
        s = _fresh()
        seed_database(s); run_resolution(s); run_projection(s, now=NOW)
        run_quality_precompute(s, now=NOW)
        run_feature_precompute(s, now=NOW)
        return sorted((r.entity_type, r.entity_id, r.feature_name, round(r.value, 6))
                      for r in F.list_features(s))
    assert snapshot() == snapshot()


# ── edge cases ───────────────────────────────────────────────────────────────

def test_no_upstream_yields_no_person_or_graph_features():
    """With canonical data but no resolution/graph/quality run, person and
    scope features that depend on those are absent — features are read from
    upstream, never fabricated."""
    s = _fresh()
    seed_database(s)                              # no resolve/project/quality
    run_feature_precompute(s, now=NOW)
    names = _names(s)
    assert "network_influence" not in names       # needs graph metrics
    assert "quality_completeness" not in names    # needs §5.2 scores
    # case features that need only canonical data are still present
    assert "gravity_weight" in names
