# LUMEN Repository Migration — Structural Alignment to LUMEN v3 Master Spec

**Status:** COMPLETE — two passes: (1) structural migration §1-§7 below, (2) a subsequent sanitation pass, §8, that superseded some of pass (1)'s conservative choices at the user's explicit direction.
**Authority:** `docs/LUMEN_MASTER_SPEC_V3.md`, §28 Repository Structure.

This document is the record required by the migration brief: what moved, what was archived, what was deleted, dependency changes, and remaining work before Session 1 implementation can begin in earnest.

**⚠️ Superseded claims:** §1-§7 below describe the FIRST pass, which deliberately preserved the legacy `legacy/` archive and kept the old JWT auth / Gemini AI / SQLAlchemy DB layer functionally working ("nothing regresses"). **§8 records a second pass that reversed this**: `legacy/` was deleted outright, and the working auth/AI/DB-boot code was removed and replaced with `HTTP 501` stubs, per the user's explicit, twice-confirmed instruction to prioritize a clean minimal skeleton over keeping legacy behavior alive. Read §8 for the current state of the repository; §1-§7 is retained as a historical record of the first pass's reasoning, not a description of the current tree.

**Validation performed (see §7 and §8.6):** the frontend builds cleanly from `client/` (1636 modules, zero errors). The FastAPI backend currently boots with **zero environment variables and zero external dependencies** (no database, no AI provider, no Neo4j) — `from main import app` succeeds, `/health` returns 200, and every other endpoint returns 501 with a message naming the future session that will implement it.

---

## 0. Decisions confirmed with the user before execution

| # | Decision | Chosen |
|---|---|---|
| 1 | Repo root | Restructure **in place inside `LUMEN/`** (preserves git history/remote). The outer `LUmen/` wrapper is untouched; `Docs/` moves down into `LUMEN/docs/`. |
| 2 | Graph backend (ADR-001: NetworkX in-process primary, Neo4j optional/additive) | **Structure only, no logic.** Create empty `graph/{backend.py,projection.py,queries.py,metrics.py}` placeholders. Move existing live Neo4j code to `/legacy` for reference. Do not implement the NetworkX backend — that is Session 9 (§33) work. |
| 3 | ~28 loose backend dev/debug scripts + ~14 loose frontend scripts, none imported by the running app | **Move all to `/legacy`, delete none**, per the "prefer /legacy over deleting" rule. `schema_dump.py`'s embedded plaintext DB credential is flagged below for rotation, not scrubbed (file preserved verbatim in `/legacy`). |
| 4 | Frontend modules with no mapping in the frozen §30 IA (Operations, Administration, most of Analytics) | **Move to `/legacy/client-extra`**, not wired into the new `client/` route tree. |

---

## 1. Target structure (§28, verbatim)

```
lumen/                                    (= repo root, i.e. LUMEN/)
├── catalyst.json · README.md · Makefile · .env.example
├── client/                               → Web Client Hosting
│   ├── client-package.json
│   ├── app/src/{main.tsx, app/{router,providers,shell}, design/{tokens.css,motion.ts,primitives/},
│   │            api/{client.ts,types.ts,hooks/}, components/{insight,graph,map,timeline,charts,identity,quality}/,
│   │            features/{command-center,geo,case,person,network,intelligence,predictions,quality}/}
│   └── dist/
├── functions/                            → Catalyst Functions
│   └── on_case_registered/ on_anomaly_detected/ on_graph_projected/ on_quality_finding/
├── api/                                  → AppSail
│   ├── app-config.json · requirements.txt · main.py
│   └── lumen/{config.py, contracts/, semantics/, db/{session.py,datastore.py,models/,repositories/},
│              services/, identity/, quality/, governance/, intelligence/, graph/, kb/, ai/, bus/,
│              policy/, registry/, resilience/, observability/, api/{deps.py,routers/}, jobs/}
├── data/{schema.sql, seeds/, eval/golden.yaml}
├── docs/{ARCHITECTURE.md, ADR/, SCHEMA_NOTES.md, GOVERNANCE.md, DEMO_SCRIPT.md, JUDGE_QA.md, CATALYST_MAP.md, RUNBOOK.md, MIGRATION.md}
└── legacy/                               (not in spec; holding area per this migration's "never delete, prefer /legacy" rule)
```

---

## 2. Frontend migration map (`src/` → `client/app/src/`)

### 2.1 KEEP + MOVE (direct relocation, import paths updated, no logic change)

