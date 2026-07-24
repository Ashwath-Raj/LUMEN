# ADR-001 — Graph analytics in-process (NetworkX)

**Status:** Accepted (architecture frozen at v3, §37).

## Context

The knowledge graph (§14) is a Tier-1 subsystem: entity resolution turns
per-case `Accused` rows into cross-case `Person` nodes, and the value of the
platform is the derived association network over them. LUMEN must be deployed
Catalyst-native (P6), and **Catalyst has no graph database service** (§14.1,
§26.3). An external graph DB is not a forbidden substitution under P6, but it
introduces an external dependency in a competition where Catalyst-native
deployment is mandatory and judged, and the ten named graph queries (§14.4)
must answer in under 400 ms from precomputed tables (§14.5, §33 done-when for
the graph session).

## Decision

Primary runtime is **NetworkX in-process**, with projections persisted to Data
Store (`lumen_graph_edge`), adjacency snapshots in Catalyst NoSQL, and hot
ego-graphs in Catalyst Cache. Neo4j is optional and additive behind
`graph/backend.py`. **The API must not know which backend answered.**

## Alternatives Considered

- **Neo4j Aura** — external graph DB.
- **ArangoDB** — external multi-model DB.

## Consequences

- The graph runs with no external graph-service dependency, removing an
  availability risk in a Catalyst-mandated deployment and keeping queries under
  the latency budget (§14.5: "Any request path exceeding 400 ms reads a
  precomputed table instead").
- The backend is swappable: `graph/backend.py` is the seam, and a Neo4j
  adapter can slot in without any caller changing.
- NetworkX is registered as a P6 exception (§26.3): "No graph service exists in
  Catalyst."
- Graph metrics (degree, betweenness, eigenvector, Louvain) are computed by the
  projection pipeline and persisted; nothing is recomputed per request.

## Specification references

§14 (knowledge graph), §14.1 (runtime decision), §14.5 (projection pipeline),
§26.3 (P6 exception register), §35 ADR-001, P6.
