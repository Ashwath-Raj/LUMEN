/**
 * `LifecycleBadge` — the §10 intelligence-lifecycle state on an insight
 * (Generated → Verified → Approved → Operational → Expired → Archived → Deleted).
 *
 * The state carries governance meaning (§10, §11 gate 6): `verified` is machine-
 * checked but "unverified by human"; `approved` means a District SP / State
 * Analyst signed off (T2) — this is where P3 becomes auditable. The badge labels
 * each state plainly; `approved`/`operational` read as signal (human-reviewed),
 * `expired`/`archived` as muted. Only surfaceable states are expected here —
 * `generated`/`deleted` never reach the client (§10), but are labelled for
 * completeness so an unexpected value never renders blank.
 */
import { Badge } from "@/design/primitives/Badge";
import type { LifecycleState } from "@/types/contracts";

interface LifecycleBadgeProps {
  state: LifecycleState;
}

const LABEL: Record<LifecycleState, string> = {
  generated: "Generated",
  verified: "Verified · unverified by human",
  approved: "Approved",
  operational: "Operational",
  expired: "Expired",
  archived: "Archived",
  deleted: "Deleted",
};

/** States that indicate human review — rendered in signal tone (§10, §11). */
const REVIEWED: ReadonlySet<LifecycleState> = new Set([
  "approved",
  "operational",
]);

export function LifecycleBadge({ state }: LifecycleBadgeProps) {
  return (
    <Badge
      tone={REVIEWED.has(state) ? "var(--signal)" : undefined}
      title={`Lifecycle state: ${LABEL[state]} (§10)`}
    >
      {LABEL[state]}
    </Badge>
  );
}
