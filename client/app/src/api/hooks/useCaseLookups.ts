/**
 * Filter facet lookups for the Case Registry FilterBar (E.3) — crime heads,
 * districts, stations, statuses, etc. §29.1 names no dedicated lookups endpoint,
 * so this reads the facet metadata `GET /cases` is expected to expose; the hook
 * is isolated so the FilterBar has one source for its select options.
 *
 * It never blocks the grid: on error or before the backend lands, the FilterBar
 * falls back to free-text filter entry (see the FilterBar), so filtering by URL
 * still works. `staleTime` is generous — lookups change rarely.
 *
 * NOTE: endpoint pending backend; wired to a canonical-shaped path, drift fails
 * typecheck (arch §G).
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { rejectUnavailable } from "@/api/unavailable";
import { queryKeys } from "@/api/queryKeys";
import type { CaseLookups } from "@/types/caseFilters";

export function useCaseLookups() {
  return useQuery({
    queryKey: queryKeys.caseLookups(),
    staleTime: 60 * 60 * 1000, // 1h — lookups are near-static (§23 cache intent)
    retry: false, // a missing lookups facet must not spam retries; UI falls back
    queryFn: async ({ signal }) => {
      // No `/cases/lookups` endpoint exists → the FilterBar falls back to
      // free-text filter entry (see CaseRegistryPage); never requests it.
      if (ENDPOINTS.caseLookups === null) rejectUnavailable("Case filter lookups");
      const { data } = await apiFetch<CaseLookups>(ENDPOINTS.caseLookups, { signal });
      return data;
    },
  });
}
