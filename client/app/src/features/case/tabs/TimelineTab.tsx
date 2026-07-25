/**
 * Timeline tab (E.4, §30.4) — the case's chronological investigation events
 * (§2.1 ProcessEvents): incident → info received → registered → arrest →
 * chargesheet. Supports expand/collapse per event, a kind filter, and entity
 * links; events are never invented — the list is exactly what
 * `GET /cases/{id}/timeline` returns.
 *
 * The district-median reference (§30.4) is shown as context. The full
 * gaps-to-scale visual rail (D7) builds on this in a later graph/geo session;
 * Session 2 delivers the chronological, filterable, linkable event list.
 */
import { useState } from "react";
import { ChevronDown, ChevronRight, ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";

import { useCaseTimeline } from "@/api";
import { QueryBoundary } from "@/components/states";
import { Panel } from "@/design/primitives";
import type { TimelineEvent, TimelineEventKind } from "@/types/timeline";
import { cn } from "@/utils/cn";

const KIND_LABEL: Record<TimelineEventKind, string> = {
  incident: "Incident",
  info_received: "Information received",
  registered: "Registered",
  arrest: "Arrest",
  chargesheet: "Chargesheet",
};

const KIND_ORDER: TimelineEventKind[] = [
  "incident",
  "info_received",
  "registered",
  "arrest",
  "chargesheet",
];

export function TimelineTab({ caseId }: { caseId: string }) {
  const timeline = useCaseTimeline(caseId);
  const [filter, setFilter] = useState<TimelineEventKind | "all">("all");

  return (
    <QueryBoundary
      query={timeline}
      emptyMessage="No timeline events recorded for this case."
      isEmpty={(data) => data.events.length === 0}
      skeletonLines={6}
    >
      {(data) => {
        const events =
          filter === "all"
            ? data.events
            : data.events.filter((e) => e.kind === filter);

        return (
          <div className="flex flex-col gap-4">
            <div className="flex flex-wrap items-center gap-2">
              <FilterChip
                label="All"
                active={filter === "all"}
                onClick={() => setFilter("all")}
              />
              {KIND_ORDER.map((kind) => (
                <FilterChip
                  key={kind}
                  label={KIND_LABEL[kind]}
                  active={filter === kind}
                  onClick={() => setFilter(kind)}
                />
              ))}
              {data.district_median_days !== null ? (
                <span className="ml-auto text-caption text-ink-faint">
                  District median: {data.district_median_days} days between stages
                </span>
              ) : null}
            </div>

            {events.length === 0 ? (
              <p className="text-caption text-ink-faint">
                No {filter === "all" ? "" : KIND_LABEL[filter as TimelineEventKind]}{" "}
                events.
              </p>
            ) : (
              <ol className="flex flex-col gap-2">
                {events.map((event) => (
                  <TimelineRow key={event.event_id} event={event} />
                ))}
              </ol>
            )}
          </div>
        );
      }}
    </QueryBoundary>
  );
}

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "rounded border px-2 py-1 text-caption transition-colors duration-DEFAULT ease-ease",
        active
          ? "border-signal/50 text-signal"
          : "border-line text-ink-muted hover:border-signal/40 hover:text-ink-primary",
      )}
    >
      {label}
    </button>
  );
}

function TimelineRow({ event }: { event: TimelineEvent }) {
  const [open, setOpen] = useState(false);

  return (
    <li>
      <Panel className="flex flex-col">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          className="flex items-center gap-2 px-3 py-2 text-left"
        >
          {open ? (
            <ChevronDown size={14} className="text-ink-faint" aria-hidden />
          ) : (
            <ChevronRight size={14} className="text-ink-faint" aria-hidden />
          )}
          <span className="text-caption uppercase tracking-wide text-signal">
            {KIND_LABEL[event.kind]}
          </span>
          <span className="font-mono text-caption text-ink-muted">
            {event.occurred_at ? event.occurred_at.slice(0, 10) : "date unknown"}
          </span>
          <span className="ml-auto truncate text-caption text-ink-muted">
            {event.station_name ?? ""}
          </span>
        </button>

        {open ? (
          <div className="flex flex-col gap-1 border-t border-line px-9 py-2 text-caption text-ink-muted">
            <p>{event.label}</p>
            {event.io_display_name ? <p>IO: {event.io_display_name}</p> : null}
            {event.chargesheet_type ? (
              <p>Chargesheet type: {event.chargesheet_type}</p>
            ) : null}
            {event.entity_url ? (
              <Link
                to={event.entity_url}
                className="inline-flex items-center gap-1 text-signal hover:underline"
              >
                Open linked entity
                <ArrowUpRight size={12} aria-hidden />
              </Link>
            ) : null}
          </div>
        ) : null}
      </Panel>
    </li>
  );
}
