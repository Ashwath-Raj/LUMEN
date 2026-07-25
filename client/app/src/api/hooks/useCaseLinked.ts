/**
 * `GET /cases/{id}/linked` — linked cases (§29.1): other cases sharing entities,
 * with the reason + shared entities (E.4 "Linked cases (reason + shared
 * entities)"). One typed hook. The linked list reuses `CaseListItem` rows plus a
 * `reason` string; a case with no links returns an empty list (rendered as the
 * Empty state, never fabricated).
 *
 * NOTE: canonical endpoint pending backend; wired to the §29.1 path, drift fails
 * typecheck (arch §G).
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { queryKeys } from "@/api/queryKeys";
import type { CaseListItem } from "@/types/case";

/** A linked case = a case row + why it is linked (§29.1 "reason + shared entities"). */
export interface LinkedCase {
  case: CaseListItem;
  reason: string;
  shared_entities: string[];
}

export function useCaseLinked(id: string) {
  return useQuery({
    queryKey: queryKeys.caseLinked(id),
    enabled: !!id,
    queryFn: async ({ signal }) => {
      const { data } = await apiFetch<LinkedCase[]>(`/cases/${id}/linked`, {
        signal,
      });
      return data;
    },
  });
}
