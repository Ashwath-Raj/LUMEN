/**
 * Intelligence-graph hooks (D8, §14) — all three are LIVE against the
 * specification's own paths:
 *
 *   GET /network/query/{q1..q10}   §14.4 named queries → Insight + graph
 *   GET /persons/{id}/network      §29.1 ego graph
 *   GET /cases/{id}/graph          §29.1 investigation-board payload
 *
 * The backend returns the §7 `GraphContract` shape; `adaptGraph` translates it
 * to the canvas payload in one place. §14.4's "never a bare graph" invariant is
 * preserved: the named-query hook returns the Insight alongside the graph.
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { rejectUnavailable } from "@/api/unavailable";
import { adaptGraph, type RawGraphContract } from "@/api/graphAdapter";
import { queryKeys } from "@/api/queryKeys";
import type { Insight } from "@/types/contracts";
import type { GraphPayload, GraphQueryResult } from "@/types/graph";

/** `GET /cases/{id}/graph` — the investigation board payload (E.4). */
export function useCaseGraph(id: string) {
  return useQuery({
    queryKey: queryKeys.caseGraph(id),
    enabled: !!id,
    retry: false,
    queryFn: async ({ signal }): Promise<GraphPayload> => {
      if (ENDPOINTS.caseGraph === null) rejectUnavailable("Investigation graph");
      const { data } = await apiFetch<RawGraphContract>(ENDPOINTS.caseGraph(id), {
        signal,
      });
      return adaptGraph(data)!;
    },
  });
}

/** Params the ten §14.4 queries accept (each uses the subset it needs). */
export interface NetworkQueryParams {
  person_a?: string;
  person_b?: string;
  group_a?: string[];
  group_b?: string[];
  district_id?: number;
  case_id?: number;
  top_n?: number;
  as_of?: string;
}

/** `GET /network/query/{q}` — one of the ten named queries (E.6, §14.4). */
export function useNetworkQuery(q: string | null, params: NetworkQueryParams = {}) {
  return useQuery({
    queryKey: queryKeys.networkQuery(q ?? "", params as Record<string, unknown>),
    enabled: !!q,
    retry: false,
    queryFn: async ({ signal }): Promise<GraphQueryResult> => {
      if (ENDPOINTS.networkQuery === null || !q) rejectUnavailable("Network query");
      const query = new URLSearchParams();
      for (const [key, value] of Object.entries(params)) {
        if (value === undefined || value === null || value === "") continue;
        if (Array.isArray(value)) value.forEach((v) => query.append(key, String(v)));
        else query.set(key, String(value));
      }
      const { data } = await apiFetch<{ insight: Insight; graph: RawGraphContract }>(
        ENDPOINTS.networkQuery(q),
        { signal, query },
      );
      return { insight: data.insight, graph: adaptGraph(data.graph)! };
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
      const { data } = await apiFetch<RawGraphContract>(
        ENDPOINTS.personNetwork(id),
        { signal },
      );
      return adaptGraph(data)!;
    },
  });
}
