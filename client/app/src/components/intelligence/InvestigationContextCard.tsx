/**
 * `InvestigationContextCard` — the active investigation context (Part 1 left
 * panel / Part 5 investigation memory): selected case, persons, district scope,
 * and the session's investigation timeline (what was asked/pinned, in order).
 * The SELECTION lives in the URL (restorable/shareable); this card renders and
 * edits it. District scope feeds the REAL `/ai/ask` `district_scope` param.
 */
import type { ReactNode } from "react";
import { X } from "lucide-react";

import { Panel } from "@/design/primitives";
import { cn } from "@/utils/cn";

export interface ContextItem {
  id: string;
  label: string;
  sublabel?: string;
}

interface InvestigationContextCardProps {
  caseId: string | null;
  onClearCase: () => void;
  persons: ContextItem[];
  onRemovePerson: (id: string) => void;
  districts: ContextItem[];
  onRemoveDistrict: (id: string) => void;
  /** Session activity, oldest first: asked questions + pins. */
  timeline: Array<{ at: string; label: string }>;
}

function Group({
  title,
  children,
  empty,
}: {
  title: string;
  children?: ReactNode;
  empty?: string;
}) {
  return (
    <section className="flex flex-col gap-1.5">
      <h3 className="text-caption uppercase tracking-wide text-ink-muted">
        {title}
      </h3>
      {children ?? <p className="text-caption text-ink-faint">{empty}</p>}
    </section>
  );
}

function Chip({
  label,
  sublabel,
  onRemove,
}: ContextItem & { onRemove: () => void }) {
  return (
    <span
      className={cn(
        "inline-flex max-w-full items-center gap-1.5 rounded border border-line",
        "bg-raised/50 px-2 py-1 text-caption text-ink-primary",
      )}
    >
      <span className="truncate">{label}</span>
      {sublabel ? <span className="shrink-0 text-ink-faint">{sublabel}</span> : null}
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Remove ${label} from context`}
        className="shrink-0 text-ink-faint hover:text-ink-primary"
      >
        <X size={11} />
      </button>
    </span>
  );
}

export function InvestigationContextCard({
  caseId,
  onClearCase,
  persons,
  onRemovePerson,
  districts,
  onRemoveDistrict,
  timeline,
}: InvestigationContextCardProps) {
  return (
    <Panel className="flex flex-col gap-4 p-3">
      <Group title="Active case" empty={caseId ? undefined : "No case in context. Open one from the registry or a workspace link."}>
        {caseId ? (
          <Chip id={caseId} label={`Case ${caseId}`} onRemove={onClearCase} />
        ) : undefined}
      </Group>

      <Group
        title={`Persons (${persons.length})`}
        empty={persons.length ? undefined : "No persons selected."}
      >
        {persons.length ? (
          <div className="flex flex-wrap gap-1.5">
            {persons.map((p) => (
              <Chip key={p.id} {...p} onRemove={() => onRemovePerson(p.id)} />
            ))}
          </div>
        ) : undefined}
      </Group>

      <Group
        title={`District scope (${districts.length})`}
        empty={districts.length ? undefined : "Statewide — no district scope."}
      >
        {districts.length ? (
          <div className="flex flex-wrap gap-1.5">
            {districts.map((d) => (
              <Chip key={d.id} {...d} onRemove={() => onRemoveDistrict(d.id)} />
            ))}
          </div>
        ) : undefined}
      </Group>

      <Group
        title="Investigation timeline"
        empty={timeline.length ? undefined : "Session activity appears here."}
      >
        {timeline.length ? (
          <ol className="flex flex-col gap-1">
            {timeline.map((entry, i) => (
              <li key={i} className="flex items-baseline gap-2 text-caption">
                <span className="shrink-0 font-mono text-ink-faint">
                  {entry.at.slice(11, 19)}
                </span>
                <span className="min-w-0 truncate text-ink-muted">
                  {entry.label}
                </span>
              </li>
            ))}
          </ol>
        ) : undefined}
      </Group>
    </Panel>
  );
}
