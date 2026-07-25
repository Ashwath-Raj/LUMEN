/**
 * `GET /cases/{id}` — the case aggregate (E.4), one typed hook (arch §G). "One
 * aggregate call renders header + entities" (§29.1): this returns the `CaseDetail`
 * the workspace header, summary strip, and Overview tab are built from.
 *
 * `enabled: !!id` guards the initial render before the route param resolves.
 * Endpoint: `/investigation/cases/{id}` — the case aggregate, live.
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { queryKeys } from "@/api/queryKeys";
import { useSession } from "@/providers/sessionContext";
import type { CaseDetail } from "@/types/case";

export function useCase(id: string) {
  // The caller's §20.1 role drives §4.2 identity masking server-side. When no
  // role is bound yet the backend applies the most restrictive default
  // (station_officer) — masking is never weakened by a missing binding.
  const { role } = useSession();
  return useQuery({
    queryKey: [...queryKeys.case(id), role ?? "unbound"],
    enabled: !!id,
    queryFn: async ({ signal }) => {
      const query = new URLSearchParams();
      if (role) query.set("viewer_role", role);
      const { data } = await apiFetch<CaseDetail>(ENDPOINTS.case(id), { signal, query });
      return data;
    },
  });
}
