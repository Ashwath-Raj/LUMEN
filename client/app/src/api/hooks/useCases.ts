/**
 * `GET /cases` — the Case Registry list (E.3), one typed hook (arch §G).
 *
 * Server-side pagination + filtering + multi-sort: the `CaseFilters` (all §29.1
 * params) serialize to query params, and the same filters key the cache, so
 * back/forward through the URL is a cache hit and no fetch is duplicated. Returns
 * the paged `CaseList` (§29.2 `total` + `limit`/`offset`).
 *
 * `placeholderData: keepPreviousData` keeps the current page visible while the
 * next page/filter loads, so the grid doesn't flash empty on every keystroke.
 *
 * Endpoint: `/investigation/cases` — live, serving the canonical §3.5 schema
 * with §29.2 paging and the §29.1 filter set.
 */
import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { queryKeys } from "@/api/queryKeys";
import type { CaseList } from "@/types/case";
import type { CaseFilters } from "@/types/caseFilters";

/** Serialize `CaseFilters` to the §29.1 query params for `GET /cases`. */
export function caseFiltersToQuery(filters: CaseFilters): URLSearchParams {
  const q = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === "") continue;
    if (key === "sort") {
      const sort = value as CaseFilters["sort"];
      if (sort && sort.length) {
        q.set("sort", sort.map((s) => `${s.field}:${s.direction}`).join(","));
      }
      continue;
    }
    q.set(key, String(value));
  }
  return q;
}

export function useCases(filters: CaseFilters) {
  return useQuery({
    queryKey: queryKeys.cases(filters as Record<string, unknown>),
    queryFn: async ({ signal }) => {
      const { data } = await apiFetch<CaseList>(ENDPOINTS.cases, {
        signal,
        query: caseFiltersToQuery(filters),
      });
      return data;
    },
    placeholderData: keepPreviousData,
  });
}
