/**
 * Central query-key registry for TanStack Query (arch §G).
 *
 * One place defines every cache key so invalidation and prefetch are
 * consistent across hooks. Feature sessions add keys here as they add the
 * corresponding §29 endpoint hook in `api/hooks/`.
 */
export const queryKeys = {
  overview: () => ["overview"] as const,
  insights: (params?: Record<string, unknown>) =>
    ["insights", params ?? {}] as const,

  // Case Registry + Workspace (§29.1).
  cases: (params?: Record<string, unknown>) => ["cases", params ?? {}] as const,
  case: (id: string) => ["case", id] as const,
  caseTimeline: (id: string) => ["case", id, "timeline"] as const,
  caseInsights: (id: string) => ["case", id, "insights"] as const,
  caseLinked: (id: string) => ["case", id, "linked"] as const,
  caseActivity: (id: string, params?: Record<string, unknown>) =>
    ["case", id, "activity", params ?? {}] as const,
  caseLookups: () => ["cases", "lookups"] as const,

  // Geo Intelligence (§29.1, §30.3).
  geoBoundaries: () => ["geo", "boundaries"] as const,
  geoDistricts: () => ["geo", "districts"] as const,
  geoHotspots: (params?: Record<string, unknown>) =>
    ["geo", "hotspots", params ?? {}] as const,
  geoUnits: (districtId: string) => ["geo", "units", districtId] as const,
  geoDelay: (params?: Record<string, unknown>) =>
    ["geo", "delay", params ?? {}] as const,

  person: (id: string) => ["person", id] as const,
  personNetwork: (id: string) => ["person", id, "network"] as const,

  // Intelligence graph (§14).
  caseGraph: (id: string) => ["case", id, "graph"] as const,
  networkQuery: (q: string, params?: Record<string, unknown>) =>
    ["network", q, params ?? {}] as const,

  systemHealth: () => ["system", "health"] as const,
  systemMetrics: () => ["system", "metrics"] as const,
  systemRegistry: () => ["system", "registry"] as const,
  systemEval: () => ["system", "eval"] as const,
  qualityScores: () => ["quality", "scores"] as const,
  qualityFindings: () => ["quality", "findings"] as const,

  // Intelligence workbench (§16, §18).
  persons: (params?: Record<string, unknown>) =>
    ["persons", params ?? {}] as const,
  recommendations: (subject?: string) => ["recommendations", subject ?? ""] as const,
  anomalies: () => ["anomalies"] as const,
  predictionsDistricts: () => ["predictions", "districts"] as const,
  predictionOutcome: (caseId: string) => ["predictions", "outcome", caseId] as const,
} as const;
