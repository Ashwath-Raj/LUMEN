# LUMEN v3 — Architecture (as built)

AI Crime Intelligence Platform · Karnataka State Police · Catalyst-native.

This document describes the architecture **as implemented**, sourced from
LUMEN_MASTER_SPEC_V3 (the single source of truth, §37 frozen at v3). It does
not reinterpret or redesign anything; it records what exists and points to the
specification section that governs each part.

---

## 1. Design philosophy (§0)

Twelve principles govern every decision. Any decision contradicting one is a
defect.

| # | Principle |
|---|---|
| P1 | Intelligence over CRUD — every screen generates or consumes an `Insight` |
| P2 | Evidence before AI — the model never queries the DB; IDs not in the retrieved bundle are dropped server-side |
| P3 | Human in the loop — LUMEN recommends, officers decide |
| P4 | Explainability by default — no score without factors, confidence, method, lineage, limitations |
| P5 | Event-driven intelligence — state changes emit domain events |
| P6 | Catalyst native — Catalyst services used where available; exceptions in §26.3 |
| P7 | Zero trust — every request authenticated, authorised, audited, attributable |
| P8 | Extensible platform — capabilities register through a common interface |
| P9 | Protected attributes are never analytical inputs — deny-list, tested in CI |
| P10 | Identity claims carry uncertainty — every cross-case identity is inferred with confidence |
| P11 | Data is classified and governed — every table declares classification, owner, retention, masking |
| P12 | Fail visibly, degrade gracefully — every dependency has a fallback; the UI states degraded data |

---

## 2. Build tiers (§1)

Tiering is about **truthfulness of claims**, not effort. A T3 subsystem is
never described in the present tense.

- **T1** — Built, live, demonstrated (code, demo, slides).
- **T2** — Built, demonstrated if stable.
- **T3** — Designed and documented, deliberately **not built** (see §9 below).

Subsystem tiers are the §1 table: semantic layer (T1), canonical model (T1),
governance (T1 declaration / T2 enforcement automation), quality (T1),
resolution (T1), contracts (T1), insight/explainability/lineage (T1),
confidence (T1), lifecycle (T1 states / T2 approval), trust (T1), feature store
(T2), prediction (T1), knowledge graph (T1), knowledge base (T1), AI
orchestrator (T1), AI evaluation (T1), decision support (T2), bus (T1), policy
(T1 RBAC / T2 ABAC), event store & audit (T1 partial), service registry (T2),
resource manager (T2), failure strategy (T1), observability (T2). T3:
multi-agent decomposition (§16.6), district digital twin (§36.1), plugin SDK
(§36.2), research extensions & federation (§36.3).

---

## 3. Semantic layer (§2)

Nothing above `db/repositories/` references a table or column name (§28 rule 3).
Everything speaks the **eleven-entity closed vocabulary** (§2.1): `Case`,
`Person`, `CaseParticipant`, `Officer`, `Station`, `Jurisdiction`, `Court`,
`Charge`, `CrimeType`, `ProcessEvent`, `Insight`. Repositories translate;
nothing else does. Canonical display forms live in `semantics/render.py` (§2.3).

---

## 4. Data model (§3)

- **Canonical:** the 27 tables of the supplied KSP ERD, adopted verbatim
  (ADR-002), in `db/models/canonical.py`. Known inconsistencies are handled,
  not fixed (§3.3 → `SCHEMA_NOTES.md`).
- **LUMEN overlay (§3.6):** `lumen_`-prefixed tables, keyed to canonical IDs,
  never duplicating a canonical column. Dropping every `lumen_` table leaves
  exactly the official schema.
- **Migrations:** the schema is created entirely through Alembic (see
  `RUNBOOK.md`); the app never calls `Base.metadata.create_all()`. Migrations
  `0001`–`0011` build the canonical baseline and the `lumen_` overlay tables.

---

## 5. Module layout (§28)

The backend package `api/lumen/` follows §28. Each directory maps to a
specification section:

```
contracts/        §7  — the only shapes crossing a module boundary
semantics/        §2  — entity vocabulary + render forms
db/models/        §3  — canonical + lumen_ tables (the only place table names appear)
db/repositories/  §2  — translation; the only other place table names appear
governance/       §4  — classification, masking, retention
quality/          §5  — rules, engine, scoring
identity/         §6  — entity resolution (normalise, block, score, cluster)
intelligence/     §8-§13 — engine, explain, confidence, lifecycle, counterfactual,
                  risk, hotspots, anomaly, linkage, outcome, features, guards (P9)
graph/            §14 — backend, projection, queries, metrics
kb/               §15 — ingest, retrieve
ai/               §16-§17 — orchestrator, intent, retriever, toolsel, envelope,
                  provider (only LLM call site), eval, prompts
bus/              §19 — signals (only publisher), events, catalog
policy/           §20 — engine (only authoriser), roles, audit_repo
registry/         §22 — models, prompts, services
resilience/       §24 — breaker, timeouts, degradation
observability/    §25 — metrics, health
accelerators/     §26.1 — SmartBrowz briefing, Mail/Push, Zia OCR/voice (T2)
jobs/             seed, precompute, resolve, quality, kb_ingest, feature_precompute
api/routers/      §29 — the HTTP surface
```

