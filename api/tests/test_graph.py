"""
Session 9 — §14 graph projection, metrics, persistence.

Covers: the §14.5 pipeline (person resolution mapping, all eight structural
edge types, all five derived edge types with their §14.3 thresholds/props),
metrics (degree, betweenness, eigenvector, Louvain; §3.6 persistence with the
lumen_person FK rule), community rows with broker, re-run idempotence and
update correctness.

Fixture: the deterministic Session 5 seed + Session 7 resolution output, plus
a hand-built resolved network (lumen_person rows with state="linked" links —
legitimate precomputed §6 output) that gives the graph cross-case persons:
two clusters bridged by one broker, a repeat co-offender pair, a spree trio,
and a shared-IO pair. Self-contained in-memory SQLite; no live PostgreSQL.
"""
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.db.models import canonical as m
from lumen.db.models.graph import LumenCommunity, LumenGraphEdge, LumenPersonMetrics
from lumen.db.models.identity import LumenPerson, LumenPersonLink
from lumen.db.models.intelligence import LumenModelRegistry
from lumen.graph import metrics as gm
from lumen.graph.projection import resolve_person_nodes, run_projection
from lumen.jobs.resolve import run_resolution
from lumen.jobs.seed import seed_database

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)
OLD = date(2026, 1, 10)
RECENT = date(2026, 7, 10)


def _fresh_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _case(s, cid, unit, registered, *, lat=None, lng=None, head=1):
    s.add(m.CaseMaster(CaseMasterID=cid, CrimeNo=f"CN{cid}", CaseNo=f"C{cid}",
                       CrimeRegisteredDate=registered, PoliceStationID=unit,
                       CaseCategoryID=1, GravityOffenceID=1, CrimeMajorHeadID=head,
                       CrimeMinorHeadID=11, CaseStatusID=1,
                       latitude=lat, longitude=lng, BriefFacts="Synthetic graph case."))


def _member(s, aid, cid, person_id, name):
    """One Accused row linked (state='linked') to a resolved person."""
    s.add(m.Accused(AccusedMasterID=aid, CaseMasterID=cid, AccusedName=name,
                    AgeYear=30, GenderID=1, PersonID="A1"))
    s.add(LumenPersonLink(person_id=person_id, accused_master_id=aid,
                          confidence=0.9, match_features={}, state="linked"))


