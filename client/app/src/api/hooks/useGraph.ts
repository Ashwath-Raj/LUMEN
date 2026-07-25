/**
 * Intelligence-graph hooks (D8, §14) — reconciled against the backend OpenAPI.
 *
 * There is NO graph endpoint in the OpenAPI (`/cases/{id}/graph`,
 * `/network/query/{q}`, `/persons/{id}/network` are all absent — the graph
 * subsystem is a later backend session). So each hook resolves immediately to
 * the "not available yet" degraded state via `rejectUnavailable` — it never
 * requests a non-existent path and never fabricates relationships. When the
 * backend adds a graph endpoint, repoint the `ENDPOINTS` entry (one line) and the
 * hook goes live against the frozen `GraphContract` shape.
 *
 * One endpoint → one hook → one query key (arch §G).
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { rejectUnavailable } from "@/api/unavailable";
import { queryKeys } from "@/api/queryKeys";
import type { GraphPayload, GraphQueryResult } from "@/types/graph";

/** `GET /cases/{id}/graph` — the investigation board payload (E.4). */
export function useCaseGraph(id: string) {
  return useQuery({
    queryKey: queryKeys.caseGraph(id),
    enabled: !!id,
    retry: false,
    queryFn: async ({ signal }): Promise<GraphPayload> => {
      if (ENDPOINTS.caseGraph === null) rejectUnavailable("Investigation graph");
      const { data } = await apiFetch<GraphPayload>(ENDPOINTS.caseGraph(id), {
        signal,
      });
      return data;
    },
  });
}

/** `GET /network/query/{q}` — one of the ten named queries (E.6, §14.4). */
export function useNetworkQuery(q: string | null) {
  return useQuery({
    queryKey: queryKeys.networkQuery(q ?? ""),
    enabled: !!q,
    retry: false,
    queryFn: async ({ signal }): Promise<GraphQueryResult> => {
      if (ENDPOINTS.networkQuery === null || !q)
        rejectUnavailable("Network query");
      const { data } = await apiFetch<GraphQueryResult>(
        ENDPOINTS.networkQuery(q),
        { signal },
      );
      return data;
    },
  });
}

/** `GET /persons/{id}/network` — a person's ego graph (E.5). */
export function usePersonNetwork(id: string) {
  return useQuery({
    queryKey: queryKeys.personNetwork(id),
    enabled: !!id,
    retry: false,
    queryFn: async ({ signal }): Promise<GraphPayload> => {
      if (ENDPOINTS.personNetwork === null) rejectUnavailable("Ego graph");
      const { data } = await apiFetch<GraphPayload>(
        ENDPOINTS.personNetwork(id),
        { signal },
      );
      return data;
    },
  });
}
