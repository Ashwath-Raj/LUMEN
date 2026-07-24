"""
Confidence model — LUMEN_MASTER_SPEC_V3 §9.

"Confidence stops being a decorative number. It is computed, decomposed, and
displayed as its parts."

    composite = evidence_quality
              × model_confidence
              × data_completeness
              × identity_confidence
              × graph_confidence

Component definitions (§9's table; each is 1.0 when not applicable):

  evidence_quality    Retrieved evidence count ÷ expected, capped at 1,
                      weighted by source classification.
  model_confidence    Model's own probability, or 1 − normalised anomaly
                      distance. Supplied by the producing model (Session 10+).
  data_completeness   `lumen_quality_score` completeness dimension for the
                      scope (§5.2 — Session 6 output).
  identity_confidence Minimum resolution confidence across persons in the
                      evidence (§6 — Session 7 output).
  graph_confidence    Edge support: 1 − 1/(1 + supporting_edges), damped by
                      projection staleness (§14 graph — Session 9).

Two details are NOT defined by the specification and are therefore exposed as
explicit caller parameters rather than invented constants:
  * the per-classification weights for evidence_quality ("weighted by source
    classification" — no weight table is given). Default: neutral 1.0 per item.
  * the projection-staleness damping for graph_confidence (no formula given).
    Default: no damping (factor 1.0).
In Session 8 no retriever (§15/§16) and no graph (§14) exist, so both
components take the spec-defined not-applicable value of 1.0 in practice.

§9 display bands: ≥0.80 High · 0.55–0.79 Moderate · <0.55 Low. Low-confidence
insights are rendered de-emphasised with the weakest component named —
"limited by identity match confidence (0.61)".

Multiplicative is deliberate (§9): a chain of inferences is only as strong as
its weakest link.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from lumen.contracts.insight import ConfidenceBreakdown, Evidence
from lumen.db.models.identity import LumenPerson
from lumen.db.models.quality import LumenQualityScore

# §10: "Anything below the confidence floor (0.35) is `generated` and never
# surfaces." The floor is applied by the lifecycle (§10), defined once here.
CONFIDENCE_FLOOR = 0.35

# §9 display bands.
BAND_HIGH = 0.80       # ≥ 0.80 High
BAND_MODERATE = 0.55   # 0.55–0.79 Moderate; < 0.55 Low

# Human-readable component names for the weakest-link sentence. The §9 example
# names identity as "identity match confidence".
_COMPONENT_LABELS: dict[str, str] = {
    "evidence_quality": "evidence quality",
    "model_confidence": "model confidence",
    "data_completeness": "data completeness",
    "identity_confidence": "identity match confidence",
    "graph_confidence": "graph confidence",
}

NOT_APPLICABLE = 1.0   # §9: "Value when not applicable: 1.0" for every component


# ── Component computations (§9 table) ──────────────────────────────────────

def evidence_quality(
    retrieved: int | None,
    expected: int | None,
    *,
    weights: list[float] | None = None,
) -> float:
    """Retrieved evidence count ÷ expected, capped at 1, weighted by source
    classification. `weights` is one weight per retrieved item; the
    specification does not define the per-classification weight values, so
    they must be supplied by the caller — absent, each item weighs 1.0
    (neutral). Not applicable (no retrieval expectation) → 1.0."""
    if retrieved is None or expected is None or expected <= 0:
        return NOT_APPLICABLE
    if weights is not None:
        if len(weights) != retrieved:
            raise ValueError("weights must have one entry per retrieved evidence item")
        weighted_count = float(sum(weights))
    else:
        weighted_count = float(retrieved)
    return min(1.0, weighted_count / float(expected))


def model_confidence(
    probability: float | None = None,
    *,
    normalised_anomaly_distance: float | None = None,
) -> float:
    """Model's own probability, or 1 − normalised anomaly distance.
    Not applicable (no model in the chain) → 1.0."""
    if probability is not None:
        return float(probability)
    if normalised_anomaly_distance is not None:
        return 1.0 - float(normalised_anomaly_distance)
    return NOT_APPLICABLE


def data_completeness(session: Session, scope_type: str, scope_id: str) -> float:
    """`lumen_quality_score` completeness dimension for the scope (§5.2).
    No score row for the scope → not applicable → 1.0."""
    row = (
        session.query(LumenQualityScore)
        .filter(
            LumenQualityScore.scope_type == scope_type,
            LumenQualityScore.scope_id == scope_id,
            LumenQualityScore.dimension == "completeness",
        )
        .order_by(LumenQualityScore.computed_at.desc())
        .first()
    )
    return float(row.score) if row is not None else NOT_APPLICABLE


def identity_confidence(session: Session, evidence: list[Evidence]) -> float:
    """Minimum resolution confidence across persons in the evidence (the §6
    lumen_person.resolution_confidence, always carried per P10).
    No person evidence → 1.0."""
    person_ids = [e.id for e in evidence if e.entity == "person"]
    if not person_ids:
        return NOT_APPLICABLE
    confidences: list[float] = []
    for pid in person_ids:
        person = session.get(LumenPerson, pid)
        if person is not None and person.resolution_confidence is not None:
            confidences.append(float(person.resolution_confidence))
    return min(confidences) if confidences else NOT_APPLICABLE


def graph_confidence(
    supporting_edges: int | None,
    *,
    staleness_damping: float = 1.0,
) -> float:
    """Edge support: 1 − 1/(1 + supporting_edges), damped by projection
    staleness. The damping formula is not defined by the specification, so the
    factor is caller-supplied (default 1.0 — no damping). No graph in the
    chain (the §14 projection is Session 9) → not applicable → 1.0."""
    if supporting_edges is None:
        return NOT_APPLICABLE
    return (1.0 - 1.0 / (1.0 + float(supporting_edges))) * float(staleness_damping)


# ── Composition (§9) ───────────────────────────────────────────────────────

def compose(
    *,
    evidence_quality: float = NOT_APPLICABLE,
    model_confidence: float = NOT_APPLICABLE,
    data_completeness: float = NOT_APPLICABLE,
    identity_confidence: float = NOT_APPLICABLE,
    graph_confidence: float = NOT_APPLICABLE,
) -> ConfidenceBreakdown:
    """Build the §8 ConfidenceBreakdown with §9's multiplicative composite."""
    composite = (
        evidence_quality
        * model_confidence
        * data_completeness
        * identity_confidence
        * graph_confidence
    )
    return ConfidenceBreakdown(
        evidence_quality=evidence_quality,
        model_confidence=model_confidence,
        data_completeness=data_completeness,
        identity_confidence=identity_confidence,
        graph_confidence=graph_confidence,
        composite=composite,
    )


# ── Display (§9 bands + weakest component) ─────────────────────────────────

def band(composite: float) -> str:
    """§9: ≥0.80 High · 0.55–0.79 Moderate · <0.55 Low."""
    if composite >= BAND_HIGH:
        return "High"
    if composite >= BAND_MODERATE:
        return "Moderate"
    return "Low"


def weakest_component(breakdown: ConfidenceBreakdown) -> tuple[str, float]:
    """The limiting factor — the smallest of the five components."""
    values = {name: getattr(breakdown, name) for name in _COMPONENT_LABELS}
    name = min(values, key=lambda k: values[k])
    return name, values[name]


def limitation_sentence(breakdown: ConfidenceBreakdown) -> str:
    """§9: the weakest component named — 'limited by identity match
    confidence (0.61)'."""
    name, value = weakest_component(breakdown)
    return f"limited by {_COMPONENT_LABELS[name]} ({value:.2f})"
