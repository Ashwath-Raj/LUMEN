/**
 * Canonical backend endpoint registry — the §29.1 API contract, verbatim.
 *
 * Every path below is defined by LUMEN_MASTER_SPEC_V3 §29.1 and confirmed
 * present in the live OpenAPI. Hooks import from here; no hook hard-codes a
 * path, so the frontend↔backend contract is auditable in one file.
 *
 * `null` marks a surface the specification names but whose architecture it does
 * not define; the owning hook resolves to the specification's own degraded
 * state rather than requesting a route that cannot exist.
 */

export const ENDPOINTS = {
  // ── Authentication (§26.1 row 17 — Catalyst) ──────────────────────────
  me: "/auth/me",

  // ── Overview (§29.1) ──────────────────────────────────────────────────
  overview: "/overview" as string | null,

  // ── Cases (§29.1) ─────────────────────────────────────────────────────
  cases: "/cases",
  case: (id: string) => `/cases/${id}`,
  caseTimeline: ((id: string) => `/cases/${id}/timeline`) as null | ((id: string) => string),
  caseInsights: ((id: string) => `/cases/${id}/insights`) as null | ((id: string) => string),
  caseLinked: ((id: string) => `/cases/${id}/linked`) as null | ((id: string) => string),
  caseGraph: ((id: string) => `/cases/${id}/graph`) as null | ((id: string) => string),
  /** T2 — SmartBrowz PDF; the control is hidden while unbuilt (arch E.4). */
  caseBriefing: (id: string) => `/cases/${id}/briefing`,
  /** §29.1 defines no lookups/facets endpoint; the FilterBar uses free text. */
  caseLookups: null,

  // ── Geo (§29.1, §30.3) ────────────────────────────────────────────────
  geoDistricts: "/geo/districts" as string | null,
  geoHotspots: "/geo/hotspots",
  geoUnits: ((id: string) => `/geo/units/${id}`) as null | ((id: string) => string),
  geoDelay: "/geo/delay" as string | null,

  // ── Insights (§29.1, §8, §10, §17.5) ──────────────────────────────────
  insights: "/insights" as string | null,
  insightLineage: (id: string) => `/insights/${id}/lineage`,
  insightApprove: ((id: string) => `/insights/${id}/approve`) as null | ((id: string) => string),
  insightFeedback: ((id: string) => `/insights/${id}/feedback`) as null | ((id: string) => string),

  // ── Network / graph (§29.1, §14.4) ────────────────────────────────────
  networkQuery: ((q: string) => `/network/query/${q}`) as null | ((q: string) => string),
  personNetwork: ((id: string) => `/persons/${id}/network`) as null | ((id: string) => string),

  // ── Predictions · anomalies · recommendations (§29.1, §13, §18) ───────
  predictionsDistricts: "/predictions/districts",
  predictionOutcome: (caseId: string) => `/predictions/outcome/${caseId}`,
  anomalies: "/anomalies",
  recommendations: "/recommendations" as string | null,

  // ── Persons (§29.1, §6.4) ─────────────────────────────────────────────
  persons: "/persons",
  person: (id: string) => `/persons/${id}`,
  personDispute: (id: string) => `/persons/${id}/dispute`,

  // ── Quality · AI · System · Audit (§29.1) ─────────────────────────────
  qualityScores: "/quality/scores",
  qualityFindings: "/quality/findings",
  aiAsk: "/ai/ask",
  systemHealth: "/system/health",
  systemMetrics: "/system/metrics",
  systemRegistry: "/system/registry",
  systemEval: "/system/eval",
  audit: "/audit",
} as const;
