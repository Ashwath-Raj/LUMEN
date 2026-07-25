/**
 * Time scrubber (§30.3 "bottom scrubber", §30.10 "re-query on release, not on
 * drag"). A range over the trailing 12 months; dragging updates the label
 * locally, and only RELEASE commits the new window (fires `onCommit`), which the
 * page turns into a `date_from` filter + fresh geo query.
 *
 * Read-only visual while dragging keeps the map from re-querying on every tick.
 */
import { useEffect, useState } from "react";

import { Panel } from "@/design/primitives";

interface TimeScrubberProps {
  /** Current committed window start (ISO date) or null for "all". */
  from: string | null;
  /** Commit a new window start (null clears it). */
  onCommit: (from: string | null) => void;
}

const MONTHS = 12;

/** Month options: index 0 = all time, 1..12 = "last N months". */
function labelFor(value: number): string {
  if (value === 0) return "All time";
  if (value === MONTHS) return "Last 12 months";
  return `Last ${value} month${value === 1 ? "" : "s"}`;
}

export function TimeScrubber({ from, onCommit }: TimeScrubberProps) {
  // Derive the slider position from the committed `from`, else "all".
  const [value, setValue] = useState<number>(from ? 6 : 0);

  useEffect(() => {
    if (!from) setValue(0);
  }, [from]);

  function commit(months: number) {
    if (months === 0) {
      onCommit(null);
      return;
    }
    // Compute the window start as "months ago" from today; date-only.
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth() - months, now.getDate());
    onCommit(start.toISOString().slice(0, 10));
  }

  return (
    <Panel elevated className="flex items-center gap-3 px-4 py-2">
      <span className="w-32 shrink-0 text-caption text-ink-muted">
        {labelFor(value)}
      </span>
      <input
        type="range"
        min={0}
        max={MONTHS}
        step={1}
        value={value}
        aria-label="Time range (commits on release)"
        onChange={(e) => setValue(Number(e.target.value))}
        onMouseUp={() => commit(value)}
        onKeyUp={() => commit(value)}
        onTouchEnd={() => commit(value)}
        className="flex-1 accent-signal"
      />
    </Panel>
  );
}
