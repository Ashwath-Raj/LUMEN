"""
Graph backend — LUMEN_MASTER_SPEC_V3 §14.1, ADR-001.

§14.1: "primary runtime is NetworkX in-process, projections persisted to Data
Store (`lumen_graph_edge`) ... Neo4j is optional and additive behind
`graph/backend.py`. The API must not know which backend answered."

This module is that seam: callers ask for a graph, and the answer is built by
the active backend. The NetworkX backend implemented here loads PRECOMPUTED
edges from `lumen_graph_edge` (written by `projection.py`) — it never touches
canonical tables, so nothing here re-projects per request (§14.5: "Nothing
here runs per request"). A Neo4j backend can be added behind the same two
functions without any caller changing (ADR-001: "Backend is swappable");
`legacy_neo4j_service.py` in this package remains reference material only and
is not wired here.
"""
from __future__ import annotations

import networkx as nx
from sqlalchemy.orm import Session

from lumen.db.models.graph import LumenGraphEdge


def load_edges(session: Session, *, rels: list[str] | None = None) -> list[LumenGraphEdge]:
    """All precomputed edges, optionally filtered to specific rel types."""
    q = session.query(LumenGraphEdge)
    if rels is not None:
        q = q.filter(LumenGraphEdge.rel.in_(rels))
    return q.all()


def person_graph(session: Session, *, rels: list[str] | None = None) -> nx.Graph:
    """The undirected person↔person graph from precomputed person-to-person
    edges (CO_ACCUSED_WITH, SAME_IO_AS by default). Node = semantic person id;
    edge attributes = rel, weight, props."""
    rels = rels or ["CO_ACCUSED_WITH", "SAME_IO_AS"]
    g = nx.Graph()
    for e in load_edges(session, rels=rels):
        if e.src_type == "person" and e.dst_type == "person":
            g.add_edge(e.src_id, e.dst_id, rel=e.rel, weight=e.weight or 1.0,
                       props=e.props or {})
    return g


def case_graph(session: Session, rel: str) -> nx.Graph:
    """The undirected case↔case graph for one derived rel
    (SHARES_SIGNATURE or PROXIMATE_TO)."""
    g = nx.Graph()
    for e in load_edges(session, rels=[rel]):
        if e.src_type == "case" and e.dst_type == "case":
            g.add_edge(e.src_id, e.dst_id, rel=e.rel, weight=e.weight or 1.0,
                       props=e.props or {})
    return g


def person_case_graph(session: Session) -> nx.Graph:
    """The undirected bipartite person↔case graph over ACCUSED_IN edges —
    the substrate for Q7's 'neighbourhood expansion via Person'."""
    g = nx.Graph()
    for e in load_edges(session, rels=["ACCUSED_IN"]):
        g.add_edge(("person", e.src_id), ("case", e.dst_id),
                   rel=e.rel, weight=e.weight or 1.0)
    return g
