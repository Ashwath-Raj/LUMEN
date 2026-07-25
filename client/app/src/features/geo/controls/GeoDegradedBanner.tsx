/**
 * Degraded banner (user brief) — when the live `/geo/*` intelligence is
 * unavailable (501 / error), the map + Karnataka boundaries stay visible and
 * this banner states "Live geographic intelligence unavailable." No table
 * replacement (that only happens if Leaflet itself fails to load — handled by
 * the page's error boundary).
 */
import { CloudOff } from "lucide-react";

export function GeoDegradedBanner({ detail }: { detail?: string }) {
  return (
    <div
      role="status"
      className="flex items-center gap-2 rounded border border-degraded/50 bg-panel/90 px-3 py-2 text-caption text-degraded backdrop-blur"
    >
      <CloudOff size={14} strokeWidth={1.5} aria-hidden />
      <span>
        Live geographic intelligence unavailable.
        {detail ? <span className="text-ink-faint"> {detail}</span> : null}
      </span>
    </div>
  );
}
