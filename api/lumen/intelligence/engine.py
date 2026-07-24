"""
Prediction engine orchestration — LUMEN_MASTER_SPEC_V3 §13 (Session 10 slice
of the intelligence engine; §8-§11 orchestration beyond predictions arrives
with its own sessions).

`run_predictions` is the §13 batch step: it runs all six model scorers,
registers each model version in `lumen_model_registry` (so §8 invariant 5
holds for every produced insight), and converts every `PredictionContract`
into a Session 8 `Insight` — §33's Session 10 criterion: "Insights carry
factors, counterfactuals, limitations."

  * `factors` — §13: feature importances, straight from each model.
  * `limitations` — §13: the training window line each contract already
    carries (structurally enforced on PredictionContract).
  * `counterfactuals` — generated for the kinds whose surfaces mandate them
    (§30.4 risk, §30.8 forecast) by `counterfactual.py` (Session 11), which
    completes §33 row 10's done-when. Other kinds carry the field empty —
    §8 places no never-empty invariant on counterfactuals.

Insight kinds (§8's closed vocabulary offers no per-model mapping — choice
disclosed): district_risk/hotspots → "risk", volume_anomaly/reporting_delay →
"anomaly", case_linkage → "linkage", case_outcome → "forecast".

All insights are persisted in `generated` state (§10 — nothing surfaces
without the verified gate). Deterministic ids (uuid5 over model+subject) make
re-runs upserts, not duplicates. Per §28 rule 4, `intelligence/` is the
producer of these Insights.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from lumen.contracts.insight import Insight, Lineage
from lumen.contracts.prediction import PredictionContract
from lumen.db.models.intelligence import LumenModelRegistry
from lumen.intelligence import confidence as C
from lumen.intelligence.anomaly import score_reporting_delay, score_volume_anomaly
from lumen.intelligence.counterfactual import counterfactuals_for
from lumen.intelligence.hotspots import score_hotspots
from lumen.intelligence.lifecycle import save_insight
from lumen.intelligence.linkage import score_case_linkage
from lumen.intelligence.outcome import score_case_outcome
from lumen.intelligence.risk import score_district_risk

_NS = uuid.UUID("d3f00000-0000-4000-8000-000000000013")

KIND_OF = {
    "district_risk": "risk",
    "hotspots": "risk",
    "volume_anomaly": "anomaly",
    "reporting_delay": "anomaly",
    "case_linkage": "linkage",
    "case_outcome": "forecast",
}

ALL_MODELS = ("district_risk", "hotspots", "volume_anomaly",
              "case_linkage", "case_outcome", "reporting_delay")


def _model_confidence(contract: PredictionContract) -> float:
    """§9: 'Model's own probability, or 1 − normalised anomaly distance';
    1.0 when the model exposes neither."""
    out = contract.output
    if contract.model == "district_risk":
        return float(out["score"])
    if contract.model == "case_outcome":
        return max(out["probabilities"].values())
    if contract.model == "volume_anomaly":
        # IsolationForest score_samples is more negative for more anomalous;
        # report 1 − normalised distance capped into [0, 1].
        return max(0.0, min(1.0, 1.0 + float(out["isolation_forest_score"])))
    return C.NOT_APPLICABLE


def _to_insight(session: Session, contract: PredictionContract) -> Insight:
    scope = (("district", contract.subject_id)
             if contract.subject_type == "district" else ("state", "karnataka"))
    breakdown = C.compose(
        model_confidence=_model_confidence(contract),
        data_completeness=C.data_completeness(session, *scope),
    )
    headline = {
        "district_risk": f"District {contract.subject_id} risk band: "
                         f"{contract.output.get('band')}.",
        "hotspots": f"Hotspot cluster of {contract.output.get('weight')} cases "
                    f"in district {contract.subject_id}.",
        "volume_anomaly": f"District {contract.subject_id} case volume spiked "
                          f"{contract.output.get('sigma')}σ above baseline.",
        "case_linkage": f"Case {contract.subject_id} has "
                        f"{len(contract.output.get('ranked_linked_cases', []))} "
                        "ranked linked case(s).",
        "case_outcome": f"Case {contract.subject_id} outcome probabilities "
                        "computed across cstype A/B/C.",
        "reporting_delay": f"Unit {contract.subject_id} shows anomalous "
                           "reporting delay.",
    }[contract.model]
    # discriminator so multiple findings per subject (e.g. two hotspot
    # clusters in one district, two spike weeks) get distinct, stable ids
    disc = str(contract.output.get("cluster_id", contract.output.get("spike_week", "")))
    return Insight(
        id=str(uuid.uuid5(_NS, f"{contract.model}:{contract.subject_type}:{contract.subject_id}:{disc}")),
        kind=KIND_OF[contract.model],
        subject_type=contract.subject_type,
        subject_id=contract.subject_id,
        headline=headline,
        score=None,
        confidence=breakdown.composite,
        confidence_breakdown=breakdown,
        factors=contract.factors,
        # §33 row 10: "Insights carry factors, counterfactuals, limitations."
        # Generated for the kinds whose surfaces mandate them (§30.4 risk,
        # §30.8 forecast); see intelligence/counterfactual.py.
        counterfactuals=counterfactuals_for(KIND_OF[contract.model], contract.factors),
        evidence=[],                  # subject-level predictions carry no record chips
        limitations=contract.limitations,
        lineage=Lineage(
            method=contract.model, model_version=contract.model_version,
            prompt_version=None, features_used=[f.label for f in contract.factors],
            query_ids=[], source_row_count=0,
            quality_score=C.data_completeness(session, *scope),
            computed_at=contract.computed_at,
        ),
        lifecycle_state="generated",
        classification="INTERNAL",    # district risk / hotspot examples in §4.1
        generated_at=contract.computed_at,
    )


def run_predictions(session: Session, *, now: datetime | None = None) -> dict:
    """§13 batch scoring: run all six models, persist their tables, register
    model versions, and persist every prediction as a generated Insight."""
    now = now or datetime.now(timezone.utc)

    contracts: list[PredictionContract] = []
    contracts += score_district_risk(session, now=now)
    contracts += score_hotspots(session, now=now)
    contracts += score_volume_anomaly(session, now=now)
    contracts += score_case_linkage(session, now=now)
    contracts += score_case_outcome(session, now=now)
    contracts += score_reporting_delay(session, now=now)

    for name in ALL_MODELS:
        session.merge(LumenModelRegistry(
            model_id=f"{name}@v1", name=name, kind="prediction", version="v1",
            params={}, metrics={}, trained_at=now, active=True,
        ))

    insights = 0
    for contract in contracts:
        save_insight(session, _to_insight(session, contract))
        insights += 1

    session.commit()
    by_model: dict[str, int] = {}
    for contract in contracts:
        by_model[contract.model] = by_model.get(contract.model, 0) + 1
    return {"predictions": len(contracts), "insights": insights, **by_model}
