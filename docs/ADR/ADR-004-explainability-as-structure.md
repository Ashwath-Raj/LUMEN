# ADR-004 — Explainability as a data structure (`Insight`), not a UI feature

**Status:** Accepted (architecture frozen at v3, §37).

## Context

P4 requires explainability by default: no score without factors, confidence,
method, lineage, and stated limitations. If explanation is produced as free
text by the model, it cannot be tested, cached, or guaranteed present, and it
can be silently omitted. Every screen in the platform generates or consumes
meaning (P1), so a single explainable object is needed.

## Decision

Explainability is a **data structure** — the `Insight` (§8) — not a UI feature.
One object carries `factors`, `confidence` + `confidence_breakdown`,
`lineage`, `evidence`, `counterfactuals`, and `limitations` (never empty).
Seven invariants are enforced in CI (§8). Tree ensembles are chosen over deep
learning for the same reason — they report feature importances, which become
`factors` (§13).

## Alternatives Considered

- **Explanation strings from the model** — free-text rationale.

## Consequences

- Structure makes explanation **testable, cacheable, and impossible to omit**:
  the seven §8 invariants (score only inside an Insight, non-empty limitations,
  resolvable evidence IDs, no P9 in a factor label, model version registered,
  classification ≥ evidence, confidence == composite) are CI-enforced.
- `intelligence/` is the only producer of `Insight` (§28 rule 4); the object is
  the platform's "output currency" (§2.1).
- Tree ensembles are preferred because they expose feature importances (§13),
  the direct source of `Insight.factors`.

## Specification references

§8 (Insight, explainability, lineage), §8 invariants, §13 (prediction engine —
feature importances), §28 structural rule 4, P1, P4, §35 ADR-004.
