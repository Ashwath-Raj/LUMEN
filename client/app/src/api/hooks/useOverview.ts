/**
 * `GET /overview` — one typed hook (arch §G: "every §29 endpoint has one typed
 * hook in api/hooks/; caching/staleness handled there, never in components").
 *
 * Backs the Command Center (E.1) and Briefing (C.3). Returns the unwrapped,
 * typed `Overview` payload; no endpoint logic beyond wiring lives here.
 *
 * NOTE: the canonical §29.1 `/overview` endpoint is not yet served by the
 * backend (only legacy `/dashboard/*` stubs returning HTTP 501). This hook is
 * wired to the canonical path against the frozen envelope + transcribed
 * `Overview` contract; it connects with zero change once the endpoint lands, and
 * a contract drift then fails the typecheck (arch §G). Until then it surfaces a
 * typed `ApiError` that the consumer renders via `ErrorState`.
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { queryKeys } from "@/api/queryKeys";
import type { Overview } from "@/types/overview";

export function useOverview() {
  return useQuery({
    queryKey: queryKeys.overview(),
    queryFn: async ({ signal }) => {
      const { data } = await apiFetch<Overview>("/overview", { signal });
      return data;
    },
  });
}
