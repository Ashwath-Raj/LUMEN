# Architecture Decision Records

The ten architecture decisions for LUMEN v3, one file per record, per
LUMEN_MASTER_SPEC_V3 §35 ("Full records in `docs/ADR/`"). Each record follows
the structure: Title · Status · Context · Decision · Alternatives Considered ·
Consequences · Specification references.

The Decision, Alternatives, and Rationale of every ADR are taken verbatim from
§35's summary table; Context and Consequences are drawn from the specification
sections each decision governs — no new decisions are introduced (§37: the
architecture is frozen at v3).

| ADR | Decision |
|---|---|
| [001](ADR-001-graph-in-process.md) | Graph analytics in-process (NetworkX) |
| [002](ADR-002-adopt-ksp-erd.md) | Adopt the supplied KSP ERD verbatim as canonical |
| [003](ADR-003-build-entity-resolution.md) | Build entity resolution rather than treating `Accused` as identity |
| [004](ADR-004-explainability-as-structure.md) | Explainability as a data structure (`Insight`) |
| [005](ADR-005-quickml-primary-llm.md) | QuickML as the primary LLM provider |
| [006](ADR-006-modular-monolith.md) | Modular monolith on AppSail, not microservices |
| [007](ADR-007-decomposed-confidence.md) | Confidence as a decomposed product, not a scalar |
| [008](ADR-008-quality-as-product.md) | Data quality as an intelligence product |
| [009](ADR-009-batch-precompute.md) | Batch precompute over on-demand analytics |
| [010](ADR-010-protected-attributes.md) | Protected attributes stored but never analysed |

**Change control (§37).** The architecture is frozen at v3. A change is
admissible only if it (1) fixes a contradiction in the specification,
(2) removes a subsystem, or (3) is required to make a T1 item work. Every
change is recorded here with date, reason, and the sections affected.
