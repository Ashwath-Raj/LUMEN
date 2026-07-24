# ADR-006 — Modular monolith on AppSail, not microservices

**Status:** Accepted (architecture frozen at v3, §37).

## Context

The platform has many subsystems (§1): semantics, quality, resolution, graph,
prediction, KB, AI orchestrator, bus, policy, registry, resilience,
observability. These must be deployed on Catalyst. The graph runs in-process
(ADR-001) and the ML models share memory; a decomposition strategy must be
chosen that reaches a working Catalyst deployment with the least risk.

## Decision

A **modular monolith on AppSail** (managed runtime, §26.1 #3), not
microservices. One deployable FastAPI service. Module boundaries are enforced
by contracts (§7) and the §28 structural rules, so decomposition later is
mechanical.

## Alternatives Considered

- **Functions-per-domain** — a Catalyst Function per subsystem.
- **Containers** — a container per service.

## Consequences

- One deployable, shared memory for graph and ML (ADR-001's NetworkX runs
  in-process), simplest path to a working Catalyst deployment.
- Module boundaries are enforced by contracts (§7 rule 4: `contracts/` holds
  the only shapes crossing a module boundary) and the §28 structural rules, so
  a later decomposition into services is mechanical rather than a rewrite.
- Catalyst Functions are still used for event-driven work on Signals (§26.1 #1,
  #21) — the monolith and the event functions coexist.

## Specification references

§1 (subsystem tiers), §7 (data contracts), §26.1 #3 (AppSail managed runtime),
§28 (repository structure + structural rules), §35 ADR-006.
