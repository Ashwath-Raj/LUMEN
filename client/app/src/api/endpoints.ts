/**
 * Canonical backend endpoint registry — the SINGLE source of truth for every
 * path the frontend calls, audited against the backend OpenAPI (the routers in
 * `api/lumen/api/routers/*`). Hooks import from here; no hook hard-codes a path.
 * This is what makes "consume only endpoints that exist" enforceable in one file.
 *
 * ── OpenAPI reconciliation (Session 3 regression fix) ────────────────────
 * The frontend previously called §29.1 *spec* paths (`/geo/districts`, `/cases`,
 * `/overview`, `/insights`, …) that DO NOT EXIST in the backend OpenAPI. Every
 * path below is confirmed present in the OpenAPI. Where the backend has no
 * endpoint for a surface, the constant is `null` and the hook degrades to the
 * "not available yet" state instead of requesting a non-existent route.
 *
 * The live case/geo endpoints are currently the legacy prototype routers
 * (`/investigation/*`, `/geospatial/*`) which return HTTP 501 pending their DB
 * implementation — but they are the REAL, mounted paths, so the frontend targets
 * them (not invented ones) and lights up when they are implemented.
 *
 * `null` = no such endpoint in the OpenAPI (surface renders a degraded state):
 *   overview, insights feed, case timeline / insights / linked, case lookups,
 *   geo districts choropleth values, geo reporting-delay.
 * ─────────────────────────────────────────────────────────────────────────
 */

export const ENDPOINTS = {
  // ── Auth (real; Catalyst-backed) ──────────────────────────────────────
  me: "/auth/me",

  // ── Cases → investigation router (real paths; currently 501) ──────────
  cases: "/investigation/cases",
  case: (id: string) => `/investigation/cases/${id}`,
  /** Governed briefing PDF (real path). */
  caseBriefing: (id: string) => `/cases/${id}/briefing`,
  /** No backend endpoint exists for these case sub-resources. */
  caseTimeline: null,
  caseInsights: null,
  caseLinked: null,
  caseLookups: null,

  // ── Geo → geospatial router (real path; currently 501) ────────────────
  geoHotspots: "/geospatial/hotspots",
  geoSectorIntel: (sectorId: string) => `/geospatial/sector-intel/${sectorId}`,
  /** No dedicated districts-choropleth or reporting-delay endpoint exists;
   *  district boundaries load from the static GeoJSON asset instead. */
  geoDistricts: null,
  geoDelay: null,
  geoUnits: null,

  // ── Overview / insights → no backend endpoint exists ──────────────────
  overview: null,
  insights: null,
  /** Insight lifecycle mutations — no backend endpoint exists yet. */
  insightFeedback: null as null | ((id: string) => string),
  insightApprove: null as null | ((id: string) => string),

  // ── Intelligence graph → NO backend endpoint exists in the OpenAPI ────
  // (`/cases/{id}/graph`, `/network/query/{q}`, `/persons/{id}/network` are all
  // absent — the graph subsystem is a later backend session). The graph renders
  // its empty/degraded state; no relationships are fabricated.
  caseGraph: null as null | ((id: string) => string),
  networkQuery: null as null | ((q: string) => string),
  personNetwork: null as null | ((id: string) => string),

  // ── Real, DB-backed surfaces (exist in OpenAPI) ───────────────────────
  audit: "/audit",
  qualityScores: "/quality/scores",
  qualityFindings: "/quality/findings",
  persons: "/persons",
  person: (id: string) => `/persons/${id}`,
  personDispute: (id: string) => `/persons/${id}/dispute`,
  systemHealth: "/system/health",
  systemMetrics: "/system/metrics",
  systemRegistry: "/system/registry",
  systemEval: "/system/eval",
  aiAsk: "/ai/ask",
} as const;
