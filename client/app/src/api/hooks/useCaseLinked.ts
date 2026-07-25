/**
 * `GET /cases/{id}/linked` — linked cases (§29.1). Per §13 case_linkage and §8
 * invariant 1, a link is returned as an Insight (its evidence names the shared
 * entities), never as a bare similarity score.
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { rejectUnavailable } from "@/api/unavailable";
import { queryKeys } from "@/api/queryKeys";
import type { Insight } from "@/types/contracts";

export function useCaseLinked(id: string) {
  return useQuery({
    queryKey: queryKeys.caseLinked(id),
    enabled: !!id,
    retry: false,
    queryFn: async ({ signal }): Promise<Insight[]> => {
      if (ENDPOINTS.caseLinked === null) rejectUnavailable("Linked cases");
      const { data } = await apiFetch<{ linked: Insight[] }>(
        ENDPOINTS.caseLinked(id),
        { signal },
      );
      return data.linked;
    },
  });
}
