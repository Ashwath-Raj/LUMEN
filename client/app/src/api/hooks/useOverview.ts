/**
 * `GET /overview` — one typed hook (arch §G: "every §29 endpoint has one typed
 * hook in api/hooks/; caching/staleness handled there, never in components").
 *
 * Backs the Command Center (E.1) and Briefing (C.3). Returns the unwrapped,
 * typed `Overview` payload; no endpoint logic beyond wiring lives here.
 *
 * NOTE: the backend OpenAPI exposes NO `/overview` endpoint (the closest is the
 * legacy `/dashboard/summary` 501 stub, a different shape). Rather than request a
 * non-existent path, this hook resolves to the "not available yet" degraded
 * state (`ENDPOINTS.overview` is null); repoint it when the backend adds one.
 * (Not consumed by any Session 1–3 page yet — Command/Briefing are placeholders.)
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
