"""
The ten named graph queries — LUMEN_MASTER_SPEC_V3 §14.4.

| #   | Query                        | Algorithm                                 |
|-----|------------------------------|-------------------------------------------|
| Q1  | Shortest connection          | BFS/Dijkstra                               |
| Q2  | Hidden intermediary          | Betweenness on connecting subgraph         |
| Q3  | Communities                  | Louvain                                    |
| Q4  | Most influential in district | Eigenvector, district-filtered             |
| Q5  | Repeat co-offender pairs     | Edge-weight rank                           |
| Q6  | Cross-district networks      | Communities spanning ≥2 districts          |
| Q7  | 2-hop linked cases           | Neighbourhood expansion via `Person`       |
| Q8  | Signature families           | Components over `SHARES_SIGNATURE`         |
| Q9  | Emerging cluster             | Communities with ≥50% edge growth in 30d   |
| Q10 | Spree chain                  | Path over `PROXIMATE_TO` ordered by date   |

§14.4: "Every result returns `Insight` **plus** graph payload, never a bare
graph, and every result carries its limitations line."

Everything reads the PRECOMPUTED tables (`lumen_graph_edge`,
`lumen_person_metrics`, `lumen_community`) written by `projection.py` —
nothing re-projects from canonical data per request (§14.5). Query-time
algorithms (BFS, betweenness-on-subgraph, district-filtered eigenvector,
seeded Louvain for membership) run over the precomputed edge set, exactly as
§14.4's Algorithm column prescribes; that is how "all ten answer in <400 ms
from precomputed tables" (§33) is met.

Disclosed implementation notes (details §14 does not fix):
  * All ten insights use `kind="network"` — §8's vocabulary offers no
    per-query kind mapping.
  * `score` is None — §14 assigns no scalar score to query results.
  * Limitations lines: association-network results carry §11's mandated
    "Co-accusal reflects charging decisions, not adjudicated guilt."; results
    whose payload includes SAME_IO_AS edges add §14.3's workload-artefact
    caveat; Q8/Q10 carry honest method caveats authored here because the
    spec mandates a line but supplies no wording for those two.
  * `classification` is the highest §4.2 classification of the evidence
    (§4.3 rule 2); INTERNAL when a result has no evidence rows.
  * §3.6's `lumen_community` persists no member list; membership comes from
    `lumen_person_metrics.community_id` (resolved persons) or the seeded,
    deterministic Louvain over the precomputed edges where full membership
    is needed (Q9).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import networkx as nx
from sqlalchemy.orm import Session

from lumen.contracts.graph import GraphContract, GraphQueryResult
from lumen.contracts.insight import Evidence, Factor, Insight, Lineage
from lumen.db.models import canonical as m
from lumen.db.models.graph import LumenCommunity, LumenGraphEdge, LumenPersonMetrics
from lumen.db.models.identity import LumenPerson
from lumen.governance.classification import CLASSIFICATION_ORDER
from lumen.graph import backend
from lumen.graph.metrics import association_graph, compute_metrics
from lumen.intelligence import confidence as C
from lumen.intelligence.explain import classification_of_evidence
from lumen.graph.projection import METHOD_NAME, METHOD_VERSION

_NS = uuid.UUID("9a7c1f00-0000-4000-8000-00000000014a")

# §11 trust statement for network results.
CO_ACCUSAL_LIMITATION = "Co-accusal reflects charging decisions, not adjudicated guilt."
SAME_IO_LIMITATION = "A shared investigating officer is a workload artefact, not an indicator of guilt."
SIGNATURE_LIMITATION = "A shared act-section signature reflects similar charges filed, not proven common authorship."
SPREE_LIMITATION = "Spatio-temporal proximity suggests, but does not establish, a connected series."


# ── shared assembly ────────────────────────────────────────────────────────

def _person_chip(session: Session, node: str) -> Evidence:
    if node.startswith("accused:"):
        return Evidence(entity="participant", id=node, label=node, url=f"/persons/{node}")
    person = session.get(LumenPerson, node)
    label = person.canonical_name if person is not None else node
    return Evidence(entity="person", id=node, label=label, url=f"/persons/{node}")


def _case_chip(cid: str) -> Evidence:
    return Evidence(entity="case", id=str(cid), label=f"Case {cid}", url=f"/cases/{cid}")


def _edge_dicts(g: nx.Graph, *, node_type: str) -> list[dict]:
    return [
        {"src_type": node_type, "src_id": a, "dst_type": node_type, "dst_id": b,
         "rel": d.get("rel", ""), "weight": d.get("weight", 1.0), "props": d.get("props", {})}
        for a, b, d in g.edges(data=True)
    ]


def _result(session: Session, *, qid: str, headline: str, subject_type: str,
            subject_id: str, nodes: list[dict], edges: list[dict],
            evidence: list[Evidence], limitations: list[str],
            factors: list[Factor] | None = None,
            supporting_edges: int | None = None,
            now: datetime | None = None) -> GraphQueryResult:
    """§14.4 result shape: Insight plus graph payload, never a bare graph.
    `supporting_edges` feeds §9's graph_confidence; it defaults to the payload
    edge count, and community queries pass the count of association edges the
    finding rests on when the payload itself is node-only."""
    now = now or datetime.now(timezone.utc)
    scope = ("district", subject_id) if subject_type == "district" else ("state", "karnataka")
    breakdown = C.compose(
        data_completeness=C.data_completeness(session, *scope),
        identity_confidence=C.identity_confidence(session, evidence),
        graph_confidence=C.graph_confidence(
            supporting_edges if supporting_edges is not None else len(edges)
        ),
    )
    classification = "INTERNAL"
    if evidence:
        classification = max((classification_of_evidence(e) for e in evidence),
                             key=lambda c: CLASSIFICATION_ORDER[c])
    insight = Insight(
        id=str(uuid.uuid5(_NS, f"{qid}:{subject_type}:{subject_id}:{headline}")),
        kind="network",
        subject_type=subject_type,
        subject_id=subject_id,
        headline=headline,
        score=None,
        confidence=breakdown.composite,
        confidence_breakdown=breakdown,
        factors=factors or [],
        counterfactuals=[],
        evidence=evidence,
        limitations=limitations,
        lineage=Lineage(
            method=METHOD_NAME, model_version=METHOD_VERSION, prompt_version=None,
            features_used=[], query_ids=[qid],
            source_row_count=session.query(LumenGraphEdge).count(),
            quality_score=C.data_completeness(session, *scope),
            computed_at=now,
        ),
        lifecycle_state="generated",
        classification=classification,
        generated_at=now,
    )
    return GraphQueryResult(insight=insight,
                            graph=GraphContract(nodes=nodes, edges=edges))


def _person_payload(g: nx.Graph, members: list[str]) -> tuple[list[dict], list[dict]]:
    sub = g.subgraph(members)
    nodes = [{"type": "person", "id": n} for n in sorted(sub.nodes)]
    return nodes, _edge_dicts(sub, node_type="person")


def _limitations_for(edges: list[dict]) -> list[str]:
    lims = [CO_ACCUSAL_LIMITATION]
    if any(e["rel"] == "SAME_IO_AS" for e in edges):
        lims.append(SAME_IO_LIMITATION)
    return lims


# ── Q1 Shortest connection — BFS/Dijkstra ──────────────────────────────────

def q1_shortest_connection(session: Session, person_a: str, person_b: str,
                           *, now: datetime | None = None) -> GraphQueryResult:
    g = backend.person_graph(session)
    if person_a in g and person_b in g and nx.has_path(g, person_a, person_b):
        path = nx.shortest_path(g, person_a, person_b)      # BFS (unweighted)
        headline = f"{person_a} and {person_b} are connected through {len(path) - 1} link(s)."
        nodes, edges = _person_payload(g, path)
    else:
        path, nodes, edges = [], [], []
        headline = f"No connection found between {person_a} and {person_b}."
    evidence = [_person_chip(session, p) for p in path]
    return _result(session, qid="q1", headline=headline, subject_type="person",
                   subject_id=person_a, nodes=nodes, edges=edges,
                   evidence=evidence, limitations=_limitations_for(edges), now=now)


# ── Q2 Hidden intermediary — betweenness on connecting subgraph ────────────

def q2_hidden_intermediary(session: Session, group_a: list[str], group_b: list[str],
                           *, now: datetime | None = None) -> GraphQueryResult:
    # Betweenness is a centrality computation — run on the association
    # network (CO_ACCUSED_WITH) only. SAME_IO_AS is §14.3-caveated as a
    # workload artefact and, like §6.4's candidate links, stays out of
    # centrality; it still participates in Q1 connection-finding.
    g = association_graph(session)
    connecting: set[str] = set()
    for a in group_a:
        for b in group_b:
            if a in g and b in g and nx.has_path(g, a, b):
                connecting.update(nx.shortest_path(g, a, b))
    intermediary = None
    if connecting:
        sub = g.subgraph(connecting)
        centrality = nx.betweenness_centrality(sub)
        outsiders = [n for n in sub.nodes if n not in set(group_a) | set(group_b)]
        if outsiders:
            intermediary = max(outsiders, key=lambda n: centrality[n])
    if intermediary is not None:
        headline = f"{intermediary} is the link between the two groups."
        nodes, edges = _person_payload(g, sorted(connecting))
        evidence = [_person_chip(session, intermediary)]
    else:
        headline = "No intermediary connects the two groups."
        nodes, edges, evidence = [], [], []
    return _result(session, qid="q2", headline=headline, subject_type="state",
                   subject_id="karnataka", nodes=nodes, edges=edges,
                   evidence=evidence, limitations=_limitations_for(edges), now=now)


# ── Q3 Communities — Louvain (precomputed) ─────────────────────────────────

def q3_communities(session: Session, *, now: datetime | None = None) -> GraphQueryResult:
    communities = session.query(LumenCommunity).order_by(LumenCommunity.community_id).all()
    members_by_c: dict[int, list[str]] = {}
    for row in session.query(LumenPersonMetrics).all():
        if row.community_id is not None:
            members_by_c.setdefault(row.community_id, []).append(row.person_id)
    nodes = [{"type": "community", "id": str(c.community_id), "size": c.size,
              "district_ids": c.district_ids, "broker_person_id": c.broker_person_id}
             for c in communities]
    evidence = [_person_chip(session, c.broker_person_id)
                for c in communities if c.broker_person_id]
    headline = (f"{len(communities)} co-offending communities operate as units."
                if communities else "No co-offending communities found.")
    support = (session.query(LumenGraphEdge)
               .filter(LumenGraphEdge.rel == "CO_ACCUSED_WITH").count()
               if communities else 0)
    return _result(session, qid="q3", headline=headline, subject_type="state",
                   subject_id="karnataka", nodes=nodes, edges=[],
                   evidence=evidence, limitations=[CO_ACCUSAL_LIMITATION],
                   supporting_edges=support, now=now)


# ── Q4 Most influential in district — eigenvector, district-filtered ──────

def q4_most_influential(session: Session, district_id: int,
                        *, now: datetime | None = None) -> GraphQueryResult:
    in_district = {
        e.src_id for e in session.query(LumenGraphEdge).filter(
            LumenGraphEdge.rel == "OPERATES_IN",
            LumenGraphEdge.dst_id == f"district:{district_id}",
        )
    }
    g = association_graph(session).subgraph(in_district)
    top = None
    if g.number_of_nodes() > 0 and g.number_of_edges() > 0:
        try:
            centrality = nx.eigenvector_centrality(g, max_iter=1000)
        except nx.PowerIterationFailedConvergence:
            centrality = {n: 0.0 for n in g.nodes}
        top = max(centrality, key=lambda n: centrality[n])
    if top is not None:
        headline = f"{top} is the most influential person in district {district_id}."
        nodes, edges = _person_payload(g, list(g.nodes))
        evidence = [_person_chip(session, top)]
    else:
        headline = f"No association network found in district {district_id}."
        nodes, edges, evidence = [], [], []
    return _result(session, qid="q4", headline=headline, subject_type="district",
                   subject_id=str(district_id), nodes=nodes, edges=edges,
                   evidence=evidence, limitations=[CO_ACCUSAL_LIMITATION], now=now)


# ── Q5 Repeat co-offender pairs — edge-weight rank ─────────────────────────

def q5_repeat_pairs(session: Session, *, top_n: int = 10,
                    now: datetime | None = None) -> GraphQueryResult:
    pairs = (
        session.query(LumenGraphEdge)
        .filter(LumenGraphEdge.rel == "CO_ACCUSED_WITH", LumenGraphEdge.weight >= 2)
        .order_by(LumenGraphEdge.weight.desc(), LumenGraphEdge.src_id)
        .limit(top_n)
        .all()
    )
    edges = [{"src_type": "person", "src_id": e.src_id, "dst_type": "person",
              "dst_id": e.dst_id, "rel": e.rel, "weight": e.weight, "props": e.props}
             for e in pairs]
    nodes = [{"type": "person", "id": n}
             for n in sorted({e.src_id for e in pairs} | {e.dst_id for e in pairs})]
    evidence = [c for e in pairs for c in
                (_person_chip(session, e.src_id), _person_chip(session, e.dst_id))]
    headline = (f"{len(pairs)} pairs have co-offended in two or more cases."
                if pairs else "No repeat co-offender pairs found.")
    return _result(session, qid="q5", headline=headline, subject_type="state",
                   subject_id="karnataka", nodes=nodes, edges=edges,
                   evidence=evidence, limitations=[CO_ACCUSAL_LIMITATION], now=now)


# ── Q6 Cross-district networks — communities spanning ≥2 districts ─────────

def q6_cross_district(session: Session, *, now: datetime | None = None) -> GraphQueryResult:
    spanning = [c for c in session.query(LumenCommunity).order_by(LumenCommunity.community_id)
                if c.district_ids and len(c.district_ids) >= 2]
    nodes = [{"type": "community", "id": str(c.community_id), "size": c.size,
              "district_ids": c.district_ids, "broker_person_id": c.broker_person_id}
             for c in spanning]
    evidence = [_person_chip(session, c.broker_person_id) for c in spanning if c.broker_person_id]
    headline = (f"{len(spanning)} communities span two or more districts."
                if spanning else "No cross-district communities found.")
    support = (session.query(LumenGraphEdge)
               .filter(LumenGraphEdge.rel == "CO_ACCUSED_WITH").count()
               if spanning else 0)
    return _result(session, qid="q6", headline=headline, subject_type="state",
                   subject_id="karnataka", nodes=nodes, edges=[],
                   evidence=evidence, limitations=[CO_ACCUSAL_LIMITATION],
                   supporting_edges=support, now=now)


# ── Q7 2-hop linked cases — neighbourhood expansion via Person ─────────────

def q7_two_hop_cases(session: Session, case_id: int,
                     *, now: datetime | None = None) -> GraphQueryResult:
    g = backend.person_case_graph(session)
    start = ("case", str(case_id))
    linked: list[str] = []
    via: list[tuple] = []
    if start in g:
        for person in g.neighbors(start):                    # hop 1: case → person
            for other in g.neighbors(person):                # hop 2: person → case
                if other != start:
                    linked.append(other[1])
                    via.append((person[1], other[1]))
    linked = sorted(set(linked))
    nodes = ([{"type": "case", "id": str(case_id)}]
             + [{"type": "case", "id": c} for c in linked]
             + [{"type": "person", "id": p} for p in sorted({p for p, _ in via})])
    edges = [{"src_type": "person", "src_id": p, "dst_type": "case", "dst_id": c,
              "rel": "ACCUSED_IN", "weight": 1.0, "props": {}} for p, c in via]
    evidence = [_case_chip(case_id)] + [_case_chip(c) for c in linked]
    headline = (f"Case {case_id} is linked to {len(linked)} other case(s) within two hops."
                if linked else f"Case {case_id} has no 2-hop linked cases.")
    return _result(session, qid="q7", headline=headline, subject_type="case",
                   subject_id=str(case_id), nodes=nodes, edges=edges,
                   evidence=evidence, limitations=[CO_ACCUSAL_LIMITATION], now=now)


# ── Q8 Signature families — components over SHARES_SIGNATURE ──────────────

def q8_signature_families(session: Session, *, now: datetime | None = None) -> GraphQueryResult:
    g = backend.case_graph(session, "SHARES_SIGNATURE")
    families = [sorted(c) for c in nx.connected_components(g)]
    families.sort(key=lambda f: f[0])
    nodes = [{"type": "case", "id": c} for fam in families for c in fam]
    edges = _edge_dicts(g, node_type="case")
    evidence = [_case_chip(c) for fam in families for c in fam]
    headline = (f"{len(families)} case families share an act-section signature."
                if families else "No signature families found.")
    return _result(session, qid="q8", headline=headline, subject_type="state",
                   subject_id="karnataka", nodes=nodes, edges=edges,
                   evidence=evidence, limitations=[SIGNATURE_LIMITATION], now=now)


# ── Q9 Emerging cluster — ≥50% edge growth in 30 days ─────────────────────

def q9_emerging_clusters(session: Session, *, as_of: datetime | None = None,
                         now: datetime | None = None) -> GraphQueryResult:
    g = association_graph(session)
    per_node = compute_metrics(g)          # seeded Louvain over precomputed edges
    members_by_c: dict[int, set[str]] = {}
    for node, vals in per_node.items():
        if vals["community_id"] is not None:
            members_by_c.setdefault(vals["community_id"], set()).add(node)

    all_dates = [d.get("props", {}).get("first") for _, _, d in g.edges(data=True)]
    all_dates = [d for d in all_dates if d]
    if as_of is None and all_dates:
        as_of = datetime.fromisoformat(max(all_dates))
    emerging: list[int] = []
    if as_of is not None:
        window_start = (as_of - timedelta(days=30)).date().isoformat()
        for cid, members in members_by_c.items():
            sub = g.subgraph(members)
            new = old = 0
            for _, _, d in sub.edges(data=True):
                first = d.get("props", {}).get("first")
                if first is None:
                    continue
                if first >= window_start:
                    new += 1
                else:
                    old += 1
            if new > 0 and (old == 0 or new / old >= 0.5):    # ≥50% growth in 30d
                emerging.append(cid)
    nodes = [{"type": "community", "id": str(cid),
              "members": sorted(members_by_c[cid])} for cid in sorted(emerging)]
    edges: list[dict] = []
    for cid in sorted(emerging):
        edges.extend(_edge_dicts(g.subgraph(members_by_c[cid]), node_type="person"))
    evidence = [_person_chip(session, p) for cid in sorted(emerging)
                for p in sorted(members_by_c[cid])]
    headline = (f"{len(emerging)} cluster(s) show at least 50% edge growth in the last 30 days."
                if emerging else "No emerging clusters in the last 30 days.")
    return _result(session, qid="q9", headline=headline, subject_type="state",
                   subject_id="karnataka", nodes=nodes, edges=edges,
                   evidence=evidence, limitations=[CO_ACCUSAL_LIMITATION], now=now)


# ── Q10 Spree chain — path over PROXIMATE_TO ordered by date ───────────────

def q10_spree_chain(session: Session, case_id: int,
                    *, now: datetime | None = None) -> GraphQueryResult:
    g = backend.case_graph(session, "PROXIMATE_TO")
    start = str(case_id)
    chain: list[str] = []
    if start in g:
        component = nx.node_connected_component(g, start)
        dates = {
            str(c.CaseMasterID): c.CrimeRegisteredDate
            for c in session.query(m.CaseMaster)
            .filter(m.CaseMaster.CaseMasterID.in_([int(x) for x in component]))
        }
        chain = sorted(component, key=lambda c: (dates.get(c) is None, dates.get(c), int(c)))
    nodes = [{"type": "case", "id": c} for c in chain]
    edges = _edge_dicts(g.subgraph(chain), node_type="case") if chain else []
    evidence = [_case_chip(c) for c in chain]
    headline = (f"Case {case_id} sits in a proximate series of {len(chain)} cases."
                if len(chain) > 1 else f"Case {case_id} is not part of a proximate series.")
    return _result(session, qid="q10", headline=headline, subject_type="case",
                   subject_id=str(case_id), nodes=nodes, edges=edges,
                   evidence=evidence, limitations=[SPREE_LIMITATION], now=now)


ALL_QUERIES = {
    "q1": q1_shortest_connection, "q2": q2_hidden_intermediary,
    "q3": q3_communities, "q4": q4_most_influential, "q5": q5_repeat_pairs,
    "q6": q6_cross_district, "q7": q7_two_hop_cases,
    "q8": q8_signature_families, "q9": q9_emerging_clusters,
    "q10": q10_spree_chain,
}
