"""
Session 9 — the ten §14.4 named queries and the §33 completion criterion:
"All ten answer in <400 ms from precomputed tables."

Each query is exercised against the projected graph (seed + resolved synthetic
network — see test_graph.py's fixture design):
  * correctness of the answer,
  * §14.4's result shape — Insight PLUS graph payload, never a bare graph,
  * the limitations line on every result,
  * the <400 ms criterion, measured per query over the precomputed tables,
  * serialization, and integration with the Session 8 verified gate.

Self-contained: in-memory SQLite, no live PostgreSQL.
"""
import time
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.contracts.graph import GraphQueryResult
from lumen.db.models import canonical as m
from lumen.graph import queries as Q
from lumen.graph.projection import run_projection
from lumen.jobs.resolve import run_resolution
from lumen.jobs.seed import seed_database

from tests.test_graph import NOW, synthetic_network


def _fresh_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


@pytest.fixture(scope="module")
def s():
    session = _fresh_session()
    seed_database(session)
    run_resolution(session)
    synthetic_network(session)
    run_projection(session, now=NOW)
    return session


def _check_shape(result: GraphQueryResult):
    """§14.4: Insight plus graph payload, never a bare graph; limitations
    line always present (§8 invariant 2 backs it)."""
    assert result.insight is not None and result.graph is not None
    assert result.graph.contract_version == "v1"
    assert result.insight.limitations
    assert result.insight.kind == "network"
    assert round(result.insight.confidence, 3) == round(
        result.insight.confidence_breakdown.composite, 3)


# ── Q1 shortest connection ─────────────────────────────────────────────────

def test_q1_shortest_connection(s):
    r = Q.q1_shortest_connection(s, "P-A3", "P-B3", now=NOW)
    _check_shape(r)
    assert "connected" in r.insight.headline
    path_nodes = {n["id"] for n in r.graph.nodes}
    # BFS legitimately shortcuts through the SAME_IO_AS edge A1↔B1 — and the
    # workload-artefact caveat must then accompany the co-accusal line
    assert {"P-A3", "P-A1", "P-B1", "P-B3"} <= path_nodes
    assert Q.CO_ACCUSAL_LIMITATION in r.insight.limitations
    if any(e["rel"] == "SAME_IO_AS" for e in r.graph.edges):
        assert Q.SAME_IO_LIMITATION in r.insight.limitations
    # no path case
    r2 = Q.q1_shortest_connection(s, "P-A3", "accused:11001", now=NOW)
    assert "No connection" in r2.insight.headline and r2.graph.edges == []


# ── Q2 hidden intermediary ─────────────────────────────────────────────────

def test_q2_hidden_intermediary(s):
    r = Q.q2_hidden_intermediary(s, ["P-A2", "P-A3"], ["P-B2", "P-B3"], now=NOW)
    _check_shape(r)
    assert "P-X" in r.insight.headline           # the only bridge between clusters
    assert any(e.id == "P-X" for e in r.insight.evidence)


# ── Q3 communities ─────────────────────────────────────────────────────────

def test_q3_communities(s):
    r = Q.q3_communities(s, now=NOW)
    _check_shape(r)
    assert "communities" in r.insight.headline
    assert r.graph.nodes                          # from precomputed lumen_community
    assert all(n["type"] == "community" for n in r.graph.nodes)


# ── Q4 most influential in district ────────────────────────────────────────

def test_q4_most_influential(s):
    r = Q.q4_most_influential(s, 1, now=NOW)
    _check_shape(r)
    assert "district 1" in r.insight.headline
    assert r.insight.subject_type == "district" and r.insight.subject_id == "1"
    assert r.insight.evidence                     # a top person named


# ── Q5 repeat co-offender pairs ────────────────────────────────────────────

def test_q5_repeat_pairs(s):
    r = Q.q5_repeat_pairs(s, now=NOW)
    _check_shape(r)
    pairs = {frozenset((e["src_id"], e["dst_id"])) for e in r.graph.edges}
    assert frozenset(("P-A1", "P-A2")) in pairs   # weight-2 pair
    assert all(e["weight"] >= 2 for e in r.graph.edges)


# ── Q6 cross-district networks ─────────────────────────────────────────────

def test_q6_cross_district(s):
    r = Q.q6_cross_district(s, now=NOW)
    _check_shape(r)
    assert r.graph.nodes                          # the bridged community spans 1 and 2
    assert all(len(n["district_ids"]) >= 2 for n in r.graph.nodes)


# ── Q7 2-hop linked cases ──────────────────────────────────────────────────