### Structural rules (§28, enforced)

1. Routers: parse → one service call → return contract.
2. Services contain no SQL; repositories contain no business rules.
3. Table/column names appear only in `db/repositories/` and `db/models/`.
4. `intelligence/` is the only producer of `Insight`.
5. `ai/provider.py` is the only file that calls an LLM.
6. `bus/signals.py` is the only publisher.
7. `policy/engine.py` is the only authoriser.
8. `contracts/` holds the only shapes crossing module boundaries.
9. The frontend computes nothing.
10. Nothing reads a P9 column outside `governance/masking.py`.

---

## 6. Data flow (as built)

```
canonical data
  → entity resolution (§6)        → lumen_person / lumen_person_link
  → graph projection (§14)        → lumen_graph_edge / lumen_person_metrics / lumen_community
  → quality engine (§5)           → lumen_quality_finding / lumen_quality_score
  → prediction engine (§13)       → lumen_hotspot / lumen_district_risk + insights
  → feature store (§12)           → lumen_feature
  → intelligence (§8-§11)         → lumen_insight (factors, confidence, lineage, limitations)
  → KB ingest (§15)               → lumen_kb_document / lumen_kb_chunk
  → AI orchestrator (§16)         → Insight(kind="summary"), evidence-verified
  → bus (§19)                     → lumen_event (append-only) + dispatch
  → policy (§20) / audit (§21)    → lumen_audit + PolicyDenied on denial
  → registry (§22) · resilience (§24) · observability (§25)  → /system/*
```

Batch precompute (ADR-009) writes the precomputed tables off the request path;
the API reads them. The confidence model (§9) multiplies evidence quality,
model confidence, data completeness, identity confidence, and graph confidence
into one composite — the point at which resolution, quality, and graph become
coherent (ADR-007, ADR-008).

---

## 7. Contracts (§7)

Every inter-module payload is a versioned Pydantic contract in `contracts/`:
`EntityContract`, `InsightContract`, `GraphContract`, `PredictionContract`,
`EvidenceContract`, `EventContract` (+ the recommendation/quality contracts
where their producers exist). Contracts are additive within a major version;
every payload carries `contract_version` (§7 rules).

---

## 8. Architecture decisions

The ten decisions are recorded in [`ADR/`](ADR/README.md) (§35): in-process
graph (001), canonical ERD (002), entity resolution (003), explainability as
structure (004), QuickML primary LLM (005), modular monolith (006), decomposed
confidence (007), quality as product (008), batch precompute (009), protected
attributes stored-never-analysed (010).

---

## 9. Documented, not built (§36) — roadmap only

The following are **explicitly roadmap items. They are documented, not built,
and are never described in the present tense** (§1, §36). No code for any of
them exists.

**36.1 District digital twin** — live district state fusing crime, patrol,
resources and forecast. Requires patrol and resource feeds that do not exist in
the supplied schema. **Blocked on data availability, not engineering** — say
exactly that.

**36.2 Plugin SDK and intelligence marketplace** — capability packs (cyber,
women's safety, narcotics, missing persons) registering through the interface
implied by P8 and §7. The contract layer is designed today; no packs are built.

**36.3 Research extensions** — graph neural networks over the knowledge graph,
federated learning across state clusters with differential privacy, multimodal
evidence (CCTV, video, satellite), digital evidence chain of custody.

**36.4 Multi-state federation** — state-owned clusters with a metadata-only
national aggregation layer, cross-state linkage on anonymised hashes. Legal
architecture, not only technical.

**Multi-agent decomposition (§16.6, T3)** — one orchestrator with tool
selection is what is built. A supervisor routing to specialist agents is the
same capability with more failure modes; documented as the scaling path, not
built.

---

## 10. Related documents

- [`ADR/`](ADR/README.md) — architecture decision records (§35).
- [`GOVERNANCE.md`](GOVERNANCE.md) — classification, asset register, P9, trust (§4, §9, §11).
- [`SCHEMA_NOTES.md`](SCHEMA_NOTES.md) — schema facts and handled inconsistencies (§3).
- [`CATALYST_MAP.md`](CATALYST_MAP.md) — Catalyst service map and P6 register (§26).
- [`RUNBOOK.md`](RUNBOOK.md) — deployment mechanics and operations (§27, §23, §24).
- [`JUDGE_QA.md`](JUDGE_QA.md) — judge questions and answers (§38).
