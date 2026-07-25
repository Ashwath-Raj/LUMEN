/**
 * `GET /cases/{id}/insights` — the case's insights (E.4 Insights tab), one typed
 * hook. Returns the frozen §8 `Insight[]` the `InsightCard` family renders. This
 * is the case-scoped counterpart of the global `useInsights` feed; kept separate
 * because it is a distinct §29.1 endpoint with its own cache key (arch §G: one
 * endpoint → one hook → one key).
 *
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { rejectUnavailable } from "@/api/unavailable";
import { queryKeys } from "@/api/queryKeys";
import type { Insight } from "@/types/contracts";

// Served by GET /intelligence/workbench?subject_type=case&subject_id={id} —
// the persisted lumen_insight feed scoped to one case.
export function useCaseInsights(id: string) {
  return useQuery({
    queryKey: queryKeys.caseInsights(id),
    enabled: !!id,
    retry: false,
    queryFn: async ({ signal }): Promise<Insight[]> => {
      if (ENDPOINTS.caseInsights === null) rejectUnavailable("Case insights");
      const { data } = await apiFetch<{ insights: Insight[] }>(
        ENDPOINTS.caseInsights(id),
        { signal },
      );
      return data.insights;
    },
  });
}
