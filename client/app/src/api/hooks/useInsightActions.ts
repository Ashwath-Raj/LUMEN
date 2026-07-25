/**
 * Insight lifecycle mutations (spec §29.1, §10, §17.5) — one hook per endpoint.
 *
 *   POST /insights/{id}/feedback  — officer feedback (§17.5), any analyst
 *   POST /insights/{id}/approve   — lifecycle approval (§10), role-gated (T2)
 *
 * Both invalidate the insight feed on success so a card's lifecycle badge and
 * the feeds reflect the new state without a manual refetch. Role-gating of
 * approval is enforced by the UI (RequireRole / disabled action) AND by the
 * backend policy engine (§20) — the mutation itself never assumes authority.
 */
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { rejectUnavailable } from "@/api/unavailable";

/** §17.5 officer feedback payload. */
export interface InsightFeedback {
  /** Directional signal — the minimum §17.5 records. */
  rating: "useful" | "not_useful";
  comment?: string;
}

export function useInsightFeedback(insightId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (feedback: InsightFeedback) => {
      if (ENDPOINTS.insightFeedback === null) rejectUnavailable("Insight feedback");
      const { data } = await apiFetch<{ ok: true }>(
        ENDPOINTS.insightFeedback(insightId),
        { method: "POST", body: feedback },
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["insights"] });
    },
  });
}

export function useInsightApproval(insightId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      if (ENDPOINTS.insightApprove === null) rejectUnavailable("Insight approval");
      const { data } = await apiFetch<{ ok: true }>(
        ENDPOINTS.insightApprove(insightId),
        { method: "POST" },
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["insights"] });
    },
  });
}
