/**
 * `GET /persons/{id}` — the person dossier (E.5, §6.4). Unlike most Session 1–4
 * surfaces, this endpoint is REAL and DB-backed (returns live data, not 501), so
 * the Person Dossier shows genuine resolution evidence. One typed hook (arch §G).
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
