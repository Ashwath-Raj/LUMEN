"""
Tool selection — LUMEN_MASTER_SPEC_V3 §16.2 step 4.

"Which graph queries, which features, which KB index." The MAPPING from
intent to tools is not defined by the specification ("Cannot determine") —
this deterministic table is the disclosed configuration. §16.6: tool
selection is exactly where specialisation lives at T1 ("specialisation is
expressed as tool selection today").

Tool names reference what Sessions 1–13 actually built:
  kb:<index>      — §15 retrieval index (legal | case | sop)
  graph:q1..q10   — §14 named queries
  predictions:*   — §13 batch tables / insights
  insights        — persisted lumen_insight rows for the subject
"""
from __future__ import annotations

from dataclasses import dataclass

from lumen.ai.intent import Intent


@dataclass(frozen=True)
class ToolSelection:
    kb_indexes: tuple[str, ...]       # which §15 indexes to retrieve from
    graph_queries: tuple[str, ...]    # which §14 named queries are relevant
    prediction_sources: tuple[str, ...]  # which §13 outputs are relevant
    include_insights: bool            # include persisted insights in bundle


# Deterministic intent → tools table (disclosed configuration).
_SELECTIONS: dict[str, ToolSelection] = {
    "case": ToolSelection(("case",), ("q7", "q8", "q10"), (), True),
    "person": ToolSelection(("case",), ("q1", "q5"), (), True),
    "district": ToolSelection(("case",), ("q4",), ("district_risk", "hotspots"), True),
    "comparison": ToolSelection(("case",), (), ("district_risk",), True),
    "forecast": ToolSelection((), (), ("district_risk", "case_outcome"), True),
    "legal": ToolSelection(("legal",), (), (), False),
    "network": ToolSelection((), ("q1", "q2", "q3", "q6"), (), True),
}


def select(intent: Intent) -> ToolSelection:
    """Step 4: the tools for an intent."""
    return _SELECTIONS[intent]
