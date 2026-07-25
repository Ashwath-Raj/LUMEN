/**
 * `GET /cases/{id}/timeline` — the case lifecycle timeline (E.4 Timeline tab,
 * §30.4 "derived lifecycle with gaps and district benchmarks"), one typed hook.
 * Returns `CaseTimeline` (ProcessEvents + district-median reference).
 *
 * NOTE: canonical endpoint pending backend; wired to the §29.1 path, drift fails
 * typecheck (arch §G).
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { rejectUnavailable } from "@/api/unavailable";
import { queryKeys } from "@/api/queryKeys";
import type { CaseTimeline } from "@/types/timeline";

// No `/cases/{id}/timeline` endpoint exists in the backend OpenAPI, so this hook
// resolves to the "not available yet" degraded state rather than requesting a
// non-existent path (repoint the ENDPOINTS entry when the backend adds it).
export function useCaseTimeline(id: string) {
  return useQuery({
    queryKey: queryKeys.caseTimeline(id),
    enabled: !!id,
    retry: false,
    queryFn: async ({ signal }) => {
      if (ENDPOINTS.caseTimeline === null) rejectUnavailable("Case timeline");
      const { data } = await apiFetch<CaseTimeline>(ENDPOINTS.caseTimeline, {
        signal,
      });
      return data;
    },
  });
}