def synthetic_network(s) -> None:
    """Two clusters (districts 1 and 2) bridged by broker P-X; A1–A2 repeat
    pair; spree trio; shared-IO pair."""
    for pid, name in [("P-A1", "Alpha One"), ("P-A2", "Alpha Two"), ("P-A3", "Alpha Three"),
                      ("P-B1", "Beta One"), ("P-B2", "Beta Two"), ("P-B3", "Beta Three"),
                      ("P-X", "Broker X")]:
        s.add(LumenPerson(person_id=pid, canonical_name=name, case_count=0,
                          district_count=0, resolution_confidence=0.9,
                          method_version="v1"))
    s.flush()
    # cluster A (unit 11 → district 1), January
    _case(s, 90001, 11, OLD);            _member(s, 90010, 90001, "P-A1", "Alpha One")
    _member(s, 90011, 90001, "P-A2", "Alpha Two"); _member(s, 90012, 90001, "P-A3", "Alpha Three")
    _case(s, 90002, 11, OLD)
    _member(s, 90013, 90002, "P-A1", "Alpha One"); _member(s, 90014, 90002, "P-A2", "Alpha Two")
    # cluster B (unit 21 → district 2), January
    _case(s, 90003, 21, OLD)
    _member(s, 90015, 90003, "P-B1", "Beta One"); _member(s, 90016, 90003, "P-B2", "Beta Two")
    _member(s, 90017, 90003, "P-B3", "Beta Three")
    # broker bridges, July (recent — drives Q9 growth)
    _case(s, 90004, 11, RECENT)
    _member(s, 90018, 90004, "P-X", "Broker X"); _member(s, 90019, 90004, "P-A1", "Alpha One")
    _case(s, 90005, 21, RECENT)
    _member(s, 90020, 90005, "P-X", "Broker X"); _member(s, 90021, 90005, "P-B1", "Beta One")
    _case(s, 90030, 11, RECENT)   # second recent A-side tie → Q9's ≥50% growth
    _member(s, 90024, 90030, "P-X", "Broker X"); _member(s, 90025, 90030, "P-A2", "Alpha Two")
    # a court so TRIED_AT projects
    s.add(m.Court(CourtID=9001, CourtName="Bengaluru Sessions", DistrictID=1,
                  StateID=1, Active=True))
    s.query(m.CaseMaster).filter(m.CaseMaster.CaseMasterID == 90001).first().CourtID = 9001
    # spree trio: same head, ≤5 km, ≤14 days, far from all seed coords
    _case(s, 90006, 11, date(2026, 7, 1), lat=15.0000, lng=76.0000)
    _case(s, 90007, 11, date(2026, 7, 4), lat=15.0050, lng=76.0050)
    _case(s, 90008, 11, date(2026, 7, 8), lat=15.0100, lng=76.0100)
    # shared IO: P-A1 and P-B1 arrested by the same investigating officer
    io = s.query(m.Employee).first().EmployeeID
    s.add(m.ArrestSurrender(ArrestSurrenderID=90001, CaseMasterID=90001,
                            ArrestSurrenderTypeID=1, ArrestSurrenderDate=OLD,
                            ArrestSurrenderDistrictId=1, PoliceStationID=11,
                            IOID=io, AccusedMasterID=90010, IsAccused=True,
                            IsComplainantAccused=False))
    s.add(m.ArrestSurrender(ArrestSurrenderID=90002, CaseMasterID=90003,
                            ArrestSurrenderTypeID=1, ArrestSurrenderDate=OLD,
                            ArrestSurrenderDistrictId=2, PoliceStationID=21,
                            IOID=io, AccusedMasterID=90015, IsAccused=True,
                            IsComplainantAccused=False))
    s.flush()


@pytest.fixture()
def projected():
    s = _fresh_session()
    seed_database(s)
    run_resolution(s)
    synthetic_network(s)
    run_projection(s, now=NOW)
    return s


def _edges(s, rel):
    return s.query(LumenGraphEdge).filter(LumenGraphEdge.rel == rel).all()


# ── person resolution mapping (§14.5 "resolve persons (§6)") ───────────────

def test_resolution_mapping_linked_and_singleton(projected):
    mapping = resolve_person_nodes(projected)
    assert mapping[90010] == "P-A1"                 # linked → lumen_person UUID
    assert mapping[90019] == "P-A1"                 # same person across cases
    assert mapping[3000] == "accused:3000"          # candidate/singleton stays own identity


# ── structural edges (§14.3 — all eight) ───────────────────────────────────

def test_all_eight_structural_edge_types_project(projected):
    for rel in ("ACCUSED_IN", "REGISTERED_AT", "IN", "REGISTERED",
                "INVESTIGATED", "CHARGED_UNDER", "TRIED_AT", "ARRESTED_IN"):
        assert _edges(projected, rel), f"{rel} missing"
    # semantic node ids, never table rows (§14.2)
    e = _edges(projected, "ACCUSED_IN")[0]
    assert e.src_type == "person" and e.dst_type == "case"
    inn = _edges(projected, "IN")[0]
    assert inn.dst_id.startswith("district:")


# ── derived edges (§14.3 table) ────────────────────────────────────────────

def test_co_accused_with_props_and_weight(projected):
    pair = [e for e in _edges(projected, "CO_ACCUSED_WITH")
            if {e.src_id, e.dst_id} == {"P-A1", "P-A2"}]
    assert len(pair) == 1
    e = pair[0]
    assert e.weight == 2.0                                   # two shared cases → Q5 rank
    assert set(e.props) == {"cases", "first", "last", "districts"}
    assert e.props["cases"] == 2 and e.props["districts"] == [1]
    assert e.props["first"] == OLD.isoformat() and e.props["last"] == OLD.isoformat()


