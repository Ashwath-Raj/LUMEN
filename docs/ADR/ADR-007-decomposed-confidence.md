# ADR-007 — Confidence as a decomposed product, not a scalar

**Status:** Accepted (architecture frozen at v3, §37).

## Context

An insight often rests on a chain of inferences: retrieved evidence, a model's
own probability, the completeness of the underlying data, the confidence of an
inferred identity, and the support of the graph. A single scalar confidence
hides which link is weakest and reads as more certain than the chain warrants —
"an insight resting on a 0.66-confidence identity match should not read as
certain" (§9).

## Decision

Confidence is a **decomposed product** (§9), not a scalar:

```
composite = evidence_quality × model_confidence × data_completeness
          × identity_confidence × graph_confidence
```

Each component has a defined formula and a not-applicable value of 1.0. The UI
names the **limiting** component — *"limited by identity match confidence
(0.61)."*

## Alternatives Considered

- **Model probability alone** — a single scalar from the model.

## Consequences

- A chain of inferences is only as strong as its weakest link; **multiplicative
  composition is deliberate** (§9), so any weak component drags the composite
  down honestly.
- Decomposition lets the UI **name the limiting factor** rather than assert a
  number, which is worth more to a judge than a higher number would be (§9
  display bands: ≥0.80 High · 0.55–0.79 Moderate · <0.55 Low).
- Resolution confidence (ADR-003) feeds `identity_confidence`; quality scores
  (ADR-008) feed `data_completeness` — the confidence model is where the
  subsystems become coherent rather than a bolt-on (§5.3).
- `Insight.confidence` must equal `confidence_breakdown.composite` to three
  decimals (§8 invariant 7, CI-enforced).

## Specification references

§8 (ConfidenceBreakdown, invariant 7), §9 (confidence model), §5.3 (quality
feeds confidence), §6.4 (resolution confidence propagates), §35 ADR-007.
