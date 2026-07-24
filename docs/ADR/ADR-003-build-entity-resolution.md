# ADR-003 — Build entity resolution rather than treating `Accused` as identity

**Status:** Accepted (architecture frozen at v3, §37).

## Context

The canonical schema has **no person master** (§3.2 fact 1): `Accused` is keyed
by `AccusedMasterID` and carries `CaseMasterID` — a per-case row, not a human.
`Accused.PersonID` is a `VARCHAR` holding `A1, A2, A3…`, ordering within a case,
never identity (§3.2 fact 2). Without a way to link the same person across
cases, the network graph has no edge longer than one case and "repeat offender"
is uncomputable (§6). The available signals are thin (§6.1): name, implied
birth year, gender, arrest districts/stations, IO, act-section signature.

## Decision

Build **entity resolution** (§6): normalise → block (gender + Double Metaphone)
→ score a weighted feature vector per candidate pair (§6.3) → threshold
(≥0.85 auto-link, 0.65–0.85 candidate, <0.65 reject) → cluster → persist
`lumen_person` + `lumen_person_link` with per-link confidence and match
features. Every inferred identity carries confidence and a "see why" disclosure
(§6.4, P10).

## Alternatives Considered

- **Join on name** — treat identical `AccusedName` as the same person.
- **Ignore cross-case identity** — treat `Accused` as identity.

## Consequences

- Without resolution the network graph has no edge longer than one case, and
  naive name joins are **defamatory for common names** — hence the mandatory
  inverse-frequency common-name penalty (§6.3), without which frequent names
  collapse hundreds of unrelated people into one node.
- Identity is always **inferred** and never asserted (P10, §6.4): the UI says
  "high-confidence match (0.91), here is why", never "this is the same person".
- Every resolved identity carries a "report incorrect match" control writing to
  `lumen_person_dispute` and emitting `PersonMatchDisputed` — human-in-the-loop
  is visible, not asserted (§6.4, P3).
- Resolution confidence propagates into every downstream insight's confidence
  (§6.4, §9 `identity_confidence`).

## Specification references

§3.2 (schema facts 1–2), §6 (entity resolution), §6.1 (signals),
§6.3 (feature weights), §6.4 (presentation rules), §9 (confidence), P3, P10,
§35 ADR-003.
