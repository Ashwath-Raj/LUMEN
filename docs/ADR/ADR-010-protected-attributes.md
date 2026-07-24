# ADR-010 — Protected attributes stored but never analysed

**Status:** Accepted (architecture frozen at v3, §37).

## Context

The canonical schema defines protected attributes — caste, religion, blood
group, disability status (`CasteID`, `ReligionID`, `Employee.BloodGroupID`,
`Employee.PhysicallyChallenged`). Two failure modes exist: dropping them breaks
fidelity to the supplied schema (ADR-002), while using them as features encodes
bias into policing. P9 governs: "Protected attributes are never analytical
inputs."

## Decision

Protected attributes are **stored but never analysed** (P9, §35). They are kept
because the canonical schema defines them (ADR-002), and excluded from every
feature, filter, chart, prompt, and map layer. Enforcement is **structural**, not
a convention: `intelligence/guards.py` holds the deny-list, every
feature/prompt/chart builder passes through it, and a CI test fails the build
if a denied column reaches a model input (§4.3 rule 6).

## Alternatives Considered

- **Drop them** — omit the columns from the canonical model.
- **Use them as features** — treat them as analytical inputs.

## Consequences

- Dropping breaks canonical fidelity (ADR-002: the official schema must be
  reproducible by dropping `lumen_` tables); using them encodes bias into
  policing.
- Enforcement is **in CI**, not by review: the P9 deny-list guard raises on any
  denied `(table, column)`, and `test_p9_guards.py` fails the build if a denied
  column reaches a model input.
- Nothing reads a P9 column outside the governed display path in
  `governance/masking.py` (§28 structural rule 10).
- `Insight` invariant 4 (§8) — no `Factor.label` references a P9 attribute — is
  the same rule applied to explanation text.
- Among LUMEN's stated red lines (§11): "use protected attributes" is something
  LUMEN will never do.

## Specification references

§3.5 (P9-marked columns), §4.3 rule 6 (structural P9 enforcement),
§8 invariant 4, §11 (red lines), §28 structural rule 10, P9, §35 ADR-010.