| Current | New | Notes |
|---|---|---|
| `src/main.jsx` | `client/app/src/main.tsx` | Renamed `.jsx`→`.tsx` shell; TS conversion is Session 16+ work, not this pass — file content unchanged except extension, per "prepare, don't implement". |
| `src/App.jsx` | `client/app/src/app/App.jsx` | Kept as `.jsx` for now (full TS port is implementation work). |
| `src/app/AppRouter.jsx`, `ProtectedRoute.jsx`, `RoleGuard.jsx` | `client/app/src/app/` | Router directory preserved as-is. |
| `src/layouts/*` | `client/app/src/app/shell/` | `RootLayout`, `ModuleLayout`, `CaseWorkspaceLayout`, `AuthLayout` become the seed of the spec's `app/shell/` (AppShell/LeftRail equivalents). No rename of internals — reorganization only. |
| `src/components/layout/*` | `client/app/src/app/shell/` | `TopNavBar`, `ModuleSidebar`, `OperatorMiniProfile` join the shell folder alongside layouts — closest existing analogues to AppShell/LeftRail/RoleBadge. |
| `src/components/common/*` | `client/app/src/design/primitives/` | Seeds the spec's `design/primitives/`. All 17 files + `index.js` moved verbatim. |
| `src/context/*`, `src/hooks/*` | `client/app/src/app/` (`context/`, `hooks/`) | Preserved as-is; small, clean, reusable. |
| `src/config/*` | `client/app/src/app/config/` | Preserved as-is; `navigation.js` will need a content rewrite when routes are renamed in implementation, not this pass. |
| `src/services/api/*` | `client/app/src/api/` | Seeds `api/client.ts`+`api/hooks/`. `axiosClient.js` is the future `client.ts`; per-domain service files kept alongside pending remap to feature folders. |
| `src/utils/apiFallback.js`, `classNames.js`, `formatters.js` | `client/app/src/app/utils/` | Preserved as-is — mock-fallback pattern is genuinely reusable. |
| `src/mocks/*` | `client/app/src/app/mocks/` | Preserved as dev fixtures. |
| `src/styles/index.css` | `client/app/src/design/index.css` | Preserved; extracting Tailwind tokens into a literal `design/tokens.css` (CSS custom properties) is flagged as remaining work (§5), not done in this pass to avoid inventing values. |
| `src/components/dashboard/CrimeTrendChart.jsx` | `client/app/src/components/charts/CrimeTrendChart.jsx` | Direct mapping to target `components/charts/`. |
| `src/components/investigation/NetworkGraph.jsx` | `client/app/src/components/graph/NetworkGraph.jsx` | Direct mapping to target `components/graph/`. |
| `src/components/geospatial/MapPanel.jsx` | `client/app/src/components/map/MapPanel.jsx` | Direct mapping to target `components/map/`. |
| `src/components/investigation/TimelineNode.jsx` | `client/app/src/components/timeline/TimelineNode.jsx` | Direct mapping to target `components/timeline/`. |
| `tailwind.config.js`, `postcss.config.js`, `vite.config.js`, `eslint.config.js`, `index.html`, `public/` | repo root (unchanged location) | Build tooling stays at the client build root; `vite.config.js` alias/proxy paths updated to point at new `client/app/src` if the build root becomes `client/`. See §6. |
| `tests/e2e/*`, `playwright.config.ts` | `client/tests/e2e/` (or repo-root `tests/e2e/`, TBD in §5) | Preserved; selectors will need route updates when IA changes — not this pass. |

### 2.2 Feature-folder seeds (existing pages/components regrouped under `features/{name}/`, still `.jsx`, still calling existing services)

| Target feature | Seeded from |
|---|---|
| `features/command-center/` | `src/pages/dashboard/DashboardPage.jsx` + `src/components/dashboard/{ActivityLogFeed,CommandActionsPanel,GeospatialHeatmapPreview}.jsx` |
| `features/geo/` | `src/pages/geospatial/GeospatialPage.jsx` + `src/components/geospatial/{PriorityHotspotsList,SectorIntelCard}.jsx` |
| `features/case/` | `src/pages/investigation/{InvestigationOverviewPage,CaseBoardPage,CaseSuspectsPage,CaseEvidencePage,CaseTimelinePage,CaseNetworkPage,CaseReportsPage,EvidenceLockerPage,WatchlistPage,FirIntelligencePage,InvestigationArchivePage,InterviewTranscriptPage,DeviceForensicsPage}.jsx` + `src/components/investigation/{CaseFolderCard,CaseWorkspaceSidebar,CorkboardCanvas,EvidenceCard,SuspectDossierCard}.jsx` |
| `features/person/` | `src/pages/investigation/SuspectProfilesPage.jsx` (list view; a dedicated `/person/:id` detail page does not exist yet — flagged as a gap in §5, not invented here) |
| `features/network/` | (no dedicated top-level page exists today; `CaseNetworkPage.jsx` and the Analytics "pattern correlation" view are the closest source material — left in `features/case/` and `legacy/client-extra` respectively; a genuine `features/network/` top-level feature is greenfield, flagged in §5) |
| `features/intelligence/` | `src/pages/intelligence/AIWorkbenchPage.jsx` + `src/components/intelligence/{ActionableDirectiveCard,GeneratedLeadCard,QueryWorkspace}.jsx` |
| `features/predictions/` | No current page maps directly; closest source material is `src/pages/analytics/AnalyticsOverviewPage.jsx` + `src/components/analytics/RiskIndexMap.jsx`, moved to `legacy/client-extra` per §2.3 since Analytics itself isn't in the frozen IA — `features/predictions/` starts empty, flagged in §5. |
| `features/quality/` | No current page or component exists. Starts empty, flagged in §5. |

**Important:** moving a page into a `features/*` folder is a **file relocation only**. No route wiring redesign, no rewrite, no visual change. `AppRouter.jsx` continues to reference the same components at their new import paths, and the *shape* of the route tree (which paths exist, nesting) is unchanged for every route that survived migration — renaming `/investigation` routes to `/case`, adding `/network` and `/quality` top-level routes, etc. is implementation work for Sessions 17–20 of §33, not this migration.

