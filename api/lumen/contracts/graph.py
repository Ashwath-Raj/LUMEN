"""
GraphContract v1 — LUMEN_MASTER_SPEC_V3 §7, §14.4.

§7's contract table lists `GraphContract` (v1, produced by the graph module,
consumed by API/UI/AI) but — as with `EntityContract` (see contracts/entity.py)
— gives no field-level shape anywhere. What §14.4 does fix is the shape of a
query result: "Every result returns `Insight` **plus** graph payload, never a
bare graph, and every result carries its limitations line."

`GraphContract` below is therefore the same minimal versioned envelope the
`EntityContract` precedent established: `contract_version` (§7 rule 2) around
the graph payload — nodes and edges as plain dicts mirroring the semantic
node/edge vocabulary of §14.2/§14.3 and the §3.6 `lumen_graph_edge` columns.
Nothing further is invented.

`GraphQueryResult` is the §14.4 result shape: the §8 Insight plus the graph
payload, together.
"""
from __future__ import annotations

from pydantic import BaseModel

from lumen.contracts.insight import Insight


class GraphContract(BaseModel):
    """Versioned graph payload (§7 GraphContract v1). `nodes` entries carry
    the semantic node type and id (§14.2); `edges` entries mirror the
    §3.6 lumen_graph_edge columns (src/dst/rel/weight/props)."""

    contract_version: str = "v1"
    nodes: list[dict]
    edges: list[dict]


class GraphQueryResult(BaseModel):
    """§14.4: 'Every result returns Insight plus graph payload, never a bare
    graph.' The insight's `limitations` carries the required limitations
    line (§8 invariant 2 makes it unomittable)."""

    insight: Insight
    graph: GraphContract
