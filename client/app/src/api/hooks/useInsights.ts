/**
 * `GET /insights` — the insight feed (spec §29.1), one typed hook (arch §G).
 *
 * The feed backs the Briefing "top insights" list (C.3,
 * `?lifecycle_state=verified&limit=6`), the Command live feed (E.1, `?limit=10`),
 * and the shared insight feed surface (D11 `FilterBar`). Every list endpoint
 * returns `total` and accepts `limit`/`offset` (§29.2), so the response is a
 * paged list.
 *
 * One endpoint → one hook → one query key. Filters serialize to query params;
 * the same params key the cache, so two callers with the same filters share a
 * fetch and back/forward through the URL is a cache hit.
 *
 * Endpoint: `/intelligence/workbench` — the persisted §8 Insight feed.
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { rejectUnavailable } from "@/api/unavailable";
import { queryKeys } from "@/api/queryKeys";
import type { Insight, InsightKind, LifecycleState } from "@/types/contracts";

/** §29.1 filter params for the insight feed. All optional; all URL-serialized. */
export interface InsightFeedParams {
  lifecycle_state?: LifecycleState;
  kind?: InsightKind;
  subject_type?: Insight["subject_type"];
  subject_id?: string;
  limit?: number;
  offset?: number;
}

/** A paged insight list (§29.2 `total` + `limit`/`offset`). */
export interface InsightFeed {
  items: Insight[];
  total: number;
  limit: number;
  offset: number;
}

/** Serialize feed params to a URLSearchParams, omitting empty values. */
function toQuery(params: InsightFeedParams): URLSearchParams {
  const q = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    q.set(key, String(value));
  }
  return q;
}

export function useInsights(params: InsightFeedParams = {}) {
  return useQuery({
    // queryKeys.insights takes the open Record shape the Session-0 registry uses
    // for every filtered key; the fixed-shape params satisfy it structurally.
    queryKey: queryKeys.insights(params as Record<string, unknown>),
    retry: false,
    queryFn: async ({ signal }): Promise<InsightFeed> => {
      if (ENDPOINTS.insights === null) rejectUnavailable("Insights feed");
      // Served by GET /intelligence/workbench (the persisted lumen_insight
      // feed): { insights, total, limit, offset } → normalised to InsightFeed.
      const { data } = await apiFetch<{
        insights: Insight[];
        total: number;
        limit: number;
        offset: number;
      }>(ENDPOINTS.insights, { signal, query: toQuery(params) });
      return {
        items: data.insights,
        total: data.total,
        limit: data.limit,
        offset: data.offset,
      };
    },
  });
}
