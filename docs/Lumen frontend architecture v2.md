# LUMEN Frontend Architecture — v2 (post-review)
### The Intelligence Operating System · Implementation Blueprint
**Source of truth:** `docs/LUMEN_MASTER_SPEC_V3.md`. Every screen, component and interaction traces to a section of that document. Where the spec does not define something, this document says *Cannot determine from specification* and the feature is excluded — it is never invented.

**Supersedes v1.** Changes from review: a case browse surface (`/cases`) added — v1's worst gap; `PeekPanel` and `GraphInspector` unified into one `InspectorPanel`; `FilterBar` added as a shared component; URL-as-state made a rule; §29.3 error codes mapped to renderings; design system expanded (type, spacing, elevation, density, a11y, responsive); graph/map table fallbacks defined; anomalies given a surface; the briefing made reachable; roadmap compressed to **six sessions**.

**Audience:** senior frontend engineers, no further clarification available. If this document and the master spec together do not determine an answer, the answer is "Cannot determine from specification" — raise it, do not resolve it silently (master spec §37).

---

## A. Product vision

LUMEN is not a dashboard suite. It is the software an intelligence analyst lives inside for a full shift: a connected chain of workspaces where every entity on screen is a door to the next one. The homepage is visited once per session; after that the analyst is always *somewhere specific* — inside a case, a person, a district, a question.

**The one-sentence test for every screen:** does this move an investigation forward? A screen that only displays numbers fails. A screen that lets the analyst open, connect, question or decide passes.

**Every screen answers seven questions** (spec P1–P4, §8, §9, §11):
1. What happened? 2. Why? 3. How do we know (evidence)? 4. How confident is the system (decomposed)? 5. What are the limitations? 6. What produced this (lineage)? 7. What should the officer do next?

The component library makes these answers *structural*: an `InsightCard` cannot render without limitations; a confidence value cannot appear without its breakdown; an evidence chip is always a link.

---

## B. UX philosophy

**Drill-in, never sidebar-hop** (spec §30.1). The rail is orientation; entity references are navigation. Every CrimeNo, person, officer, station, district, charge and insight anywhere in the product links into its workspace. A judge should click continuously for two minutes without touching the rail.

**Density over decoration.** Reference class: Palantir Gotham, i2 Analyst Notebook, Bloomberg Terminal, Elastic Security. What they get right is not styling — *context never leaves the screen*. LUMEN therefore prefers the docked `InspectorPanel` and inline expansion over modals and page swaps.

**Forbidden:** glassmorphism, gradients, glows, neon, floating cards, decorative charts, fake terminals, startup hero sections, oversized stat cards, decorative loaders. Motion is functional (spec §30.10): 180–240 ms easeOut; orchestration at exactly three moments (map load, map zoom, graph node expansion); `prefers-reduced-motion` respected globally.

**Trust is rendered, not claimed** (spec §11). Trust statements are literal component-default strings — the co-accusal caveat on every network result, the identity caveat on every resolved person, the training-window caveat on every forecast. Defaults, not per-page content, so they cannot be forgotten.

**Scope denial is a feature, not an error.** `SCOPE_DENIED` renders as a calm governance notice ("Outside your jurisdiction scope — access is logged"), visually distinct from failures. Governance made visible is a selling point (spec §20).

---

## C. Information architecture

```
/                     Mission Briefing (public landing)            [C.1]
/login                Authentication (Catalyst Auth)               [C.2]
/briefing             Intelligence Briefing (post-login;
                      reachable any time via the wordmark)         [C.3]
──────────────────────────────────────────────────────────────────
/command              Command Center                               [E.1]
/geo                  Geo Intelligence                             [E.2]
/cases                Case Registry (browse/search)     ← NEW      [E.3]
/case/:id             Case Workspace                    ★ hero     [E.4]
/person/:id           Person Dossier                               [E.5]
/network              Criminal Network                             [E.6]
/ask                  Intelligence Console                         [E.7]
/forecasts            Forecasts                                    [E.8]
/anomalies            Anomaly Register                  ← NEW      [E.8]
/quality              Data Quality                                 [E.9]
/system               Health · Metrics · Registry · Eval           [E.10]
/admin                Audit · Roles                                [E.10]
──────────────────────────────────────────────────────────────────
Global: ⌘K command palette · InspectorPanel · notification tray
```

