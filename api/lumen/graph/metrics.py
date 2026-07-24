"""
Graph metrics — LUMEN_MASTER_SPEC_V3 §14.5.

"→ metrics (degree, betweenness, eigenvector, Louvain)" over the projected
association network, persisted to `lumen_person_metrics` and
`lumen_community` (§3.6).

Scope decisions, disclosed:
  * Metrics run over the CO_ACCUSED_WITH graph — §14.3 names it "the
    association network"; SAME_IO_AS is excluded from centrality because §14.3
    caveats it as "a workload artefact, not guilt" (it still exists as an edge
    and participates in Q1 connection-finding).
  * §6.4: candidate matches are "excluded from centrality" — candidate pairs
    were never merged into nodes, so this holds by construction.
  * `lumen_person_metrics.person_id` is an FK to `lumen_person` (§3.6), so
    rows are persisted only for resolved persons; singleton "accused:<id>"
    identities carry their metrics in-memory (query payloads) but have no
    lumen_person row to reference.
  * Louvain runs with `seed=settings.SEED_RANDOM` so the partition is
    deterministic (§32's fixed-seed discipline). Communities of size ≥ 2 are
    persisted; community ids are assigned deterministically over the sorted
    member lists. The broker is the member with the highest betweenness
    (§32 guarantee 2's "exactly one high-betweenness broker").
"""
from __future__ import annotations

from datetime import datetime, timezone

import networkx as nx
from networkx.algorithms.community import louvain_communities
from sqlalchemy.orm import Session

from lumen.config import settings
from lumen.db.models.graph import LumenCommunity, LumenGraphEdge, LumenPersonMetrics
from lumen.db.models.identity import LumenPerson


def association_graph(session: Session) -> nx.Graph:
    """The CO_ACCUSED_WITH person graph from precomputed edges."""
    g = nx.Graph()
    for e in session.query(LumenGraphEdge).filter(LumenGraphEdge.rel == "CO_ACCUSED_WITH"):
        g.add_edge(e.src_id, e.dst_id, rel=e.rel, weight=e.weight or 1.0, props=e.props or {})
    return g


def compute_metrics(g: nx.Graph) -> dict[str, dict]:
    """degree / betweenness / eigenvector / Louvain community per node."""
    if g.number_of_nodes() == 0:
        return {}
    degree = dict(g.degree())
    betweenness = nx.betweenness_centrality(g)
    try:
        eigenvector = nx.eigenvector_centrality(g, max_iter=1000)
    except nx.PowerIterationFailedConvergence:      # pathological graphs only
        eigenvector = {n: 0.0 for n in g.nodes}
    communities = louvain_communities(g, seed=settings.SEED_RANDOM)
    community_of: dict[str, int] = {}
    # deterministic ids: communities ordered by their sorted member lists
    ordered = sorted((sorted(c) for c in communities), key=lambda ms: ms[0])
    for idx, members in enumerate(ordered, start=1):
        for node in members:
            community_of[node] = idx
    return {
        node: {
            "degree": degree.get(node, 0),
            "betweenness": betweenness.get(node, 0.0),
            "eigenvector": eigenvector.get(node, 0.0),
            "community_id": community_of.get(node),
        }
        for node in g.nodes
    }


def compute_and_persist(session: Session, *, now: datetime | None = None) -> dict:
    """Compute metrics over the association graph and persist
    lumen_person_metrics (resolved persons only — FK) and lumen_community
    (size ≥ 2, deterministic ids, broker = max betweenness)."""
    now = now or datetime.now(timezone.utc)
    g = association_graph(session)
    per_node = compute_metrics(g)

    # district span from OPERATES_IN edges
    district_span: dict[str, int] = {}
    for e in session.query(LumenGraphEdge).filter(LumenGraphEdge.rel == "OPERATES_IN"):
        district_span[e.src_id] = district_span.get(e.src_id, 0) + 1

    resolved_ids = {p.person_id for p in session.query(LumenPerson).all()}
    metrics_rows = 0
    for node, vals in per_node.items():
        if node not in resolved_ids:
            continue                       # §3.6 FK — resolved persons only
        session.add(LumenPersonMetrics(
            person_id=node, degree=vals["degree"], betweenness=vals["betweenness"],
            eigenvector=vals["eigenvector"], community_id=vals["community_id"],
            district_span=district_span.get(node, 0), computed_at=now,
        ))
        metrics_rows += 1

    # communities (size ≥ 2)
    by_community: dict[int, list[str]] = {}
    for node, vals in per_node.items():
        cid = vals["community_id"]
        if cid is not None:
            by_community.setdefault(cid, []).append(node)
    communities_rows = 0
    for cid, members in sorted(by_community.items()):
        if len(members) < 2:
            continue
        districts: set[int] = set()
        for e in session.query(LumenGraphEdge).filter(
            LumenGraphEdge.rel == "OPERATES_IN",
            LumenGraphEdge.src_id.in_(members),
        ):
            districts.add(int(e.dst_id.split(":", 1)[1]))
        broker = max(members, key=lambda p: per_node[p]["betweenness"])
        session.add(LumenCommunity(
            community_id=cid, size=len(members), district_ids=sorted(districts),
            broker_person_id=broker, computed_at=now,
        ))
        communities_rows += 1

    session.flush()
    return {"person_metrics": metrics_rows, "communities": communities_rows}
