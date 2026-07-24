"""
PredictionContract v1 — LUMEN_MASTER_SPEC_V3 §7, §13.

§7's contract table lists `PredictionContract` (v1, produced by the prediction
engine, consumed by the intelligence engine) but — as with `EntityContract`
and `GraphContract` — defines no field-level shape anywhere. What §13 does
fix: each model's Output column (band + score + factor weights; clusters +
weights; spike + baseline + σ; ranked linked cases; P(cstype ∈ A/B/C) +
factors; units with anomalous delay), plus three rules that shape every
prediction: feature importances become `factors`, the training window is
stated in `limitations`, and models batch-score into tables.

`PredictionContract` below is therefore the established minimal versioned
envelope (the EntityContract/GraphContract precedent): the §13 table row it
came from (`model`, `kind`), the §2.1 subject it scores, the model-specific
`output` dict (§13's Output column, verbatim keys per model), the §13-rule
fields (`factors`, `limitations`, `model_version`), and `computed_at`.
Nothing beyond §13's own vocabulary is invented.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

from lumen.contracts.insight import Factor

# §13's six model rows.
PredictionModel = Literal[
    "district_risk", "hotspots", "volume_anomaly",
    "case_linkage", "case_outcome", "reporting_delay",
]
# §13 Kind column.
PredictionKind = Literal["Classification", "Unsupervised", "Detection", "Similarity"]


class PredictionContract(BaseModel):
    contract_version: str = "v1"
    model: PredictionModel
    kind: PredictionKind
    subject_type: Literal["case", "person", "district", "unit", "state"]
    subject_id: str
    output: dict                      # §13 Output column, per model
    factors: list[Factor]             # §13: "Every model reports feature importances"
    limitations: list[str]            # §13: "Every prediction states its training window"
    model_version: str                # → lumen_model_registry (§8 invariant 5)
    computed_at: datetime

    @field_validator("limitations")
    @classmethod
    def _training_window_stated(cls, v: list[str]) -> list[str]:
        """§13 rule: 'Every prediction states its training window in
        limitations.' Enforced structurally: at least one limitation line
        must mention the window."""
        if not any("window" in s.lower() or "trained on" in s.lower() for s in v):
            raise ValueError(
                "§13: every prediction must state its training window in "
                "`limitations`."
            )
        return v
