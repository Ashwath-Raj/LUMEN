/**
 * `GET /persons/{id}` — the person dossier (E.5, §6.4): resolution evidence,
 * linked records and candidate matches. One typed hook (arch §G).
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { queryKeys } from "@/api/queryKeys";
import type { PersonDetail } from "@/types/person";

export function usePerson(id: string) {
  return useQuery({
    queryKey: queryKeys.person(id),
    enabled: !!id,
    queryFn: async ({ signal }) => {
      const { data } = await apiFetch<PersonDetail>(ENDPOINTS.person(id), {
        signal,
      });
      return data;
    },
  });
}
