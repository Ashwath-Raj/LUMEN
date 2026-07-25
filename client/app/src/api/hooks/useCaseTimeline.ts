/**
 * `GET /cases/{id}/timeline` — the case lifecycle timeline (E.4 Timeline tab,
 * §30.4 "derived lifecycle with gaps and district benchmarks"), one typed hook.
 * Returns `CaseTimeline` (ProcessEvents + district-median reference).
 *
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { rejectUnavailable } from "@/api/unavailable";
import { queryKeys } from "@/api/queryKeys";
import type { CaseTimeline } from "@/types/timeline";

// Served by GET /investigation/cases/{id}/timeline (§2.1 ProcessEvents with
// §2.3 labels + the district-median reference).
export function useCaseTimeline(id: string) {
  return useQuery({
    queryKey: queryKeys.caseTimeline(id),
    enabled: !!id,
    retry: false,
    queryFn: async ({ signal }) => {
      if (ENDPOINTS.caseTimeline === null) rejectUnavailable("Case timeline");
      const { data } = await apiFetch<CaseTimeline>(
        ENDPOINTS.caseTimeline(id),
        { signal },
      );
      return data;
    },
  });
}
