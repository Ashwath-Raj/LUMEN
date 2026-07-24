"""
InsightContract v1 — LUMEN_MASTER_SPEC_V3 §8 (with §10's LifecycleState).

§8: "One object. Everything in the platform that carries meaning is one of
these." The five models below are the specification's own Pydantic code,
reproduced verbatim (fields, types, order). §7's contract table names this
`InsightContract` v1 (producer: intelligence engine; consumers: API, UI, AI,
event bus); §8's code names the class `Insight` — both names are exported.

Two of §8's seven CI invariants are pure schema properties and are enforced
directly on the model, so an invalid object cannot even be constructed:

    2. `limitations` is never empty.
    7. `confidence` equals `confidence_breakdown.composite` to 3 decimal places.

The remaining invariants need a database session (evidence resolution, model
registry, classification of evidence) or the P9 deny-list and are enforced by
`intelligence/explain.py` / `intelligence/lifecycle.py` (the §10 `verified`
gate) and by the CI suite `tests/test_insight_invariants.py`.

Per §7 rule 4, this module is the only shape in which insights cross a module
boundary. Per §28 structural rule 4, `intelligence/` is the only producer.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

# §10 lifecycle states, in chain order:
# Generated → Verified → Approved → Operational → Expired → Archived → Deleted
LifecycleState = Literal[
    "generated",
    "verified",
    "approved",
    "operational",
    "expired",
    "archived",
    "deleted",
]


class Factor(BaseModel):
    label: str
    weight: float
    detail: str | None = None


class Evidence(BaseModel):
    entity: Literal[
        "case",
        "person",
        "participant",
        "officer",
        "station",
        "jurisdiction",
        "court",
        "charge",
        "process_event",
        "kb_document",
    ]
    id: str
    label: str
    url: str  # every evidence chip is clickable (§8)


class Lineage(BaseModel):
    method: str                       # "isolation_forest"
    model_version: str                # → lumen_model_registry
    prompt_version: str | None = None # → lumen_prompt_registry
    features_used: list[str]          # name@version
    query_ids: list[str]
    source_row_count: int
    quality_score: float              # §5.2 for the scope
    computed_at: datetime


class ConfidenceBreakdown(BaseModel):
    evidence_quality: float
    model_confidence: float
    data_completeness: float
    identity_confidence: float
    graph_confidence: float
    composite: float


class Insight(BaseModel):
    id: str
    contract_version: str = "v1"
    kind: Literal[
        "risk",
        "anomaly",
        "linkage",
        "network",
        "forecast",
        "summary",
        "recommendation",
        "data_quality",
    ]
    subject_type: Literal["case", "person", "district", "unit", "state"]
    subject_id: str
    headline: str                     # one plain sentence
    score: float | None = None
    confidence: float
    confidence_breakdown: ConfidenceBreakdown
    factors: list[Factor]
    counterfactuals: list[str]
    evidence: list[Evidence]
    limitations: list[str]            # never empty (§8 invariant 2)
    lineage: Lineage
    lifecycle_state: LifecycleState   # §10
    classification: Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]
    generated_at: datetime
    expires_at: datetime | None = None

    # ── §8 invariant 2: `limitations` is never empty ─────────────────────
    @field_validator("limitations")
    @classmethod
    def _limitations_never_empty(cls, v: list[str]) -> list[str]:
        if not v or not any(s.strip() for s in v):
            raise ValueError(
                "§8 invariant 2: `limitations` is never empty — every insight "
                "must state what it cannot tell you."
            )
        return v

    # ── §8 invariant 7: confidence == breakdown.composite to 3 dp ────────
    @model_validator(mode="after")
    def _confidence_matches_composite(self) -> "Insight":
        if round(self.confidence, 3) != round(self.confidence_breakdown.composite, 3):
            raise ValueError(
                "§8 invariant 7: `confidence` must equal "
                "`confidence_breakdown.composite` to 3 decimal places "
                f"(confidence={self.confidence!r}, "
                f"composite={self.confidence_breakdown.composite!r})."
            )
        return self


# §7 name for the same v1 contract.
InsightContract = Insight
