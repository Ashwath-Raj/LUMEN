/**
 * Intelligence Workbench hooks — the §29.1 surfaces the workbench consumes.
 *
 *   POST /ai/ask                        REAL — orchestrator (§16.2/§16.4);
 *                                       returns a bare §8 Insight. The §16.4
 *                                       deterministic fallback means it answers
 *                                       even with no LLM configured, and lineage
 *                                       carries `method: deterministic_fallback`.
 *   GET  /intelligence/leads/{session}  mounted, currently 501 → degrades
 *   GET  /dashboard/alerts              mounted, currently 501 → degrades
 *   GET  /persons                       REAL — DB-backed list (context picker)
 *
 * One endpoint → one hook → one key; centralized paths; nothing invented.
 */
import { useMutation, useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { queryKeys } from "@/api/queryKeys";
import type { Insight } from "@/types/contracts";
import type { AskRequest, IntelligenceLead } from "@/types/intelligence";
import type { PersonList } from "@/types/person";

/** POST /ai/ask — ask the orchestrator one question (REAL endpoint). */
export function useAiAsk() {
  return useMutation({
    mutationFn: async (request: AskRequest): Promise<Insight> => {
      const { data } = await apiFetch<Insight>(ENDPOINTS.aiAsk, {
        method: "POST",
        body: request,
      });
      return data;
    },
  });
}

/** GET /recommendations — §18 decision support: recommendation-kind Insights
 *  derived from existing insights (no new model). Empty until the intelligence
 *  engine generates them; never fabricated. */
export function useIntelligenceLeads(sessionId: string) {
  return useQuery({
    queryKey: queryKeys.recommendations(sessionId),
    enabled: !!sessionId,
    retry: false,
    queryFn: async ({ signal }) => {
      const { data } = await apiFetch<{ recommendations: IntelligenceLead[] }>(
        ENDPOINTS.recommendations!,
        { signal },
      );
      return data.recommendations;
    },
  });
}

/** One anomaly row (GET /anomalies — §13 volume-anomaly Insights). */
export interface ActiveAlert {
  id: string;
  headline: string;
  subject_type: string;
  subject_id: string;
  confidence: number;
  lifecycle_state: string;
  generated_at: string;
}

/** GET /anomalies — §29.1 "ranked anomalies", newest first. */
export function useActiveAlerts() {
  return useQuery({
    queryKey: queryKeys.anomalies(),
    retry: false,
    queryFn: async ({ signal }) => {
      const { data } = await apiFetch<{ anomalies: ActiveAlert[] }>(
        ENDPOINTS.anomalies,
        { signal },
      );
      return data.anomalies;
    },
  });
}

/** GET /persons — resolved identities (REAL, DB-backed; §29.2 paged). */
export function usePersons(limit = 100, offset = 0) {
  return useQuery({
    queryKey: queryKeys.persons({ limit, offset }),
    queryFn: async ({ signal }) => {
      const query = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
      });
      const { data } = await apiFetch<PersonList>(ENDPOINTS.persons, {
        signal,
        query,
      });
      return data;
    },
  });
}
