/**
 * Overview tab (E.4) — the analyst's at-a-glance summary of one case:
 *   • Entity summary  — case identity + core metadata + brief facts
 *   • Assignment      — investigating / registering officers (read-only, §29.1)
 *   • Status          — current status + lifecycle stage (read-only, §29.1)
 *   • Related people  — participants (masked per §4.2 where applicable)
 *   • Linked location — the station/unit
 *   • Charges         — acts & sections
 *   • Recent activity — last few §21 audit entries
 *
 * Assembled from the already-loaded `CaseDetail` (no re-fetch) plus a small
 * recent-activity peek. Entities open in the InspectorPanel via `onSelect`
 * (no navigation away, D10). Every entity is an `EntityCard`; the activity block
 * degrades independently through its own QueryBoundary.
 */
import type { ReactNode } from "react";

import { useCaseActivity } from "@/api";
import { EntityCard, type EntityRef } from "@/components/entity";
import { QueryBoundary } from "@/components/states";
import { QualityBadge, RiskBand } from "@/components/trust";
import { Panel } from "@/design/primitives";
import type { CaseDetail } from "@/types/case";

import { AssignmentPanel } from "../AssignmentPanel";
import { StatusPanel } from "../StatusPanel";
import { chargeRefs, participantRefs, stationRef } from "../caseEntities";

interface OverviewTabProps {
  detail: CaseDetail;
  onSelect: (ref: EntityRef) => void;
  selectedId: string | null;
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-2">
      <h3 className="text-caption uppercase tracking-wide text-ink-muted">
        {title}
      </h3>
      {children}
    </section>
  );
}

export function OverviewTab({ detail, onSelect, selectedId }: OverviewTabProps) {
  const activity = useCaseActivity(detail.case_master_id, { limit: 5 });

  const people = participantRefs(detail);
  const charges = chargeRefs(detail);
  const station = stationRef(detail);

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
      {/* Entity summary — case identity + metadata */}
      <Section title="Entity summary">
        <Panel className="flex flex-col gap-3 p-4">
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-caption">
            <dt className="text-ink-faint">Crime no</dt>
            <dd className="font-mono text-ink-muted">{detail.crime_no}</dd>
            <dt className="text-ink-faint">Crime type</dt>
            <dd className="text-ink-muted">
              {detail.crime_type.head_name}
              {detail.crime_type.sub_head_name
                ? ` · ${detail.crime_type.sub_head_name}`
                : ""}
            </dd>
            <dt className="text-ink-faint">Gravity</dt>
            <dd className="text-ink-muted">{detail.gravity.name}</dd>
            <dt className="text-ink-faint">Court</dt>
            <dd className="text-ink-muted">{detail.court?.court_name ?? "—"}</dd>
            <dt className="text-ink-faint">People</dt>
            <dd className="text-ink-muted">{detail.participants.length}</dd>
            <dt className="text-ink-faint">Charges</dt>
            <dd className="text-ink-muted">{detail.charges.length}</dd>
          </dl>
          <div className="flex flex-wrap items-center gap-2 border-t border-line pt-3">
            {detail.risk_band ? (
              <RiskBand
                band={detail.risk_band}
                score={detail.risk_score ?? undefined}
                showScore
              />
            ) : (
              <span className="text-caption text-ink-faint">
                No risk insight yet
              </span>
            )}
            {detail.quality_score !== null ? (
              <QualityBadge score={detail.quality_score} />
            ) : null}
          </div>
          {detail.brief_facts ? (
            <p className="border-t border-line pt-3 text-caption text-ink-muted">
              {detail.brief_facts}
            </p>
          ) : null}
        </Panel>
      </Section>

      <StatusPanel detail={detail} />

      <AssignmentPanel
        detail={detail}
        onSelect={onSelect}
        selectedId={selectedId}
      />

      <Section title="Related people">
        {people.length ? (
          <div className="flex flex-col gap-2">
            {people.map((p) => (
              <EntityCard
                key={p.id}
                entity={p}
                onSelect={onSelect}
                selected={selectedId === p.id}
              />
            ))}
          </div>
        ) : (
          <p className="text-caption text-ink-faint">
            No participants recorded on this case.
          </p>
        )}
      </Section>

      <Section title="Linked location">
        <EntityCard
          entity={station}
          onSelect={onSelect}
          selected={selectedId === station.id}
        />
      </Section>

      {charges.length ? (
        <Section title="Charges">
          <div className="flex flex-col gap-2">
            {charges.map((c) => (
              <EntityCard
                key={c.id}
                entity={c}
                onSelect={onSelect}
                selected={selectedId === c.id}
              />
            ))}
          </div>
        </Section>
      ) : null}

      <Section title="Recent activity">
        <Panel className="p-2">
          <QueryBoundary
            query={activity}
            emptyMessage="No recorded access activity for this case yet."
            isEmpty={(data) => data.items.length === 0}
            skeletonLines={3}
          >
            {(data) => (
              <ul className="flex flex-col divide-y divide-line/60">
                {data.items.map((entry) => (
                  <li
                    key={entry.audit_id}
                    className="flex items-baseline gap-2 px-2 py-1.5 text-caption"
                  >
                    <span className="font-mono text-ink-faint">
                      {entry.occurred_at.slice(0, 16).replace("T", " ")}
                    </span>
                    <span className="text-ink-muted">{entry.actor}</span>
                    <span className="text-ink-primary">{entry.action}</span>
                  </li>
                ))}
              </ul>
            )}
          </QueryBoundary>
        </Panel>
      </Section>
    </div>
  );
}