**One necessary exception:** removing the Analytics/Operations/Administration routes from `AppRouter.jsx` (§2.3) is not a redesign of the surviving IA — it is the direct, mechanical consequence of archiving those pages' source files. Leaving `<Route>` elements pointing at lazy imports of files that no longer exist in the live tree would have produced a broken build, not a "structure only" migration. These routes were removed, not redesigned or replaced.

### 2.3 ARCHIVE → `legacy/client-extra/`

Per the confirmed decision, everything with no mapping in the frozen §30 IA:

| Moved as-is | Reason |
|---|---|
| `src/pages/operations/*`, `src/components/operations/*`, `src/services/api/operationsService.js`, `src/mocks/operations.js` | "Operations" module not in target §30 IA or §20 roles. |
| `src/pages/administration/*`, `src/components/administration/*`, `src/services/api/administrationService.js`, `src/mocks/administration.js` | "Administration" module/role not in target spec. |
| `src/pages/analytics/*`, `src/components/analytics/*`, `src/services/api/analyticsService.js`, `src/mocks/analytics.js` | No 1:1 target; overlaps `overview`/`cases`/`quality` but isn't itself in §30. |
| `src/pages/auth/LoginPage.jsx`, `src/components/auth/LoginCard.jsx`, `src/services/api/authService.js`, `src/mocks/operator.js` | **Exception — see below.** Auth is required infrastructure (§20 Policy engine / Catalyst Authentication), not discretionary. It is moved to `client/app/src/features/auth/` (kept live), not archived, since every other feature depends on it and the spec assumes Catalyst Authentication replaces this wholesale in Session 3. Kept live as the pre-Catalyst-Auth placeholder. |

### 2.4 Root-level loose scripts → `legacy/scripts/client/`

All 14 confirmed non-application scripts, moved verbatim, none deleted: `fix_models.py`, `rewrite_models.py`, `replace_ksp.py`, `search_generic.py`, `get_cases.py`, `check_api.py`, `check_all_apis.py`, `test_investigation.py`, `update_prompts.py`, `test-all-pages.js`, `scratch-test.js`, `qa-pass.cjs`, `screenshot.cjs`, `screenshot_analytics.cjs`, `screenshot_investigation.cjs`.

**Flagged, not acted on:** `get_cases.py`, `check_api.py`, `check_all_apis.py`, `qa-pass.cjs` contain a hardcoded plaintext operator credential (`OP-7729` / `lumen2024`). Recommend rotating this credential once real authentication (Catalyst Auth, §20) replaces the current mock login. Not rotated in this pass — no credential-issuing system exists to rotate it against yet.

Root demo screenshots (`*.png` — 12 files) → `legacy/demo-screenshots/`. Not part of the app; QA/demo evidence only.

---

## 3. Backend migration map (`backend/` → `api/`)

### 3.1 KEEP + MOVE (direct relocation, real logic preserved)

| Current | New | Notes |
|---|---|---|
| `backend/app/main.py` | `api/main.py` | Preserved; will need router-prefix (`/api`→`/api/v1`) and lifespan (`create_all()`+Neo4j init) updates in *implementation*, not this pass. |
| `backend/app/core/config.py` | `api/lumen/config.py` | Direct move. |
| `backend/app/db/session.py` | `api/lumen/db/session.py` | Direct move. |
| `backend/app/db/models.py` | `api/lumen/db/models/legacy_models.py` | Kept whole (not split) — splitting the 703-line file into the canonical per-entity modules per §3.5/§3.6 is Session 2 implementation work. Renamed `legacy_models.py` to make clear it is pre-migration and mixes the rejected ~40-table "datathon prototype" schema (ADR-002) with the ~25 tables that already match the canonical KSP ERD — reconciling the two is explicitly out of scope for a structure-only pass. |
| `backend/app/db/seed.py`, `db/seeds/karnataka/*` | `api/lumen/jobs/seed.py`, `api/lumen/jobs/seeds/karnataka/*` | Direct move — this is real, working Karnataka data generation, seeds `jobs/` per target layout. |
| `backend/app/repositories/base.py`, `sqlalchemy_repository.py`, `domain_repositories.py` | `api/lumen/db/repositories/` | Direct move. `operator_repository.py` (dead code — imports nonexistent `app.data.operators`) → `legacy/backend/dead_code/` instead, see §3.3. |
| `backend/app/services/*.py` (command_center, crime_number_service, executive_dashboard, geospatial_service, intelligence_profile, officer_workbench, workflow_service) | `api/lumen/services/` | Direct move — real, partially-working service logic preserved as-is. |
| `backend/app/services/repositories/module_service.py` | `api/lumen/services/module_service.py` | Moved as-is. **Flagged, not acted on:** this 793-line "god service" is the single biggest decomposition target for Session-by-session implementation (into `services/`, `intelligence/`, `governance/`, `graph/` per spec) — decomposing it is business-logic work, out of scope here. |
| `backend/app/services/graph_service.py` | `api/lumen/graph/legacy_neo4j_service.py` | Per confirmed decision — live Neo4j code preserved for reference, out of the path new `graph/backend.py` will use. |
| `backend/app/db/graph.py` (confirmed dead code — unused parallel Neo4j wrapper) | `legacy/backend/dead_code/db_graph.py` | Never imported by the running app; preserved, not deleted, per the "never delete reusable code" rule. |
| `backend/app/ai/*` (interfaces, providers, services, utils, prompts) | `api/lumen/ai/` | Direct move — real, working Gemini integration preserved. Prompts move to `api/lumen/ai/prompts/` matching target layout (target expects `.md` prompt files; existing `.py` prompt-builder modules are kept as-is, `.md` conversion is Session 14 implementation work, flagged in §5). |
| `backend/app/dependencies/auth.py`, `core/security.py`, `core/hashing.py`, `app/services/auth_service.py` | `api/lumen/identity/` | Consolidated into the target's `identity/` module location (§6 entity), file contents unchanged, just relocated together. |
| `backend/app/models/operator.py`, `app/schemas/auth.py` | `api/lumen/contracts/` | These are the only two real Pydantic "contract" files in the current backend — moved into `contracts/` as the seed of that module. Everything else in the target `contracts/` (EntityContract, InsightContract, etc.) is greenfield, flagged in §5. |
| `backend/app/api/routers/*.py` | `api/lumen/api/routers/` | Direct move, all 9 routers preserved as-is (auth, dashboard, analytics, geospatial, investigation, intelligence, operations, administration, health). Remapping/renaming to the target's `/api/v1` endpoint list (§29.1) is Session-by-session implementation work, not this pass. |
| `backend/app/core/exceptions/*`, `core/logging.py`, `core/middleware.py`, `core/versioning.py` | `api/lumen/observability/` + `api/lumen/api/` (split: exceptions→`api/`, logging/middleware→`observability/`) | Relocated to the nearest matching target module; no content changes. |
| `backend/alembic/`, `alembic.ini` | `api/alembic/`, `api/alembic.ini` | Direct move. **Flagged, not acted on:** Alembic is not currently the source of truth for schema (most tables are created via `Base.metadata.create_all()` at boot) — reconciling this dual-sourcing is Session 2 implementation work. |
| `backend/tests/*` | `api/tests/` | Direct move — all 18 test files preserved, real RLS/RBAC/circuit-breaker coverage is genuine value. |
| `backend/requirements.txt` | `api/requirements.txt` | Moved; dependency reconciliation in §6. |
| `backend/Dockerfile`, `backend/start.sh` | `api/Dockerfile`, `api/start.sh` | Moved as-is; `app-config.json` (Catalyst AppSail requirement, §27) does not exist yet — created empty/placeholder in §4. |
| `backend/README.md` | `api/README.md` | Moved as-is. |

