# ADR-009 — Batch precompute over on-demand analytics

**Status:** Accepted (architecture frozen at v3, §37).

## Context

Centrality and clustering over the association graph, DBSCAN over incident
coordinates, and anomaly/risk scoring are expensive. The ten named graph
queries must answer in under 400 ms (§14.5, §33). Computing these per request
cannot meet an interactive latency budget, and the platform must remain useful
when dependencies fail (§24).

## Decision

**Batch precompute over on-demand analytics** (§14.5, §23). The precompute
pipeline (`jobs/precompute.py`) runs resolution → projection + metrics →
quality → predictions → features, staggered on Catalyst Cron (§26.1 #20), and
writes precomputed tables. The API reads those tables; nothing heavy runs in
the request path (§23).

## Alternatives Considered

- **Compute per request** — on-demand analytics.

## Consequences

- Centrality and clustering cannot meet an interactive latency budget;
  precomputed tables can (§14.5: "Any request path exceeding 400 ms reads a
  precomputed table instead").
- Precomputed tables also **survive dependency failure** (§24): the degradation
  ladder's L2 (precomputed-only) serves from these tables when the cache is
  cold and live queries fail.
- Precompute stages are **idempotent and checkpointed** (§23, §24.3 rule 4), so
  a partial run resumes rather than restarts.
- "Batch jobs never run in the request path" (§23) — the request path only
  reads.

## Specification references

§14.5 (projection pipeline, latency budget), §23 (resource manager),
§24 (failure strategy, degradation ladder), §24.3 rule 4, §26.1 #20 (Cron),
§35 ADR-009.