**Rail order** mirrors investigation flow: Command → Geo → Cases → Ask → Forecasts → Quality; System/Admin collapsed at the bottom. `/case/:id` and `/person/:id` never appear in the rail — they are drilled into, which teaches the interaction model. `/anomalies` is reached from the Command stat and the tray, not the rail.

**URL is state.** Every filter, map viewport, time range, selected tab and selected entity serializes to query params. Rules: (1) browser back always works mid-drill; (2) any view can be shared as a link — this is also how the demo recovers from a wrong click; (3) refresh reproduces the view. No filter state lives only in memory.

### C.1 Mission Briefing (public landing, `/`)

Government software introducing itself. One column, generous measure, fade-in only. In order:
1. **Masthead** — LUMEN wordmark · "Crime Intelligence Platform · Karnataka State Police" · **Enter Command Center** (→ `/login`) · **Download Demo Guide** (Stratus PDF; omitted — not stubbed — if spec §26.1 row 16 is not built).
2. **The problem** — static SVG flow: Fragmented records → Manual correlation → Disconnected evidence → Slow intelligence ⇒ Unified investigations · Entity resolution · Knowledge graph · Explainable AI · Officer decision support.
3. **How it works** — FIR → Extract → Resolve → Graph → Reason → Evidence → Recommendation → **Officer review** (last node visually distinct — P3 on the landing page).
4. **Demo roadmap** — the §34 path, numbered, 5–7 min, so a judge can self-drive.
5. **Architecture strip** — Frontend → FastAPI → AI layer → Knowledge graph → Data Store, each labelled with its Catalyst service.
6. **Dataset note** — seeded, deterministic, per spec §32. Stated plainly.
7. **Footer** — classification note; "AI-assisted, officer-decided."

### C.2 Authentication (`/login`)

Catalyst Authentication (spec §26.1 row 17). One panel: crest, email, password, sign in; a scope note ("access is scoped to your role and jurisdiction"). §29.3 errors render inline. Nothing else.

### C.3 Intelligence Briefing (`/briefing`)

Shift-start page, shown once per login; the shell wordmark returns here at any time. One `GET /overview` + `GET /insights?lifecycle_state=verified&limit=6`:

```
Good morning, {rank} {name}                {date} · scope: {district/state}
{n} high-risk districts  {n} active anomalies  {n} priority cases
{n} AI recommendations awaiting review     system: L0 · quality 0.87
TOP INSIGHTS SINCE LAST SESSION            (6 compact InsightCards)
                [ Begin — open Command Center ]
```

Every number is a link (anomalies → `/anomalies`, priority cases → `/cases?sort=risk`, recommendations → `/cases` filtered). For an Investigating Officer the case count is *their* scope — the "my work" entry point comes free from server-side scoping (spec §20), labelled "your assigned scope".

---

## D. Component library

Thirteen primary components; every page in §E is assembled from them. No page-specific widgets. Names are implementation names.

