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
import { queryKeys } from "@/api/queryKeys";
import type { Insight } from "@/types/contracts";

export function useCaseInsights(id: string) {
  return useQuery({
    queryKey: queryKeys.caseInsights(id),
    enabled: !!id,
    queryFn: async ({ signal }) => {
      const { data } = await apiFetch<Insight[]>(`/cases/${id}/insights`, {
        signal,
      });
      return data;
    },
  });
}
