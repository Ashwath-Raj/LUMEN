/**
 * `GET /overview` — one typed hook (arch §G: "every §29 endpoint has one typed
 * hook in api/hooks/; caching/staleness handled there, never in components").
 *
 * Backs the Command Center (E.1) and Briefing (C.3). Returns the unwrapped,
 * typed `Overview` payload; no endpoint logic beyond wiring lives here.
 *
 * Endpoint: `/dashboard/summary` — live: §29.1 counts, district risk BANDS,
 * trends and network figures. §8 invariant 1 keeps numeric scores inside
 * Insights, so this payload carries bands and counts only.
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { rejectUnavailable } from "@/api/unavailable";
import { queryKeys } from "@/api/queryKeys";
import type { Overview } from "@/types/overview";

export function useOverview() {
  return useQuery({
    queryKey: queryKeys.overview(),
    retry: false,
    queryFn: async ({ signal }) => {
      if (ENDPOINTS.overview === null) rejectUnavailable("Overview");
      const { data } = await apiFetch<Overview>(ENDPOINTS.overview, { signal });
      return data;
    },
  });
}
