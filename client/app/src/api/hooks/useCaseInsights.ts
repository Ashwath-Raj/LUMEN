/**
 * `GET /cases/{id}/insights` — the case's insights (E.4 Insights tab), one typed
 * hook. Returns the frozen §8 `Insight[]` the `InsightCard` family renders. This
 * is the case-scoped counterpart of the global `useInsights` feed; kept separate
 * because it is a distinct §29.1 endpoint with its own cache key (arch §G: one
 * endpoint → one hook → one key).
 *
 * NOTE: canonical endpoint pending backend; wired to the §29.1 path, drift fails
 * typecheck (arch §G).
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { rejectUnavailable } from "@/api/unavailable";
import { queryKeys } from "@/api/queryKeys";
import type { Insight } from "@/types/contracts";

// No `/cases/{id}/insights` endpoint exists in the backend OpenAPI (the Insight
// engine is a later backend session) → degraded state, no invented request.
export function useCaseInsights(id: string) {
  return useQuery({
    queryKey: queryKeys.caseInsights(id),
    enabled: !!id,
    retry: false,
    queryFn: async ({ signal }) => {
      if (ENDPOINTS.caseInsights === null) rejectUnavailable("Case insights");
      const { data } = await apiFetch<Insight[]>(ENDPOINTS.caseInsights, {
        signal,
      });
      return data;
    },
  });
}
