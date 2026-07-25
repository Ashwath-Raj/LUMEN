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
import { queryKeys } from "@/api/queryKeys";
import type { CaseTimeline } from "@/types/timeline";

export function useCaseTimeline(id: string) {
  return useQuery({
    queryKey: queryKeys.caseTimeline(id),
    enabled: !!id,
    queryFn: async ({ signal }) => {
      const { data } = await apiFetch<CaseTimeline>(`/cases/${id}/timeline`, {
        signal,
      });
      return data;
    },
  });
}