### 3.2 Genuinely reusable dev tools → `api/scripts/` (not deleted, not left loose at repo root)

| Current | New | Reason |
|---|---|---|
| `backend/scripts/explain_analyze.py` | `api/scripts/explain_analyze.py` | Real perf-tuning tool, confirmed still relevant against Postgres. |
| `backend/scripts/measure_queries.py` | `api/scripts/measure_queries.py` | Real N+1/latency profiler, confirmed still relevant. |
| `backend/do_seed.py` | `legacy/scripts/backend/do_seed.py` | Trivial wrapper around `seed_database()`; per user's confirmed "move all to /legacy" decision, archived rather than folded into `jobs/seed.py` (folding = code change, out of scope for a structure-only pass). |
| `backend/fresh_seed.py` | `legacy/scripts/backend/fresh_seed.py` | Same reasoning — useful "nuke and reseed" pattern, archived verbatim rather than merged. |

### 3.3 ARCHIVE → `legacy/scripts/backend/` and `legacy/backend/dead_code/`

Per the confirmed "move all to /legacy, delete none" decision, **all** of the following move verbatim, nothing deleted:

**One-off audit/check/fix/generator scripts (confirmed not imported anywhere, several already broken on this machine):**
`audit.py`, `audit_db.py`, `audit_endpoints.py`, `audit_endpoints2.py`, `audit_endpoints3.py`, `audit_hotspots.py`, `audit_repos.py`, `build_phase4.py`, `build_phase5.py`, `check.py`, `check2.py`, `check_neo4j.py`, `check_types.py`, `create_prompts.py`, `db_check.py`, `fix_all.py`, `fix_fir_generator.py`, `fix_hotspot.py`, `fix_migration.py`, `fix_module_service.py`, `fix_operator.py`, `query.py`, `rewrite_seed.py`, `rewrite_seed_2.py`, `schema_dump.py`, `update_seed.py` → `legacy/scripts/backend/`

**Migration-history scripts (job complete, kept for audit trail):**
`migrate_sqlite_to_postgres.py`, `verify_migration.py` → `legacy/scripts/backend/migration-history/`

**Dead code (confirmed unreferenced by the running app):**
`backend/app/repositories/operator_repository.py` (imports nonexistent `app.data.operators`), `backend/app/services/persistence_service.py` (confirmed unused, superseded by `domain_repositories.py`+`ModuleService`), `backend/app/db/graph.py` (duplicate, unused Neo4j wrapper), `backend/app/core/versioning.py` (defines `versioned_router()`, never called by any router) → `legacy/backend/dead_code/`

**Superseded one-off generator in `backend/scripts/`:**
`backend/scripts/build_intelligence.py`, `backend/scripts/generate_karnataka_seeds.py` → `legacy/scripts/backend/`

**`backend/scripts/sync_neo4j.py`** → `legacy/backend/neo4j/sync_neo4j.py` (grouped with the other live Neo4j code per the graph-backend decision, §0.2)

