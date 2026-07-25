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

  // Case Registry + Workspace (Session 2, §29.1).
  cases: (params?: Record<string, unknown>) => ["cases", params ?? {}] as const,
  case: (id: string) => ["case", id] as const,
  caseTimeline: (id: string) => ["case", id, "timeline"] as const,
  caseInsights: (id: string) => ["case", id, "insights"] as const,
  caseLinked: (id: string) => ["case", id, "linked"] as const,
  caseActivity: (id: string, params?: Record<string, unknown>) =>
    ["case", id, "activity", params ?? {}] as const,
  caseLookups: () => ["cases", "lookups"] as const,

  person: (id: string) => ["person", id] as const,
  systemHealth: () => ["system", "health"] as const,
} as const;
