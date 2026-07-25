/**
 * Assignment panel  — who is assigned to this case: the investigating
 * officer and the registering officer, from `CaseDetail.officers` (§2.1 Officer).
 * Each officer opens in the InspectorPanel (no navigation away) and links to
 * their caseload (`/cases?officer=…`).
 *
 * READ-ONLY: §29.1 exposes no assignment-mutation endpoint, and inventing one is
 * out of bounds (never invent backend contracts). Reassignment is a governed,
 * audited action (§20) that lands with its endpoint; the panel states that
 * rather than offering a control the backend can't honour.
 */
import { UserPlus } from "lucide-react";

import { EntityCard, type EntityRef } from "@/components/entity";
import { Panel } from "@/design/primitives";
import type { CaseDetail } from "@/types/case";

import { officerRefs } from "./caseEntities";

interface AssignmentPanelProps {
  detail: CaseDetail;
  onSelect: (ref: EntityRef) => void;
  selectedId: string | null;
}

export function AssignmentPanel({
  detail,
  onSelect,
  selectedId,
}: AssignmentPanelProps) {
  const officers = officerRefs(detail);
  const io = officers.find(
    (o) => o.fields?.some((f) => f.value === "Investigating officer"),
  );
  const others = officers.filter((o) => o !== io);

  return (
    <section aria-label="Assignment" className="flex flex-col gap-2">
      <h3 className="text-caption uppercase tracking-wide text-ink-muted">
        Assignment
      </h3>

      {officers.length === 0 ? (
        <Panel className="flex items-center gap-2 p-4 text-caption text-ink-muted">
          <UserPlus size={16} strokeWidth={1.5} className="text-ink-faint" aria-hidden />
          No officer is assigned to this case.
        </Panel>
      ) : (
        <div className="flex flex-col gap-3">
          {io ? (
            <div className="flex flex-col gap-1">
              <span className="text-caption text-ink-faint">
                Investigating officer
              </span>
              <EntityCard
                entity={io}
                variant="full"
                onSelect={onSelect}
                selected={selectedId === io.id}
              />
            </div>
          ) : null}

          {others.length ? (
            <div className="flex flex-col gap-1">
              <span className="text-caption text-ink-faint">Other officers</span>
              <div className="flex flex-col gap-2">
                {others.map((o) => (
                  <EntityCard
                    key={o.id}
                    entity={o}
                    onSelect={onSelect}
                    selected={selectedId === o.id}
                  />
                ))}
              </div>
            </div>
          ) : null}
        </div>
      )}

      <p className="text-caption text-ink-faint">
        Reassignment is a governed, audited action (§20) — available when its
        endpoint is served.
      </p>
    </section>
  );
}