**Security note, not acted on:** `schema_dump.py` (moving to `legacy/scripts/backend/`) contains a hardcoded plaintext Postgres password in source. Per the confirmed decision it is preserved verbatim (not scrubbed) since it is moving to a non-executed archive location, but **this credential should be rotated** regardless of migration — flagged for the user/team, not fixed here since rotating a live credential is an operational action outside a structural migration's mandate.

---

## 4. Structural skeleton created (empty placeholders per §28 — no logic)

The following target-spec paths do not exist in the current repo in any form and are **not** seeded from legacy code. Per the mission rules, these are created as **empty placeholder modules only** — no invented business logic, no stub implementations beyond what's needed for the package to exist and imports to resolve:

**`api/lumen/`:**
`contracts/__init__.py` (plus `contracts/README.md` noting EntityContract/InsightContract/GraphContract/etc. are Session 2/8 work), `semantics/{__init__.py,entities.py,render.py}`, `db/datastore.py`, `quality/{__init__.py,rules.py,engine.py,scoring.py}`, `governance/{__init__.py,classification.py,masking.py,retention.py}`, `intelligence/{__init__.py,engine.py,risk.py,hotspots.py,anomaly.py,linkage.py,outcome.py,explain.py,counterfactual.py,confidence.py,lifecycle.py,guards.py,features.py}`, `graph/{__init__.py,backend.py,projection.py,queries.py,metrics.py}`, `kb/{__init__.py,ingest.py,retrieve.py}`, `ai/{orchestrator.py,intent.py,retriever.py,toolsel.py,envelope.py,provider.py}`, `ai/eval/{__init__.py,runner.py,rubric.py}`, `bus/{__init__.py,signals.py,events.py,catalog.py}`, `policy/{__init__.py,engine.py,roles.py}`, `registry/{__init__.py,models.py,prompts.py,services.py}`, `resilience/{__init__.py,breaker.py,timeouts.py,degradation.py}`, `observability/health.py`, `observability/metrics.py`, `api/deps.py`, `jobs/{precompute.py,resolve.py,quality.py,kb_ingest.py}`

**Repo root:** `functions/{on_case_registered,on_anomaly_detected,on_graph_projected,on_quality_finding}/` (each an empty dir with a `README.md` placeholder), `data/{schema.sql,seeds/,eval/golden.yaml}` (schema.sql seeded from §3.5 DDL as literal spec text — this is the *canonical schema definition*, i.e. reference data, not business logic, and copying it verbatim is not an invention), `catalyst.json` (skeleton per §27 with `client`/`functions` source declarations), `api/app-config.json` (skeleton per §27 startup-command example), `client/client-package.json` placeholder pointing at the relocated `app/src`.

Every placeholder file/module contains only a docstring/comment citing the spec section it corresponds to (e.g. `# See LUMEN_MASTER_SPEC_V3 §14 — Knowledge graph. Not yet implemented.`) — never invented logic, per mission rules. 64 such placeholder files were created across `contracts/`, `semantics/`, `db/datastore.py`, `quality/`, `governance/`, `intelligence/` (13 files), `graph/` (5 files), `kb/`, `ai/` (orchestrator/intent/retriever/toolsel/envelope/provider + `eval/`), `bus/`, `policy/`, `registry/`, `resilience/`, `observability/` (2 files), `api/deps.py`, and `jobs/` (4 files).

**Mechanical fixes bundled with the move, not new features:** `api/start.sh`'s uvicorn invocation was updated from the stale `app.main:app --port 8000` (referencing the now-nonexistent `backend/app` package and hardcoding a port) to `main:app --port "${X_ZOHO_CATALYST_LISTEN_PORT:-9000}"`, matching §27's port-binding contract exactly — this is a path/port correction required by the move itself, not new deployment logic. Similarly, root-level `start-backend.ps1` (a dev convenience script, not part of the app) had its `Set-Location backend` / `app.main:app` updated to `Set-Location api` / `main:app`. `api/requirements.txt` gained one line, `tenacity` — confirmed via grep to be actually imported by `ai/providers/gemini_provider.py` but never declared; a pre-existing bug exposed by re-installing dependencies from scratch during validation, fixed as a correctness matter rather than left broken.

---

## 5. Remaining work before Session 1 implementation can proceed

This is a structural migration, not an implementation. The following are explicitly **not done** and are logged here as the punch list for implementation sessions per §33:

