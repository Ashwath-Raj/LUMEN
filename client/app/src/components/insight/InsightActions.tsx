/**
 * `InsightActions` (part of D1) — the card's footer: officer feedback (§17.5,
 * any analyst) and role-gated lifecycle approval (§10, T2 — District SP or State
 * Analyst only). Approval is where P3 (human review) becomes auditable (§10,§11
 * gate 6).
 *
 * The approve control is HIDDEN, not merely disabled, for roles without
 * authority (§20) and is absent once the insight is already approved/operational
 * — the UI never offers an action the policy engine will reject. Feedback and
 * approval each surface their own pending/error state inline; a failure here
 * never crashes the card.
 */
import type { ReactNode } from "react";
import { ThumbsUp, ThumbsDown, Check, Loader2 } from "lucide-react";

import { Button } from "@/design/primitives";
import { useInsightApproval, useInsightFeedback } from "@/api";
import { useSession } from "@/providers/sessionContext";
import type { LifecycleState, Role } from "@/types";
import { cn } from "@/utils/cn";

interface InsightActionsProps {
  insightId: string;
  lifecycleState: LifecycleState;
}

/** §10: only these roles may approve (T2). */
const APPROVER_ROLES: ReadonlySet<Role> = new Set([
  "district_sp",
  "state_analyst",
]);

const ALREADY_APPROVED: ReadonlySet<LifecycleState> = new Set([
  "approved",
  "operational",
]);

export function InsightActions({
  insightId,
  lifecycleState,
}: InsightActionsProps) {
  const { role, operator } = useSession();
  const feedback = useInsightFeedback(insightId);
  const approval = useInsightApproval(insightId);

  const canApprove =
    role !== null &&
    APPROVER_ROLES.has(role) &&
    !ALREADY_APPROVED.has(lifecycleState);

  return (
    <div className="flex flex-wrap items-center gap-2 border-t border-line pt-2">
      <span className="text-caption uppercase tracking-wide text-ink-faint">
        Feedback
      </span>

      <FeedbackButton
        label="Useful"
        icon={<ThumbsUp size={14} strokeWidth={1.5} aria-hidden />}
        active={feedback.data !== undefined && feedback.variables?.rating === "up"}
        pending={feedback.isPending && feedback.variables?.rating === "up"}
        onClick={() => feedback.mutate({ rating: "up" })}
      />
      <FeedbackButton
        label="Not useful"
        icon={<ThumbsDown size={14} strokeWidth={1.5} aria-hidden />}
        active={
          feedback.data !== undefined && feedback.variables?.rating === "down"
        }
        pending={feedback.isPending && feedback.variables?.rating === "down"}
        onClick={() => feedback.mutate({ rating: "down" })}
      />

      {canApprove ? (
        <Button
          variant="primary"
          className="ml-auto"
          onClick={() =>
            approval.mutate({
              approver: operator?.name ?? operator?.id ?? "unknown",
              role: role ?? "station_officer",
            })
          }
          disabled={approval.isPending}
        >
          {approval.isPending ? (
            <Loader2 size={14} className="animate-spin" aria-hidden />
          ) : (
            <Check size={14} strokeWidth={1.5} aria-hidden />
          )}
          Approve
        </Button>
      ) : null}

      {feedback.isError ? (
        <span className="w-full text-caption text-risk-high">
          Couldn’t record feedback — try again.
        </span>
      ) : null}
      {approval.isError ? (
        // A §10 entry-check refusal (e.g. the 0.35 confidence floor) is the
        // specification working — it is reported as a governance notice with
        // the reason, not as a failure.
        <span className="w-full text-caption text-degraded">
          Not approvable — {approval.error.message}
        </span>
      ) : null}
      {approval.isSuccess ? (
        <span className="w-full text-caption text-confidence-high">
          Approved and recorded (§10).
        </span>
      ) : null}
    </div>
  );
}

function FeedbackButton({
  label,
  icon,
  active,
  pending,
  onClick,
}: {
  label: string;
  icon: ReactNode;
  active: boolean;
  pending: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={pending}
      aria-pressed={active}
      aria-label={label}
      className={cn(
        "inline-flex items-center gap-1 rounded border px-2 py-1 text-caption",
        "transition-colors duration-DEFAULT ease-ease disabled:opacity-50",
        active
          ? "border-signal/50 text-signal"
          : "border-line text-ink-muted hover:border-signal/40 hover:text-ink-primary",
      )}
    >
      {pending ? <Loader2 size={14} className="animate-spin" aria-hidden /> : icon}
      {label}
    </button>
  );
}
