# ADR-002 — Adopt the supplied KSP ERD verbatim as canonical

**Status:** Accepted (architecture frozen at v3, §37).

## Context

The build began from a prototype carrying roughly 61 models. The organisers
supplied a *Police FIR System — ER Diagram* (the KSP ERD). A canonical data
model must be chosen: the supplied ERD, the prototype's models, or a hybrid.
The canonical model must migrate to Catalyst Data Store (§26.2) and be
trustworthy to a police-department judge.

## Decision

Adopt the supplied KSP ERD **verbatim** as canonical. Column and key names are
not "improved" (§3.1). Twenty-six tables are defined; two more are referenced
in the relationship matrix and handled per §3.4. The result is the 27 canonical
tables (§3.5).

## Alternatives Considered

- **Keep the prototype's ~61 models.**
- **Hybrid** of prototype and supplied ERD.

## Consequences

- **Provenance and trust** — the schema is the one the organisers supplied,
  not a reinterpretation.
- 27 well-defined tables are migratable to Data Store where 61 tangled ones are
  not (§26.2: bulk import, one repository interface, both PostgreSQL and Data
  Store pass the same test suite).
- Known inconsistencies are **handled, not silently fixed** (§3.3) and logged
  in `SCHEMA_NOTES.md`; each becomes a `data_quality` insight where detectable
  at runtime.
- `LUMEN_`-prefixed tables (§3.6) are an overlay only: "A judge must be able to
  drop every `lumen_` table and be left with exactly the official schema."

## Specification references

§3 (canonical data model), §3.1 (source of truth), §3.3 (known
inconsistencies), §3.4 (referenced but undefined), §3.5 (canonical DDL),
§3.6 (LUMEN-owned tables), §26.2 (Data Store migration), §35 ADR-002.
