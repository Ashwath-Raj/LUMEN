# ADR-008 — Data quality as an intelligence product, not a maintenance chore

**Status:** Accepted (architecture frozen at v3, §37).

## Context

Government data is messy (§5). The naive response is to silently clean it. But
how the data was produced is itself evidence — a `CrimeNo` that encodes one
unit while being registered to another is a real signal, not noise to be
scrubbed. LUMEN never deletes canonical records (§4.3 rule 1); it is an
analytical overlay.

## Decision

Data quality is an **intelligence product** (§5), not a maintenance chore. The
18-rule engine (§5.1) scores six dimensions per scope (§5.2) and surfaces
findings three ways (§5.3): as `Insight(kind="data_quality")` on the affected
entity, as a `/quality` administrative surface, and as a **confidence input**
so insights over poor data honestly report lower confidence.

## Alternatives Considered

- **Silent cleaning** — quietly correct the data.
- **Ignore** — treat quality as out of scope.

## Consequences

- Cleaning silently **destroys evidence** about how the data was produced;
  surfacing quality preserves it.
- Quality becomes an **administrative product** ("which stations need
  data-entry support", §5.3) — a screen no other team will have.
- Quality **feeds confidence** (§5.3 item 3, §9 `data_completeness`), which is
  the connection that makes the platform coherent rather than a bolt-on.
- Findings are `data_quality` insights (§5.3 item 1), so they pass through the
  same explainability structure as every other claim (ADR-004).

## Specification references

§5 (data quality engine), §5.1 (rule catalogue), §5.2 (scoring), §5.3 (quality
as intelligence), §4.3 rule 1 (never deletes canonical), §9 (confidence),
§35 ADR-008.