1. **Schema reconciliation (Session 2):** `db/models/legacy_models.py` mixes the rejected ~40-table prototype schema (ADR-002) with ~25 tables that already resemble the canonical KSP ERD (§3.5). Splitting, renaming to match canonical column/table names exactly, and retiring the rejected models is real modeling work.
2. **Alembic/`create_all()` dual-sourcing (Session 2):** schema is currently materialized partly by Alembic migrations, partly by `Base.metadata.create_all()` at app boot. Needs a single source of truth.
3. **Graph backend swap (Session 9, ADR-001):** `graph/backend.py` needs a real NetworkX in-process implementation; `sync_neo4j.py`/`legacy_neo4j_service.py` remain in `/legacy` as reference for what capability parity looks like (case network, evidence nexus).
4. **AI orchestrator decomposition (Session 14, ADR-005):** current `ai/services/ai_service.py` is a monolithic facade on Gemini; target wants `orchestrator.py/intent.py/retriever.py/toolsel.py/envelope.py` with QuickML as primary provider and Gemini as a declared dev-only fallback (§26.3 exception register). Provider default swap is a real behavior change, not filed here.
5. **`module_service.py` decomposition:** the 793-line god-service needs splitting into `services/`, `intelligence/`, `governance/`, `graph/` per module boundaries (§28 structural rule #2).
6. **API versioning (`/api` → `/api/v1`) and endpoint reshaping** to match §29.1 exactly — current routers are functionally close for `overview`/`cases`/`ai/ask` but need contract-shape changes (envelope format, `Insight` object, etc.).
7. **Frontend TypeScript conversion:** application source is 100% `.jsx`/`.js` today; target mandates TypeScript throughout `app/src`. Not done in this pass (would require type-authoring, which is implementation work, not restructuring).
8. **Frontend IA/route rewrite:** current routes (`/investigation`, `/analytics`, etc.) don't match target's flat 8-route IA (`/`, `/geo`, `/case/:id`, `/person/:id`, `/network`, `/intelligence`, `/predictions`, `/quality`). `features/network/`, `features/predictions/`, `features/quality/`, and a dedicated `/person/:id` detail page are greenfield — no existing page to seed them from beyond fragments left in `legacy/client-extra`.
9. **Design tokens:** `design/tokens.css` does not exist yet as literal CSS custom properties — current tokens live only in `tailwind.config.js`. Per the mission's explicit instruction to preserve, not redesign, the **current gold/dark "fusion-center" palette is being kept as the real design system**, not replaced with the spec's illustrative teal-accent hex values. Extracting `tailwind.config.js`'s existing values into `design/tokens.css` as CSS variables (same colors, just re-expressed) is still open — flagged, not done, since it touches build config beyond pure file moves.
10. **Contracts, quality engine, entity resolution, confidence model, intelligence lifecycle, trust framework, feature store, prediction engine, knowledge base/RAG, event bus, policy/ABAC, service registry, resilience, observability** (§7–§25) — all genuinely greenfield. Structural placeholders exist (§4); no logic.
11. **Credential rotation:** the plaintext `OP-7729`/`lumen2024` credential embedded in several archived QA scripts, and the plaintext Postgres password in `schema_dump.py`, should be rotated once real Catalyst Authentication (§20/§26.1) is in place.
12. **`catalyst.json` / `app-config.json` completion:** skeletons created (§4) but AppSail service initialization (§27) itself has not been run — no live Catalyst project is wired beyond the pre-existing `.catalystrc`.

---

## 6. Dependency changes

### 6.1 `backend/requirements.txt` → `api/requirements.txt`

No packages removed or added in this pass — dependency changes mandated by the spec (adding `networkx` for ADR-001, removing `neo4j` once the swap is implemented, adding a QuickML client once available, pinning `tenacity` which is imported but currently undeclared) are **implementation-time changes**, not structural ones, and are deferred to the relevant build session. Logged here so they aren't lost:
- **To add later:** `networkx` (ADR-001), `tenacity` (currently used but undeclared — pre-existing bug, not introduced by this migration).
- **To remove later, once Session 9 swaps the graph backend:** `neo4j==6.2.0`.
- **To reconsider later, once Session 14 wires QuickML:** `google-genai==2.13.0` moves from primary to declared dev-fallback per §26.3; no package removal until QuickML integration exists.

### 6.2 `package.json`

No dependency changes in this pass. Noted for future sessions: no chart/map/animation library exists today (hand-rolled SVG for charts/graphs/maps, no Framer Motion) — §30.10 mandates Framer Motion for the three orchestrated moments; adding it is implementation work for Session 16, not filed here.

### 6.3 Docker / compose

`docker-compose.yml` still declares `neo4j` and `GEMINI_API_KEY`/`ACTIVE_AI_PROVIDER=gemini` as of this migration — left as-is since changing the live service topology is an implementation decision (Session 9/14), not a structural one. Paths within (`./backend`, `./frontend/Dockerfile`) will need updating once `backend/`→`api/` and the frontend build root move — tracked as a follow-up, not yet applied, since docker-compose is not part of the Catalyst deployment path (§27 uses AppSail, not compose) and its role going forward is unclear until Session 3 stands up the Catalyst skeleton.

---

## 7. Validation performed

- [x] **Frontend builds** — `cd client && npx vite build` succeeds: 1636 modules transformed, zero errors, valid `dist/` output (removed after validation, not committed).
- [x] **Backend imports resolve and the app constructs** — validated twice: (1) static/textual resolution of every `from lumen....` import across all 44 changed files (zero remaining references to the old `app.` package); (2) a from-scratch virtualenv (`python -m venv`, `pip install -r api/requirements.txt`) followed by `from main import app` inside `api/` — succeeds, reports `LUMEN Crime Intelligence Platform` with all 10 route groups (9 routers + health) registered.
- [x] **No broken relative imports across moved files** — every in-scope (non-archived) import fixed; the only remaining unresolved imports are the deliberately-archived Analytics/Operations/Administration routes, which were then removed from `AppRouter.jsx` and `navigation.js` (see below) rather than left dangling.
- [x] **No duplicate architecture** — the one confirmed duplicate (a dead, unused second Neo4j wrapper at `backend/app/db/graph.py` alongside the live `backend/app/services/graph_service.py`) was resolved: the live one moved to `api/lumen/graph/legacy_neo4j_service.py`, the dead one to `legacy/backend/dead_code/db_graph.py`.
- [x] `git mv` used throughout for every file with git history (307 tracked files, all moved via `git mv`, confirmed as clean renames in `git status`, zero content loss — see file-count audit in this section).

**Follow-on cleanup performed as a direct, mechanical consequence of the confirmed archival decision (not a new scope decision):** once Analytics/Operations/Administration pages moved to `legacy/client-extra/`, their lazy-import statements, `<Route>` blocks, `RoleGuard`/`ROLES` usage, and `sidebarConfig`/`primaryModules` entries were removed from `client/app/src/app/AppRouter.jsx` and `client/app/src/app/config/navigation.js` so the app has no dangling references to archived modules. The three now-archived services' re-exports were likewise removed from `client/app/src/api/index.js`'s barrel file. `RoleGuard.jsx` itself was left in place (unused for now) rather than archived, since it is a small generic route-guard, not module-specific code, and real RBAC (§20) will need it again soon.

**File-count integrity check:** 307 files were tracked in git before this migration; 307 are tracked after (all renames, zero deletions from git's perspective). An additional 89 new files exist on disk (64 structural placeholders + `docs/`, `data/`, `catalyst.json`, `functions/*/README.md`, `api/app-config.json`, and this document) — all accounted for in §2-§4 above.

---

## 8. Sanitation pass (second pass — supersedes some of §1-§7)

**Trigger:** the user issued a follow-up prompt (reproduced in the session, not duplicated here) explicitly instructing deletion rather than archival of legacy code, and removal of working auth/AI/DB-boot logic ahead of the sessions that will properly rebuild them, rather than keeping it alive as "prepared but preserved." Two rounds of `AskUserQuestion` confirmed this was intentional and not a misreading: the user chose "actually delete `legacy/` and obsolete code now" and "yes — rip [auth/AI] out now, return 501 for anything auth/AI-dependent" over the more conservative defaults.

### 8.1 Deleted entirely

- **`legacy/`** (the whole directory from the first pass) — all ~48 archived one-off dev scripts, the 4 confirmed-dead code files, the live Neo4j service + sync script kept for ADR-001 reference, the archived Operations/Administration/Analytics frontend pages/components/services/mocks, and the 12 demo screenshots. Nothing recoverable except via `git log` on the commit(s) that preceded this deletion.
- **`api/lumen/db/models/legacy_models.py`** — the entire ~65-class SQLAlchemy ORM file, including the ~25 classes that already matched the canonical KSP ERD (District, Accused, ChargesheetDetails, Employee, etc.). The user explicitly chose "delete the whole file, keep nothing" over splitting out the canonical-matching subset, since Session 2 rebuilds `db/models/` properly against the spec's exact column/table names anyway (§3.5) — keeping a partial, differently-shaped version around was judged not worth the complexity of a partial split.
- **Custom JWT auth**: `api/lumen/identity/security.py`, `hashing.py`, `auth_service.py`, `dependencies.py`, plus `api/lumen/contracts/auth.py` and `contracts/operator.py` (the Pydantic models that existed only to support the deleted auth flow).
- **Live Gemini AI integration**: `api/lumen/ai/providers/{gemini_provider,mock_provider,factory}.py`, `ai/services/ai_service.py`, `ai/interfaces/ai_provider.py`, `ai/utils/json_parser.py`, and all 8 files under `ai/prompts/`. The empty placeholder files from the first pass (`orchestrator.py`, `intent.py`, `retriever.py`, `toolsel.py`, `envelope.py`, `provider.py`, `eval/*`) were left untouched — they were already docstring-only stubs for the future QuickML implementation, not part of this deletion.

### 8.2 Modified to remove the mandatory DB/AI/Neo4j boot dependency

- **`api/main.py`** — `lifespan()` rewritten to a no-op: no import of the deleted `legacy_models`, no `Base.metadata.create_all()`, no `seed_database()` call, no Neo4j driver init/close. The app now boots with zero external dependencies — no database connection attempt, no AI provider, no Neo4j — confirmed by running it with no `.env` file and no environment variables set at all.
- **All 8 non-health routers** (`administration`, `analytics`, `auth`, `dashboard`, `geospatial`, `intelligence`, `investigation`, `operations`) — every endpoint body replaced with `raise HTTPException(501, "Not yet implemented — pending Session N ...")`, naming the relevant future session (2 for DB/schema, 3 for Catalyst Authentication, 14 for the QuickML AI orchestrator). Route paths, HTTP methods, and function signatures are unchanged — only the body and now-unneeded imports (the deleted `ModuleService`, `get_current_operator`/`require_role`, deleted contracts) were removed. `health.py` was not touched — it was already dependency-free.
- **`api/alembic/env.py`** — no longer imports the deleted models file; `target_metadata` set to `None` with a comment pointing to Session 2.
- **`api/requirements.txt`** — removed `pyjwt`, `passlib`, `bcrypt`, `tenacity`, `neo4j==6.2.0`, `google-genai==2.13.0` (all confirmed unreferenced after the deletions above). `fastapi`, `uvicorn`, `python-multipart`, `pytest`, `sqlalchemy`, `psycopg[binary]`, `alembic`, `python-dotenv` remain, since `lumen/db/session.py` still defines an (unused-at-boot) SQLAlchemy engine for future use.
- **Test files** (`api/tests/*.py`) — not deleted, not rewritten to pass. Each file that imports a now-deleted module got a top-of-file comment naming what it tests and which future session will need to rewrite it. `pytest --collect-only` shows 33 of the ~45 original tests still collect; 12 fail collection with `ModuleNotFoundError` against modules that were deliberately deleted (`lumen.identity.security`, `lumen.db.models.legacy_models`) — an accepted, documented outcome, not an oversight.

### 8.3 Left on disk, intentionally unfixed and unimported ("dead but present")

Once every router was stubbed at the router level (returning 501 before ever calling into business logic), the following became unreachable from the running app but were **not** deleted, since the user's deletion instructions were scoped to legacy/, the DB models file, auth, and AI — not the service/repository layer built on top of them:

- `api/lumen/services/module_service.py` (~800 lines) and everything it alone pulled in: `command_center.py`, `officer_workbench.py`, `geospatial_service.py`, `executive_dashboard.py`, `workflow_service.py`, `intelligence_profile.py`, `crime_number_service.py`
- `api/lumen/db/repositories/{domain_repositories,sqlalchemy_repository,base}.py`
- `api/lumen/jobs/seed.py` and `api/lumen/jobs/seeds/karnataka/*` (5 files) — no longer invoked since `main.py` stopped seeding at boot
- `api/lumen/graph/legacy_neo4j_service.py` — the live Neo4j code kept from the first pass's ADR-001 decision; nothing in this second pass forced changes to it (only `main.py` and `intelligence.py` used to import it, and neither does anymore), so it was left exactly as-is rather than re-litigating the ADR-001 decision inside this sanitation pass.

These files will need either deletion or a real rewrite when Session 2 (schema/repositories) and Session 14 (AI orchestrator) actually happen — flagged here rather than acted on now, since rewriting them is implementation work, not sanitation.

### 8.4 Explicitly not touched

- `client/` (frontend) — this pass was backend-only by design. The frontend's existing `withMockFallback` pattern (`client/app/src/app/utils/apiFallback.js`) already catches any non-2xx response — including the new 501s — and falls back to fixture data in dev mode, so the UI continues to render normally against mocks without any frontend change being necessary. This was verified, not assumed: axios rejects on any non-2xx status by default, so the 501 responses trigger the existing catch-and-fallback path exactly like a network failure would.
- `api/lumen/graph/{backend,projection,queries,metrics}.py` — the empty placeholders from the first pass, confirmed zero diff.
- Any of the 64 structural placeholder files created in the first pass (contracts/, semantics/, quality/, governance/, intelligence/, kb/, bus/, policy/, registry/, resilience/, observability/, jobs/precompute.py etc.) — none of these existed as real code before, so there was nothing to delete.

### 8.5 Route-by-route status after this pass

All ~45 endpoints across the 8 non-health routers now return `501 Not Implemented` with a message naming the session that will implement them. `GET /health` is the only endpoint that still functions normally (200 OK, no dependencies). No endpoint could be kept working per the "boots with zero external dependencies" requirement, since every prior endpoint depended on either the deleted DB layer, the deleted auth, or the deleted AI service — including the one borderline case (`geospatial.py`'s parameter-update endpoint, which didn't touch the DB but did require an authenticated operator).

### 8.6 Validation performed for this pass

- `python -m compileall` across `main.py`, `lumen/`, `tests/`, `scripts/`, `alembic/` — zero syntax errors.
- Fresh virtualenv, `pip install -r requirements.txt` (the trimmed version) — installs cleanly.
- `from main import app` succeeds with **no `.env` file and no environment variables set** — this is the key claim of the whole pass (backend requires nothing external to boot) and was independently re-verified after the implementing agent's own report, not just taken on faith: a second from-scratch venv + `TestClient` run confirmed `GET /health` → 200, `POST /api/auth/login` → 501, `GET /api/dashboard/summary` → 501, each with the expected session-referencing detail message.
- `app.openapi()` / `app.routes` — 10 route entries at the FastAPI-object level (matching the pre-cleanup count), 45 concrete HTTP endpoints once sub-routes are counted (matching exactly, since only bodies changed, not route registration).
- `pytest --collect-only` — 33/45 tests collect; 12 fail collection against modules confirmed to be deliberately deleted, each with an explanatory header comment.
- Frontend rebuild (`cd client && npx vite build`) re-run after this pass to confirm the backend-only changes didn't regress it — still 1636 modules, zero errors, since nothing under `client/` was touched.

### 8.7 What remains before Session 1-14 implementation, updated

Everything listed in §5 above still applies. In addition, as a direct consequence of this pass:

- Sessions 2 (schema/repositories), 3 (Catalyst Authentication), and 14 (QuickML AI orchestrator) now have a genuinely clean slate to build against — no legacy DB models, no legacy auth, no legacy AI code left half-wired into routers to work around.
- The dead-but-present service/repository files listed in §8.3 will need to be either deleted or substantially rewritten once Session 2 defines the real `db/models/` and `db/repositories/` — they cannot be reused as-is since they're built against the deleted ORM.
- `api/tests/` needs a real rewrite pass once Sessions 2/3/14 land; in the meantime 12 of 45 tests don't even collect, which is expected and documented, not a regression to silently fix.
