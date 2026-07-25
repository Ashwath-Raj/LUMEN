/**
 * Activity tab (E.4, §21) — the read-only access audit log for this case: time,
 * actor, action, target (+ reason where recorded, e.g. policy denials). No
 * editing (§21 append-only; prompt "Read only"). Paginated via the shared
 * Pagination primitive.
 *
 * A role below Auditor may receive SCOPE_DENIED from `/audit`; `QueryBoundary`
 * renders that as the calm governance notice — an expected state, not a failure.
 */
import { useState } from "react";

import { useCaseActivity } from "@/api";
import { QueryBoundary } from "@/components/states";
import { DataGrid, Pagination, type Column } from "@/design/primitives";
import type { ActivityEntry } from "@/types/timeline";

const PAGE = 25;

const COLUMNS: Column<ActivityEntry>[] = [
  {
    key: "occurred_at",
    header: "Time",
    render: (a) => (
      <span className="font-mono text-ink-muted">
        {a.occurred_at.slice(0, 19).replace("T", " ")}
      </span>
    ),
  },
  {
    key: "actor",
    header: "Actor",
    render: (a) => <span className="text-ink-muted">{a.actor}</span>,
  },
  {
    key: "action",
    header: "Action",
    render: (a) => <span className="text-ink-primary">{a.action}</span>,
  },
  {
    key: "target",
    header: "Target",
    render: (a) => <span className="font-mono text-ink-muted">{a.target}</span>,
  },
  {
    key: "reason",
    header: "Reason",
    render: (a) => (
      <span className="text-ink-faint">{a.reason ?? "—"}</span>
    ),
  },
];

export function ActivityTab({ caseId }: { caseId: string }) {
  const [offset, setOffset] = useState(0);
  const activity = useCaseActivity(caseId, { limit: PAGE, offset });

  return (
    <div className="rounded border border-line bg-panel">
      <QueryBoundary
        query={activity}
        emptyMessage="No recorded access activity for this case yet."
        isEmpty={(data) => data.items.length === 0}
        skeletonLines={6}
      >
        {(data) => (
          <>
            <DataGrid<ActivityEntry>
              columns={COLUMNS}
              rows={data.items}
              rowKey={(a) => a.audit_id}
              caption="Case access audit log"
            />
            <Pagination
              total={data.total}
              limit={data.limit}
              offset={data.offset}
              onOffsetChange={setOffset}
            />
          </>
        )}
      </QueryBoundary>
    </div>
  );
}