def test_shares_signature_threshold_and_different_units(projected):
    sig = _edges(projected, "SHARES_SIGNATURE")
    assert any({e.src_id, e.dst_id} == {"4000", "4001"} for e in sig)   # seed g4 pair
    for e in sig:
        assert e.props["jaccard"] >= 0.6                     # §14.3 threshold
    # different units required: no same-unit signature pair exists
    cases = {c.CaseMasterID: c for c in projected.query(m.CaseMaster).all()}
    for e in sig:
        assert cases[int(e.src_id)].PoliceStationID != cases[int(e.dst_id)].PoliceStationID


def test_proximate_to_thresholds(projected):
    prox = _edges(projected, "PROXIMATE_TO")
    assert any({e.src_id, e.dst_id} == {"90006", "90007"} for e in prox)
    for e in prox:
        assert e.props["km"] <= 5.0 and e.props["days"] <= 14


def test_operates_in_union_of_case_and_arrest_districts(projected):
    ops = {(e.src_id, e.dst_id): e.props for e in _edges(projected, "OPERATES_IN")}
    assert ("P-X", "district:1") in ops and ("P-X", "district:2") in ops
    assert ops[("P-A1", "district:1")]["cases"] >= 2
    assert ops[("P-A1", "district:1")]["arrests"] == 1


def test_same_io_as_shared_ioid(projected):
    same = _edges(projected, "SAME_IO_AS")
    assert any({e.src_id, e.dst_id} == {"P-A1", "P-B1"} for e in same)


# ── metrics (§14.5) + §3.6 persistence rules ───────────────────────────────

def test_metrics_computed_and_persisted_for_resolved_persons(projected):
    rows = {r.person_id: r for r in projected.query(LumenPersonMetrics).all()}
    assert "P-A1" in rows and "P-X" in rows
    # FK rule: only lumen_person rows persist metrics — no singleton ids
    assert not any(pid.startswith("accused:") for pid in rows)
    a1 = rows["P-A1"]
    assert a1.degree >= 3                        # A2, A3, X at minimum
    assert a1.community_id is not None
    assert a1.district_span >= 1
    assert rows["P-X"].district_span == 2        # operates in districts 1 and 2
    # broker: X has the highest betweenness of the resolved persons
    assert rows["P-X"].betweenness == max(r.betweenness for r in rows.values())


def test_communities_persisted_with_broker_and_districts(projected):
    comms = projected.query(LumenCommunity).all()
    assert comms
    for c in comms:
        assert c.size >= 2 and c.computed_at is not None
    # the bridged network yields a community whose broker is P-X or that spans 2 districts
    assert any(c.broker_person_id == "P-X" or (c.district_ids and len(c.district_ids) >= 2)
               for c in comms)


def test_projection_registers_method_version(projected):
    row = projected.query(LumenModelRegistry).filter_by(name="graph_projection").one()
    assert row.version == "v1" and row.active


# ── update correctness / idempotence ───────────────────────────────────────

def test_projection_rerun_is_idempotent(projected):
    before = projected.query(LumenGraphEdge).count()
    run_projection(projected, now=NOW)
    assert projected.query(LumenGraphEdge).count() == before


def test_projection_reflects_new_data_on_rerun(projected):
    # a new shared case for A2+A3 increments their co-accusal weight 1 → 2
    _case(projected, 90009, 11, RECENT)
    _member(projected, 90022, 90009, "P-A2", "Alpha Two")
    _member(projected, 90023, 90009, "P-A3", "Alpha Three")
    projected.flush()
    run_projection(projected, now=NOW)
    pair = [e for e in _edges(projected, "CO_ACCUSED_WITH")
            if {e.src_id, e.dst_id} == {"P-A2", "P-A3"}]
    assert pair[0].weight == 2.0 and pair[0].props["cases"] == 2


# ── metrics unit behaviour ─────────────────────────────────────────────────

def test_compute_metrics_star_graph():
    import networkx as nx
    g = nx.Graph()
    for leaf in ("b", "c", "d"):
        g.add_edge("a", leaf, weight=1.0)
    per = gm.compute_metrics(g)
    assert per["a"]["degree"] == 3
    assert per["a"]["betweenness"] == max(v["betweenness"] for v in per.values())
    assert all(v["community_id"] is not None for v in per.values())
    assert gm.compute_metrics(nx.Graph()) == {}