| # | Component | Renders / does | Used in |
|---|---|---|---|
| D1 | **`InsightCard`** | `Insight` (spec §8): headline · kind glyph · `ConfidenceMeter` · expandable `FactorBars`, counterfactuals, `EvidenceChip` row, `LimitationsNote`, `LineagePanel` · lifecycle badge · feedback (`POST /insights/{id}/feedback`) · role-gated approve (`POST /insights/{id}/approve`). Compact and full variants | Everywhere. Built first |
| D2 | **`ConfidenceMeter` / `ConfidenceBreakdown`** | §9: band-coloured meter; click opens five labelled bars, limiting component named — *"limited by identity match (0.79)"* | D1, D6, Console |
| D3 | **`EvidenceChip`** | `Evidence` (§8): typed glyph + label, always a link; RESTRICTED renders masked-lock per role (§4.2) | D1, Console, timelines |
| D4 | **`EntityCard`** | `EntityContract` (§2.1/§2.3): one per semantic entity, compact + full | Workspace entities, dossier, lists, inspector |
| D5 | **`CrimeNoDecoder`** | §31.3: segmented mono, hover labels, each segment filters (`/cases?district=…`); Q04 mismatch glyph | Case header, case rows only |
| D6 | **`IdentityBanner`** | §6.4: confidence · N linked records · "see why" (match_features) · "report incorrect match" (`POST /persons/{id}/dispute`); separated candidate (<0.85) variant | Dossier, inspector |
| D7 | **`Timeline`** | §30.4: horizontal, **gaps to scale**, district-median reference, `ProcessEvent` chips | Workspace, dossier |
| D8 | **`GraphCanvas`** | §14 payloads via Cytoscape: typed node colours, hover edge labels, click selects → `InspectorPanel`, double-click expands 1-hop (animated). **Render cap 300 nodes** — beyond it, cluster placeholders with "expand". **Table fallback** (`DataGrid` of nodes/edges) toggles for a11y and serves automatically at degradation ≥ L2 or canvas error | Board, Network, dossier ego |
| D9 | **`MapCanvas`** | §30.3 via Leaflet: choropleth, DBSCAN density, incident points, station catchment, reporting-delay layers; scrubber (re-query on release). Tile failure → cached-GeoJSON choropleth without basemap (spec §24.1) | Command hero, Geo |
| D10 | **`InspectorPanel`** | *Unifies v1's PeekPanel + GraphInspector.* Right panel, two modes: **overlay** (420 px, transient — map/list peeks) and **docked** (persistent — graph selection). Content = `EntityCard` full + contextual block (edge evidence on graph; case list on cluster). Footer: "Open full view" | Maps, lists, graphs |
| D11 | **`FilterBar`** | Declarative filter set → query params: chips for active filters, add-filter menu bound to the endpoint's params, full-text `q` slot, saved defaults per role scope. One implementation | `/cases`, `/anomalies`, insight feed, `/quality` findings |
| D12 | **`TrustBadge` / `ClassificationBadge` / `QualityBadge` / `RiskBand`** | §11 statements · §4.1 classes · §5.2 scores · risk pill | Headers, cards, rows |
| D13 | **`DegradationPill` / `SystemStatus`** | §24.2 ladder: shell pill "L0" → per-dependency detail; ≥L1 turns `--state-degraded` with "serving cached data from HH:MM" | Shell, `/system` |

**Primitives** (`design/primitives/`): `Panel`, `Stat` (always clickable), `DataGrid` (dense, sortable, **virtualised**, keyboard row navigation: ↑↓ move, Enter opens, Space peeks in `InspectorPanel`), `EmptyState` (always has copy — never a bare spinner), `ErrorState` (§29.3-mapped, below), `PipelineStages` (the twelve §16.2 stages), `AuditRow`.

**`ErrorState` mapping (§29.3):**

| Code | Rendering |
|---|---|
| `SCOPE_DENIED` | Calm governance notice, lock glyph, "access is logged". Not styled as failure |
| `NOT_FOUND` | "No record for this reference" + search affordance |
| `RATE_LIMITED` | Retry-after countdown on the affected action only |
| `DEPENDENCY_UNAVAILABLE` / `DEGRADED_RESULT` | Content renders with the staleness banner; pill reflects level |
| `VALIDATION_FAILED` | Inline at the offending field |
| `INTERNAL` | Panel-scoped error with trace_id shown; page never white-screens — errors are panel-scoped by an error boundary per panel |

**Shell:** left rail (icons+labels, collapsible) · top bar: ⌘K global search (resolves CrimeNo → `/case`, names → person/officer results, districts/stations → `/geo`; backed by `GET /cases?q=` + semantic search), scope indicator ("District SP · Mysuru"), `DegradationPill`, role badge, notification tray (AnomalyDetected → `/anomalies`), wordmark → `/briefing`.

**Explicitly excluded (Cannot determine from specification):** comparison views, bulk actions, context menus, saved searches, persistent AI chat history (the spec audits AI queries; it defines no user-facing history store — the Console history rail is session-local), officer live positions, patrol animation, CCTV. Do not add them.

---

## E. Page specifications

Endpoints are spec §29.1; all responses use the §29 envelope. The API client renders the staleness banner automatically when `meta.degradation_level ≠ L0`, and raises typed errors for `ErrorState`.

