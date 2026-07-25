/**
 * `GET /cases/{id}` — the case aggregate (E.4), one typed hook (arch §G). "One
 * aggregate call renders header + entities" (§29.1): this returns the `CaseDetail`
 * the workspace header, summary strip, and Overview tab are built from.
 *
 * `enabled: !!id` guards the initial render before the route param resolves.
 * NOTE: canonical endpoint pending backend (legacy `/investigation/cases/{id}` →
 * 501); wired to the §29.1 path, drift fails typecheck (arch §G).
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { queryKeys } from "@/api/queryKeys";
import type { CaseDetail } from "@/types/case";

export function useCase(id: string) {
  return useQuery({
    queryKey: queryKeys.case(id),
    enabled: !!id,
    queryFn: async ({ signal }) => {
      const { data } = await apiFetch<CaseDetail>(`/cases/${id}`, { signal });
      return data;
    },
  });
}
