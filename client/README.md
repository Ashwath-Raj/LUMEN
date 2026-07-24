# LUMEN — Crime Intelligence Platform (Frontend)

> **Note:** this document describes the frontend as it existed before the
> repository was restructured to match `docs/LUMEN_MASTER_SPEC_V3.md` §28.
> Paths below (`src/...`) now live under `client/app/src/...`; the
> Analytics, Operations, and Administration routes described in the routing
> map were archived to `legacy/client-extra/` (they are not in the frozen
> spec's §30 information architecture) and no longer exist in the live
> route tree. See `docs/MIGRATION.md` for the authoritative record of what
> moved where. This file is kept as a historical description of the
> pre-migration frontend, not a current guide.

React (Vite) + Tailwind CSS + React Router + Axios frontend for the LUMEN
Karnataka State Police crime intelligence platform. FastAPI backend is
consumed via the `services/api` layer.

This commit is **architecture only** — routing, layouts, component
contracts, and service stubs are wired end-to-end, but every screen
currently renders a `PagePlaceholder`. Visual design comes next, screen by
screen, using this structure.

## Stack

- React 18 + Vite
- React Router v6 (nested layouts, lazy-loaded routes)
- Tailwind CSS (design tokens in `tailwind.config.js`)
- Axios (single client + per-domain service modules)

## Folder structure

```
src/
  app/                 Router + route guards
    AppRouter.jsx       Full route tree
    ProtectedRoute.jsx  Redirects unauthenticated operators to /login
    RoleGuard.jsx       Gates a subtree by operator role (e.g. Administration)

  layouts/             Shell components, nested via <Outlet/>
    AuthLayout.jsx          Centered card shell (login)
    RootLayout.jsx          Top nav shell, wraps every authenticated route
    ModuleLayout.jsx        Left sidebar shell, config-driven per module
    CaseWorkspaceLayout.jsx Nested shell for an open case (Suspects/Evidence/
                            Timeline/Network/Reports tabs)

  components/
    common/            Cross-cutting UI: Button, Badge, StatCard, DataTable,
                        SearchInput, NotificationBell, Drawer, UploadDropzone,
                        FormField, PagePlaceholder, FullScreenLoader
    layout/            TopNavBar, ModuleSidebar, OperatorMiniProfile
    auth/               LoginCard
    dashboard/          CrimeTrendChart, ActivityLogFeed
    investigation/      CorkboardCanvas, SuspectDossierCard, EvidenceCard,
                        CaseFolderCard, NetworkGraph, TimelineNode,
                        CaseWorkspaceSidebar
    geospatial/         MapPanel, FilterPanel
    analytics/          (README — planned components, pending API shape)
    operations/         (README — planned components, pending API shape)
    administration/     (README — planned components, pending API shape)
    intelligence/       (README — planned components, pending API shape)

  pages/               One file per route, grouped by module. Currently all
                        render <PagePlaceholder/> with a label + Figma reference.

  config/
    navigation.js       Single source of truth for top nav + per-module
                        sidebars + role visibility
    constants.js        App-wide constants (status enums, etc.)

  context/
    AuthContext.jsx      Session state: operator, isAuthenticated, login, logout

  services/api/         One module per backend domain, all built on the
                        shared axiosClient (baseURL, auth header, 401 handling)

  hooks/                useAuth, useAsyncData (fetch boilerplate), useDebounce
  utils/                classNames, formatters (timestamps, reference IDs, coords)
  styles/index.css      Tailwind layers + shared .panel / .label-eyebrow classes
```

## Routing map

```
/login                                    AuthLayout > LoginPage

/dashboard                                RootLayout > DashboardPage

/analytics                                RootLayout > ModuleLayout(analytics)
  /analytics/case-files
  /analytics/evidence-vault
  /analytics/field-reports
  /analytics/signal-intelligence
  /analytics/personnel
  /analytics/archived

/geospatial                               RootLayout > GeospatialPage

/investigation                            RootLayout > ModuleLayout(investigation)
  /investigation/suspects
  /investigation/evidence
  /investigation/watchlist
  /investigation/fir-intelligence
  /investigation/archive
  /investigation/interviews/:interviewId
  /investigation/forensics/:deviceId
  /investigation/cases/:caseId            > CaseWorkspaceLayout
    /investigation/cases/:caseId/suspects
    /investigation/cases/:caseId/evidence
    /investigation/cases/:caseId/timeline
    /investigation/cases/:caseId/network
    /investigation/cases/:caseId/reports

/intelligence                             RootLayout > AIWorkbenchPage

/operations                               RootLayout > ModuleLayout(operations)
  /operations/fir-upload
  /operations/suspect-profiles
  /operations/dossier

/administration  (admin/command only)     RootLayout > ModuleLayout(administration)
  /administration/personnel
  /administration/audit-log
```

## Design tokens (see `tailwind.config.js`)

Dark "fusion-center" theme: near-black surfaces, a restrained gold accent,
and four status colors (critical/warning/success/info). Type system is
Fraunces (dossier-style display headings) + Inter (UI body) + IBM Plex Mono
(IDs, timestamps, telemetry) — loaded via Google Fonts in `index.html`.

## Open decisions (flagged, not resolved)

1. Two login designs exist in the Figma export: a polished "Restricted
   Access" screen (Clearance ID + Biometric/Passphrase) and a rough
   red-neon Username/Password + role-dropdown mockup. `LoginCard` currently
   implements the former — confirm before the visual pass.
2. A red-neon "State HQ → Specialized Wings → Territorial Units" org-chart
   screen may be an onboarding/role-selection step or discarded exploration.
   Not represented in the route tree yet.
3. Several dashboard/reconstruction-board frames are near-duplicate design
   iterations; one canonical version per screen will be chosen when that
   screen is actually built.

## Getting started

```bash
npm install
cp .env.example .env
npm run dev
```