def test_q7_two_hop_cases(s):
    r = Q.q7_two_hop_cases(s, 90001, now=NOW)
    _check_shape(r)
    linked = {n["id"] for n in r.graph.nodes if n["type"] == "case"} - {"90001"}
    assert {"90002", "90004"} <= linked           # via P-A1 / P-A2
    r2 = Q.q7_two_hop_cases(s, 4000, now=NOW)     # signature pair is not person-linked
    assert "no 2-hop" in r2.insight.headline


# ── Q8 signature families ──────────────────────────────────────────────────

def test_q8_signature_families(s):
    r = Q.q8_signature_families(s, now=NOW)
    _check_shape(r)
    family_cases = {n["id"] for n in r.graph.nodes}
    assert {"4000", "4001"} <= family_cases       # seed g4 shared signature
    assert Q.SIGNATURE_LIMITATION in r.insight.limitations


# ── Q9 emerging cluster ────────────────────────────────────────────────────

def test_q9_emerging_clusters(s):
    r = Q.q9_emerging_clusters(s, as_of=datetime(2026, 7, 15), now=NOW)
    _check_shape(r)
    # the broker's July bridges are new edges against January baselines
    assert "growth" in r.insight.headline
    members = {p for n in r.graph.nodes for p in n.get("members", [])}
    assert "P-X" in members


# ── Q10 spree chain ────────────────────────────────────────────────────────

def test_q10_spree_chain(s):
    r = Q.q10_spree_chain(s, 90007, now=NOW)
    _check_shape(r)
    chain = [n["id"] for n in r.graph.nodes]
    assert chain == ["90006", "90007", "90008"]   # ordered by date
    assert Q.SPREE_LIMITATION in r.insight.limitations
    r2 = Q.q10_spree_chain(s, 4000, now=NOW)
    assert "not part of a proximate series" in r2.insight.headline


# ── §33 completion criterion: all ten < 400 ms from precomputed tables ─────

def test_all_ten_queries_under_400ms(s):
    calls = {
        "q1": lambda: Q.q1_shortest_connection(s, "P-A3", "P-B3", now=NOW),
        "q2": lambda: Q.q2_hidden_intermediary(s, ["P-A2"], ["P-B2"], now=NOW),
        "q3": lambda: Q.q3_communities(s, now=NOW),
        "q4": lambda: Q.q4_most_influential(s, 1, now=NOW),
        "q5": lambda: Q.q5_repeat_pairs(s, now=NOW),
        "q6": lambda: Q.q6_cross_district(s, now=NOW),
        "q7": lambda: Q.q7_two_hop_cases(s, 90001, now=NOW),
        "q8": lambda: Q.q8_signature_families(s, now=NOW),
        "q9": lambda: Q.q9_emerging_clusters(s, as_of=datetime(2026, 7, 15), now=NOW),
        "q10": lambda: Q.q10_spree_chain(s, 90007, now=NOW),
    }
    assert set(calls) == set(Q.ALL_QUERIES)       # all ten, no more, no fewer
    timings = {}
    for name, fn in calls.items():
        t0 = time.perf_counter()
        result = fn()
        timings[name] = (time.perf_counter() - t0) * 1000
        assert isinstance(result, GraphQueryResult)
    slow = {k: v for k, v in timings.items() if v >= 400}
    assert not slow, f"queries over the 400 ms budget: {slow}"


# ── serialization + Session 8 integration ──────────────────────────────────

def test_result_serialization_round_trip(s):
    r = Q.q1_shortest_connection(s, "P-A3", "P-B3", now=NOW)
    again = GraphQueryResult.model_validate_json(r.model_dump_json())
    assert again == r


def test_query_insight_passes_verified_gate(s):
    """A populated result's Insight satisfies the Session 8 invariants: its
    evidence resolves, its model_version is registered by the projection, its
    classification covers its evidence, and it clears the confidence floor."""
    from lumen.intelligence.lifecycle import save_insight, to_verified

    r = Q.q1_shortest_connection(s, "P-A3", "P-B3", now=NOW)
    save_insight(s, r.insight)
    verified = to_verified(s, r.insight)
    assert verified.lifecycle_state == "verified"


def test_queries_read_only_precomputed_tables(s):
    """§14.5 'nothing here runs per request': the person-graph queries answer
    identically after canonical accused rows change, until re-projection."""
    s.add(m.Accused(AccusedMasterID=95000, CaseMasterID=90003, AccusedName="Late Add",
                    AgeYear=30, GenderID=1, PersonID="A9"))
    s.flush()
    r = Q.q5_repeat_pairs(s, now=NOW)
    pairs = {frozenset((e["src_id"], e["dst_id"])) for e in r.graph.edges}
    assert frozenset(("P-A1", "P-A2")) in pairs   # unchanged — read from lumen_graph_edge
    s.query(m.Accused).filter(m.Accused.AccusedMasterID == 95000).delete()
    s.flush()