### E.1 Command Center — `/command`

Purpose: statewide situational awareness; every element is an entry point (spec §30.2).

Layout: left `Stat` column (period cases · active anomalies · high-band districts · network-central persons) · centre Karnataka `MapCanvas` choropleth (600 ms ascending-risk fade on load — sanctioned moment #1) · right live feed of compact `InsightCard`s · bottom 12-month sparklines for top-5 crime heads.

Backend: `GET /overview` · `GET /geo/districts` · `GET /insights?limit=10` · `GET /anomalies`.
Interactions: stats → `/anomalies`, `/cases?sort=risk`, `/network` seeded, `/forecasts`; district click → `/geo?district=…`; insight expands in place, subject chip navigates.

### E.2 Geo Intelligence — `/geo`

Purpose: four real query levels — State → District → Station → Cluster (spec §30.3). The map is the navigation.

Full-bleed `MapCanvas`; floating layer control (incident points · density · risk choropleth · station catchment · **reporting-delay** — spec §3.2 fact 5, the layer no other team has); bottom scrubber; selection opens `InspectorPanel` (overlay).

Backend: `GET /geo/districts` → `/geo/units/{district_id}` → `/geo/hotspots?…` → `/geo/delay`.
Interactions: each zoom level is a fresh query. Cluster → inspector lists member cases (rows with `CrimeNoDecoder`); case → `/case/:id`. Viewport and layers serialize to the URL. Zoom transition = sanctioned moment #2.

### E.3 Case Registry — `/cases`  *(new; fixes v1's front-door gap)*

Purpose: the analyst's worklist and the product's text entry point. An analyst who knows "the Whitefield burglary from March" but not its number starts here.

Layout: `FilterBar` (crime head, sub-head, gravity, status, category, district, unit, date range, full-text `q` — exactly the spec §29.1 params) above a virtualised `DataGrid`: `CrimeNoDecoder` · crime type · gravity `RiskBand` · status · station/district · registered date · insight count. Default view = caller's scope ("your assigned scope" for an IO — free from spec §20 server-side scoping). Row keyboard nav; Space peeks in `InspectorPanel`; Enter opens the workspace.

Backend: `GET /cases` (returns `total`, `limit`/`offset` per spec §29.2).

### E.4 Case Workspace — `/case/:id` ★ hero

Purpose: everything about one FIR on one screen; hours of work without leaving (spec §30.4). Three persistent columns, no top-level tabs.

```
┌ header ───────────────────────────────────────────────────────────┐
│ CrimeNoDecoder · CrimeType · Gravity · Status · TrustBadge        │
│ registered {date} at {Station}, {District} · IO {Officer}         │
│ ClassificationBadge · QualityBadge ({n} findings → expands)       │
├──────────────┬───────────────────────────────┬────────────────────┤
│ ENTITIES     │ INVESTIGATION BOARD           │ INTELLIGENCE       │
│ EntityCards: │ GraphCanvas: case ⇄ resolved  │ Risk InsightCard   │
│ victims,     │ persons ⇄ arrests ⇄ officers  │ Outcome probability│
│ accused A1…, │ ⇄ linked cases; double-click  │  (InsightCard)     │
│ complainants,│ expands 1-hop (moment #3)     │ Linked cases       │
│ charges,     │ ───────────────────────────── │  (reason + shared  │
│ court,       │ TIMELINE — to scale, district │   entities)        │
│ evidence,    │ median line: incident→info→   │ Signature family   │
│ notes,       │ registered→arrest(s)→charge-  │ AI case summary    │
│ quality      │ sheet→court                   │ Recommendations    │
│ findings     │                               │ [Generate Briefing]│
└──────────────┴───────────────────────────────┴────────────────────┘
```

Backend: `GET /cases/{id}` (one aggregate call renders header + entities) · `/graph` · `/timeline` · `/insights` · `/linked` · `GET /predictions/outcome/{id}` · `GET /recommendations?subject=case:{id}` · `POST /cases/{id}/briefing` (button hidden — never stubbed — if the T2 endpoint is absent).
Interactions: every entity links onward (resolved accused → `/person/:id`; officer → `/cases?officer=…`; charge → KB section text in the inspector). Timeline event → inspector. Board selection → docked inspector with edge evidence. Role masking renders `A2 (masked)` with lock affordance below threshold (spec §4.2) — demo step 9.

### E.5 Person Dossier — `/person/:id`

Purpose: an intelligence profile of a resolved, *uncertain* identity (spec §30.5, P10). Never a CRUD person page.

Top-to-bottom: **`IdentityBanner` first, always** → three columns: case history (`EntityCard`s with decoders) · arrest history + districts of operation (mini `MapCanvas` dots) · ego `GraphCanvas` depth-1 with plain-language metrics (*"connected to 14 people across 3 districts; the only path between two otherwise separate groups"*) → associates ranked by shared cases → **candidate matches** (<0.85), visually separated, excluded from the metrics above (spec §6.4).

Backend: `GET /persons/{id}` · `/persons/{id}/network?depth=1` · `POST /persons/{id}/dispute`.

### E.6 Criminal Network — `/network`

Purpose: the ten named queries as an instrument (spec §14.4, §30.6).

Left **query rail**: Q1–Q10, each labelled with its plain-language question ("Who is the only link between these groups?"); parameter slots on selection (person pickers via ⌘K-style search, district selects). Centre `GraphCanvas` with community hulls (district labels on cross-district hulls). Right: results as **`InsightCard`s above the graph payload** — insight states the finding, graph shows it, never a bare graph; the co-accusal caveat renders by default.

Backend: `GET /network/query/{q1..q10}` · `/persons/{id}/network?depth=2` for seeding.
Q2's result card highlights the broker node in the canvas — demo step 7.

### E.7 Intelligence Console — `/ask`

Purpose: the AI Workbench — an assistant whose *process is visible* (spec §16.2, §30.7). Not a chatbot.

Question bar + suggested queries (golden-set categories, spec §17.1). On submit, `PipelineStages` shows the twelve stages progressing (…→ **evidence verify** → …). The answer is a **report card**: prose answer · `ConfidenceMeter`→breakdown · `FactorBars` · `EvidenceChip`s · queries executed (Q-refs) · KB sources (typed) · `LimitationsNote` · `LineagePanel` · feedback · role-gated approve · lifecycle badge. Session-local history rail. LLM down → deterministic-fallback answer renders with `method: deterministic_fallback` stated and the pill at L3 (spec §16.4) — demo step 11.

Backend: `POST /ai/ask` · `POST /insights/{id}/feedback` · `/approve`.

### E.8 Forecasts — `/forecasts` · Anomaly Register — `/anomalies`

**Forecasts** (spec §30.8): `DataGrid` of districts by `RiskBand`; row expansion → `FactorBars`, counterfactuals, fitted series, training-window caveat. District name → `/geo?district=…`.
**Anomalies** *(new surface for an existing endpoint)*: `FilterBar` + grid of anomaly `InsightCard`s (baseline, σ, both methods per spec §13), ranked; subject chips → `/geo` or `/cases`. This is where the Command stat and the tray land.

Backend: `GET /predictions/districts` · `GET /anomalies`.

### E.9 Data Quality — `/quality`

An administrative product, not a defect list (spec §5.3, §30.9): six-dimension `QualityBadge` grid per district · trend · top rules firing (Q01–Q18, plain-language names) · "stations that would benefit from data-entry support" ranked. Finding → inspector → affected entity.

Backend: `GET /quality/scores` · `/quality/findings`.

### E.10 System — `/system` · Admin — `/admin`

Judge-facing ops surfaces (spec §25, §22, §17.4, §21): health (dependency states + ladder) · metrics (latency percentiles, cache hits, token counts, fallback count) · registries (services, models, prompts) · **eval scorecard** (§17 metrics rendered — show it in Q&A) · audit grid (Auditor role) · role administration. All `DataGrid` + `Stat` assemblies.

Backend: `GET /system/health` · `/metrics` · `/registry` · `/eval` · `GET /audit`.

---

## F. Design system (expanded)

Tokens are master spec §31.1 verbatim — **the prototype's gold accent is replaced by `--signal` cyan in Session 1**. Additions below extend, not replace.

**Typography.** Display (`Space Grotesk`): 24/32 page titles, 18/26 panel titles. Body (`Inter`): 14/20 default, 13/18 dense grids, 12/16 captions and badge text. Mono (`JetBrains Mono`): identifiers only — CrimeNo, KGID, IDs, timestamps in audit rows. Minimum rendered size 12 px. No font weight above 600.

**Spacing & grid.** 8 px base (spec §31.1); allowed steps 4/8/12/16/24/32. Page gutter 24. Three-column workspaces: 280 px left rail · fluid centre · 360 px right column. `InspectorPanel`: 420 overlay, 380 docked. `DataGrid` rows 36 px (dense) / 44 (comfortable) — density toggle in the grid header, persisted per user.

**Elevation.** Two levels only. Level 0: page surfaces, 1 px `--line` borders, no shadow. Level 1: floating panels (inspector-overlay, ⌘K, tray, tooltips) — shadow `0 8px 24px rgb(0 0 0 / .45)`. Nothing else casts shadow (spec §31.2).

**Iconography.** One line-icon set (Lucide), 16 px in text/rows, 20 px in the rail, stroke 1.5. Entity-type glyphs are fixed and global: case ▣, person ◉, officer ✦, station ⌂, district ⬡, charge §, insight ◆ — the same glyph everywhere an entity type appears (chips, nodes, cards, search results).

**Motion.** As §B; additionally: grid sort/filter changes do not animate; skeletons appear only after 300 ms delay to avoid flicker; the three orchestrated moments are disabled entirely under `prefers-reduced-motion`, not slowed.

**Accessibility.** Contrast ≥ 4.5:1 for text on `--bg-panel` (the §31 ink scale passes; never place `--ink-faint` on `--bg-raised`). Visible 2 px `--signal` focus ring on every interactive element; full keyboard reach: rail (Alt+1…9), ⌘K, grid row nav, Esc closes the inspector. `GraphCanvas` and `MapCanvas` each expose their table fallback as the accessible alternative (same data, `DataGrid`). Risk/confidence bands never rely on colour alone — band label text accompanies the colour. Masked values render the lock glyph + "restricted", not blank space (spec §31.2).

**Responsive.** Desktop-first, designed for 1440; supported ≥ 1280. Below 1280 the right column collapses into inspector-toggles. No mobile layout — at < 1024 a static notice: "LUMEN is designed for operations workstations." (Judges demo on laptops; a broken tablet layout is worse than an honest notice.)

**Dark theme.** The only theme. No light mode. Long-session ergonomics: body text is `--ink-primary` at 14/20, never pure white; large fills use `--bg-panel`, with `--bg-raised` reserved for hover/selection so selection state is always visible.

---

## G. Frontend engineering architecture

**Stack:** Vite + React + TypeScript. **Server state:** TanStack Query — every §29 endpoint has one typed hook in `api/hooks/`; caching/staleness handled there, never in components. **Client state:** URL query params (filters, viewport, selection) + one small session context (user, role, scope, degradation level from the last envelope). **No global store.** If someone proposes Redux, the answer is no — there is no client state here that isn't URL or session.

**Types are generated** from the backend contracts (spec §7) — never hand-written. A contract drift fails the typecheck, which is the point.

**Folder ownership** (extends spec §28 `client/app/src/`): `design/` owns tokens+primitives; `components/` owns D1–D13 (each with its own directory, stories file, and fallback states); `features/<page>/` owns page assembly only — **a feature folder may not define a reusable-looking component**; if it's needed twice, it moves to `components/` first. `api/` owns hooks + generated types + the envelope client (degradation banner + `ErrorState` mapping live here, once).

**Error boundaries per panel**, not per page: a graph crash degrades one panel to its table fallback; the workspace around it survives.

**Performance budgets:** first meaningful paint of `/command` < 2 s on the demo machine; grids virtualised above 50 rows; `GraphCanvas` capped at 300 rendered nodes (cluster placeholders beyond — spec §14.5 precompute keeps payloads under this in practice); map layers request simplified geometries per zoom level; route-level code splitting with the graph and map libraries in their own chunks so `/command` doesn't pay for Cytoscape.

**Testing scope (honest for the budget):** unit tests for the `InsightCard` invariants (limitations always rendered; evidence always links; confidence equals breakdown composite — mirrors spec §8 invariants), the `ErrorState` mapping, and the URL-state serializers. One Playwright script that walks the §I demo path — it doubles as the pre-demo smoke test.

---

## H. Implementation roadmap — six sessions

Each session ends demoable. Session prompt: *"Implement Session N of docs/LUMEN_Frontend_Architecture.md (v2). The backend is complete — wire to live §29 endpoints. Do not invent features. Do not modify backend code."*

| # | Session | Builds | Done when |
|---|---|---|---|
| **1** | **Foundation, shell, component core** | Tokens (gold → `--signal` cyan), shell (rail, top bar, ⌘K, tray, `DegradationPill`), envelope API client + `ErrorState` mapping + generated types + Query hooks, URL-state utilities, primitives, and D1–D3 + D11–D13 complete (`InsightCard` family, `FilterBar`, badges) | A live insight renders with every §8 field; `SCOPE_DENIED` renders as governance notice; degradation banner appears on `meta.degradation_level ≠ L0`; filters round-trip through the URL |
| **2** | **Case Registry + Case Workspace** | E.3 (`FilterBar` + virtualised grid + keyboard nav + inspector peek), E.4 in full with D4, D5, D7 (to-scale timeline + median line), intelligence column incl. outcome card; board panel wired to `/cases/{id}/graph` rendered as the **table fallback** pending Session 4's canvas | "Whitefield burglary, March" is findable in three keystrokes and opens whole from live calls; masking varies by role; every entity links onward |
| **3** | **Command Center + Geo + Anomalies** | D9 `MapCanvas` (five layers incl. reporting-delay), E.1, E.2, `InspectorPanel` overlay mode, E.8-anomalies, the two map motions | State→District→Station→Cluster→Case drill on live data; scrubber re-queries on release; tray items land on `/anomalies` |
| **4** | **Graph surfaces** | D8 `GraphCanvas` + docked `InspectorPanel`; the investigation board goes live (1-hop expansion — moment #3); E.6 Network with the Q1–Q10 rail; E.5 Person Dossier with D6, candidates block, dispute | Q2 highlights the seeded broker; expanding A2 reveals the cross-district cases; dossier shows match evidence; canvas cap + table toggle work |
| **5** | **Intelligence Console + Forecasts** | E.7 (`PipelineStages`, report card, feedback/approve, deterministic-fallback rendering), E.8-forecasts | A golden-set question returns a full report card; killing the LLM shows the L3 fallback visibly; forecast rows expand to counterfactuals |
| **6** | **Assembly + hardening + demo** | E.9 Quality, E.10 System/Admin (incl. eval scorecard), C.3 Briefing, C.1 Landing, C.2 polish; empty/error-state audit, reduced-motion pass, §4.2 masking audit, Playwright demo script; run the §I demo **twice without reload and once with the LLM disabled** | Post-login lands on the briefing; `/system/eval` renders the scorecard; the twelve-step demo runs clean; a fresh judge can self-drive from `/` |

**Cut line inside Session 6** if time collapses (Sessions 1–5 are the product's identity and are never cut): drop C.1 Landing (open the demo at `/login`) and `/admin` role administration (show governance via live case-masking instead). Quality, System-eval and the Briefing stay — they are grid assemblies and carry disproportionate judge value.

---

## I. Demo flow (frontend cut of master spec §34)

`/` (or `/login` if landing is cut) → **Briefing** (15 s — "the analyst's morning") → **Command Center** (choropleth load) → district → **Geo** hotspot → cluster inspector → **Case Workspace**: decoder + Q04 flag → board expansion of A2 — *the 45-second entity-resolution story* → risk card → confidence breakdown naming its limiting component → **Network** Q2 hidden intermediary (caveat on the card) → **Console** (stages progress → report card → evidence chips) → role-switch to Station Officer (same case, masked) → live case insert (tray ticks, network updates) → kill the LLM (L3 pill, fallback answer) → **`/system/eval`** scorecard → close.

Rehearse until it runs twice without reload and once degraded. Build order = demo order. `/admin` is not demoed unless asked; the Registry (`/cases`) appears only as the three-keystroke search moment — its job in the demo is speed, not screen time.