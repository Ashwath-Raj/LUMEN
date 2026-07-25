/**
 * Insight lifecycle mutations — LUMEN_MASTER_SPEC_V3 §29.1, §10, §17.5.
 *
 *   POST /insights/{id}/feedback  — §17.5 "thumbs up/down plus optional reason",
 *                                   written to `lumen_event` as
 *                                   `InsightFeedbackGiven`
 *   POST /insights/{id}/approve   — §10 approval, recorded with approver and
 *                                   timestamp; District SP / State Analyst only
 *
 * Approval legitimately REFUSES when §10's entry checks fail — most often the
 * 0.35 confidence floor ("the insight stays `generated` and never surfaces").
 * That refusal arrives as a 409 and is surfaced verbatim, because it is the
 * specification working rather than a fault.
 */
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { rejectUnavailable } from "@/api/unavailable";

/** §17.5 officer feedback. */
export interface InsightFeedback {
  rating: "up" | "down";
  reason?: string;
  actor_id?: string;
}

export function useInsightFeedback(insightId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (feedback: InsightFeedback) => {
      if (ENDPOINTS.insightFeedback === null) rejectUnavailable("Insight feedback");
      const { data } = await apiFetch<{ event_id: string }>(
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

export interface ApproveRequest {
  approver: string;
  role: string;
}

export function useInsightApproval(insightId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (request: ApproveRequest) => {
      if (ENDPOINTS.insightApprove === null) rejectUnavailable("Insight approval");
      const { data } = await apiFetch<{ lifecycle_state: string }>(
        ENDPOINTS.insightApprove(insightId),
        { method: "POST", body: request },
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["insights"] });
    },
  });
}
