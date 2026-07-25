/**
 * Status panel (Session 2) — the case's current status (§3.5 CaseStatusMaster)
 * and where it sits in the investigation lifecycle (§2.1 ProcessEvent stages:
 * incident → info received → registered → arrest → chargesheet). The stage is
 * derived from the timeline (the latest recorded event), so it reflects the
 * real events, never an invented one.
 *
 * READ-ONLY: §29.1 exposes no status-transition endpoint; changing status is a
 * governed, audited action (§20/§10) that lands with its endpoint. The panel
 * shows the current standing and the ordered lifecycle for context.
 */
import { Check, Circle } from "lucide-react";

import { useCaseTimeline } from "@/api";
import { Badge, Panel } from "@/design/primitives";
import type { CaseDetail } from "@/types/case";
import type { TimelineEventKind } from "@/types/timeline";
import { cn } from "@/utils/cn";

const STAGE_ORDER: TimelineEventKind[] = [
  "incident",
  "info_received",
  "registered",
  "arrest",
  "chargesheet",
];

const STAGE_LABEL: Record<TimelineEventKind, string> = {
  incident: "Incident",
  info_received: "Information received",
  registered: "Registered",
  arrest: "Arrest",
  chargesheet: "Chargesheet",
};

export function StatusPanel({ detail }: { detail: CaseDetail }) {
  const timeline = useCaseTimeline(detail.case_master_id);

  const reached = new Set<TimelineEventKind>(
    (timeline.data?.events ?? []).map((e) => e.kind),
  );
  // Current stage = furthest reached in the ordered lifecycle.
  const currentIndex = STAGE_ORDER.reduce(
    (max, stage, i) => (reached.has(stage) ? i : max),
    -1,
  );

  return (
    <section aria-label="Status" className="flex flex-col gap-2">
      <h3 className="text-caption uppercase tracking-wide text-ink-muted">
        Status
      </h3>

      <Panel className="flex flex-col gap-3 p-4">
        <div className="flex items-center gap-2">
          <span className="text-body text-ink-primary">{detail.status.name}</span>
          <Badge>{detail.gravity.name}</Badge>
        </div>

        <ol className="flex flex-col gap-1.5 border-t border-line pt-3">
          {STAGE_ORDER.map((stage, i) => {
            const done = i <= currentIndex;
            const current = i === currentIndex;
            return (
              <li key={stage} className="flex items-center gap-2 text-caption">
                {done ? (
                  <Check size={14} className="text-signal" aria-hidden />
                ) : (
                  <Circle size={14} className="text-ink-faint" aria-hidden />
                )}
                <span
                  className={cn(
                    done ? "text-ink-primary" : "text-ink-faint",
                    current && "font-medium text-signal",
                  )}
                >
                  {STAGE_LABEL[stage]}
                </span>
                {current ? (
                  <span className="text-ink-faint">· current</span>
                ) : null}
              </li>
            );
          })}
        </ol>
      </Panel>

      <p className="text-caption text-ink-faint">
        Status transitions are governed and audited (§10, §20) — available when
        the transition endpoint is served.
      </p>
    </section>
  );
}
