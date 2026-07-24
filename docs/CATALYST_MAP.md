# LUMEN v3 — Catalyst Service Map

Sourced from LUMEN_MASTER_SPEC_V3 §26. LUMEN is Catalyst-native (P6): where
Catalyst provides a managed service for a capability, that service is used;
exceptions are registered in §26.3.

**Honesty rule (§26.1):** a listed service is used and demonstrable. Rows marked
*Not applicable* say so with a reason. **An unused service claimed as used is
worse than an unused service.**

---

## 1. Complete service map — all 26 capabilities (§26.1)

| # | Capability | Service | LUMEN usage | Tier |
|---|---|---|---|---|
| 1 | Serverless functions | **Functions** | Event functions on Signals: resolution trigger, cache invalidation, notification dispatch, quality rule runs | T1 |
| 2 | Docker image deployment | **AppSail (custom OCI)** | Fallback runtime if ML/geo dependencies exceed the managed runtime. linux/amd64 | T2 |
| 3 | Managed runtime web app | **AppSail (managed)** | Primary FastAPI service | T1 |
| 4 | Frontend / SPA | **Web Client Hosting** | React SPA build output | T1 |
| 5 | Custom domain + SSL | **Domain Mappings** | `lumen.<domain>` if available | T2 |
| 6 | Relational database | **Data Store** | All 27 canonical + all `lumen_` tables | T1 |
| 7 | Unstructured data | **NoSQL** | Graph adjacency snapshots, insight payloads, prompt/response logs | T1 |
| 8 | Object storage | **Stratus** | Evidence assets, exported briefings, model artefacts, KB source documents | T1 |
| 9 | Cache | **Cache** | Overview, hotspots, ego graphs, district risk, AI answers — TTLs in §23 | T1 |
| 10 | Full-text search | **Data Store full-text** | Search over `BriefFacts`; also the RAG fallback path (§24.1) | T1 |
| 11 | Text LLMs / RAG | **QuickML (LLM serving, RAG)** | Generation step and the knowledge base (§15) | T1 |
| 12 | No-code ML pipelines | **QuickML** | Hotspot and anomaly pipelines as managed pipelines | T2 |
| 13 | Automated tabular training | **Zia AutoML** | District risk classifier; case outcome classifier | T1 |
| 14 | OCR / text analytics | **Zia Services** | OCR on scanned FIR/chargesheet uploads into the evidence pipeline; entity extraction from `BriefFacts` | T2 |
| 15 | Voice services | **Zia Services** | Speech-to-text into the Intelligence Console; Kannada→English translation of BriefFacts | T2 |
| 16 | PDF / headless browser | **SmartBrowz** | **Case Intelligence Briefing PDF** — dossier with insights, network figure, timeline, evidence, watermarked per §4.3 | T2 |
| 17 | User auth | **Authentication** | Replaces bespoke JWT entirely | T1 |
| 18 | API routing / throttling | **API Gateway** | Fronts AppSail, edge auth, rate limits `/ai/ask` | T1 |
| 19 | OAuth for Zoho / 3rd party | **Connections** | *Not applicable* — LUMEN integrates no external OAuth service. Stated rather than padded | — |
| 20 | Scheduled jobs | **Cron / Job Scheduling** | `jobs/precompute.py`: resolution, projection, metrics, hotspots, anomalies, quality | T1 |
| 21 | React to in-project events | **Signals + Event Functions** | The intelligence bus (§19) | T1 |
| 22 | Cross-app event bus | **Signals** | Routes `AnomalyDetected` to notification functions | T1 |
| 23 | Multi-step orchestration | **Circuits** | The AI orchestrator pipeline (§16.2) — genuinely branching and parallel | T2 |
| 24 | Transactional email | **Mail** | Anomaly alert to the district officer; briefing delivery | T2 |
| 25 | Push notifications | **Push Notifications** | High-risk alerts to officer devices | T2 |
| 26 | CI/CD | **Pipelines** | Build and deploy client + AppSail on push; runs the §17 eval suite | T2 |

---

## 2. P6 exception register (§26.3)

The only non-Catalyst dependencies. **Anything not in this table is a defect.**

| Dependency | Catalyst equivalent | Reason |
|---|---|---|
| NetworkX (in-process) | None | No graph service exists in Catalyst (ADR-001) |
| scikit-learn (local) | Zia AutoML / QuickML | Deterministic fallback path per P12; Zia AutoML is the primary trainer |
| Leaflet / OSM tiles | None | No map tile service in Catalyst |
| Non-Catalyst LLM | QuickML | **Local development only. Never the deployed path** (ADR-005) |

---

## 3. Data Store migration notes (§26.2)

- Types map: `INT`→number, `VARCHAR`/`TEXT`→text, `DATE`/`TIMESTAMP`→datetime,
  `BOOLEAN`/`BIT`→boolean. **Verify decimal handling for `latitude`/`longitude`
  before seeding** — never store coordinates float-rounded; if a decimal type is
  unavailable, store as text and parse server-side.
- Data Store enforces relationships less strictly than PostgreSQL, so
  referential integrity also lives in `db/repositories/` — every write validates
  parents.
- Seed via bulk import, not row-by-row.
- A `DATABASE_URL` switch runs PostgreSQL locally and Data Store deployed,
  behind one repository interface. **Both paths pass the same repository test
  suite.**

---

## 4. Backend-swappable Catalyst integrations (as built)

Several Catalyst services are external and unavailable in the local
environment. Following ADR-001's pattern ("the API must not know which backend
answered"), these are implemented behind swappable interfaces with local
deterministic backends, and the Catalyst client slots in at deployment:

- **Cache (#9):** `services/cache.py` — in-process TTL cache (the §23 TTLs) with
  a `CacheBackend` interface; Catalyst Cache swaps in at deploy.
- **Cron (#20):** `jobs/precompute.py` — the staggered, idempotent, checkpointed
  precompute pipeline as a plain callable; Catalyst Cron schedules it at deploy.
- **SmartBrowz (#16):** `accelerators/briefing.py` — dossier assembly +
  swappable renderer → Stratus URL.
- **Mail (#24) / Push (#25):** `accelerators/notify.py` — swappable backends
  with a local outbox.
- **Zia OCR/voice (#14, #15):** `accelerators/zia.py` — honest stubs that report
  the capability as unavailable rather than fabricating output; the Zia client
  swaps in at deploy.
- **QuickML LLM (#11):** `ai/provider.py` — the single LLM call site; QuickML is
  primary, a dev-fallback provider sits behind the same interface (ADR-005),
  and generation-unavailable degrades to the §16.4 deterministic fallback.

Deployment-time substitution of each is described in its module and in
[`RUNBOOK.md`](RUNBOOK.md).
