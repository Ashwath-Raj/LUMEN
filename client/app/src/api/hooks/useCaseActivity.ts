/**
 * `GET /audit` (case-scoped) — the §21 access log for one case (E.4 Activity
 * tab: who read it, who ran which AI query, who was denied). Read-only (§21).
 * One typed hook returning the paged `ActivityLog` (§29.2).
 *
 * The case scope is passed as a `subject` param (the §29.1 audit endpoint is
 * Auditor-facing but scopes to a subject); when the backend lands, a role below
 * Auditor may receive `SCOPE_DENIED`, which the `QueryBoundary` renders as the
 * calm governance notice — an expected, correct state, not a failure.
 *
 * NOTE: canonical endpoint pending backend; wired to the §29.1 path, drift fails
 * typecheck (arch §G).
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { queryKeys } from "@/api/queryKeys";
import type { ActivityLog } from "@/types/timeline";

interface CaseActivityParams {
  limit?: number;
  offset?: number;
}

export function useCaseActivity(id: string, params: CaseActivityParams = {}) {
  return useQuery({
    queryKey: queryKeys.caseActivity(id, params as Record<string, unknown>),
    enabled: !!id,
    queryFn: async ({ signal }) => {
      const query = new URLSearchParams({ subject: `case:${id}` });
      if (params.limit !== undefined) query.set("limit", String(params.limit));
      if (params.offset !== undefined)
        query.set("offset", String(params.offset));
      const { data } = await apiFetch<ActivityLog>("/audit", { signal, query });
      return data;
    },
  });
}
