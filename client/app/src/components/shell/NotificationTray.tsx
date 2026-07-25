/**
 * `NotificationTray` — the shell notification tray (arch §D shell). The live
 * feed (AnomalyDetected events → `/anomalies`) is wired in a later session with
 * the event bus (§19); Session 1 ships the tray as a functional placeholder: a
 * toggle button with an unread indicator slot and a dropdown that shows an
 * explicit empty state (never a bare, broken menu).
 *
 * It is a real disclosure (open/close, Esc closes, click-outside closes, aria)
 * so later sessions only add data, not behaviour.
 */
import { useEffect, useRef, useState } from "react";
import { Bell } from "lucide-react";

import { Panel, EmptyState } from "@/design/primitives";
import { cn } from "@/utils/cn";

export function NotificationTray() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDocClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label="Notifications"
        aria-haspopup="menu"
        aria-expanded={open}
        className={cn(
          "text-ink-muted hover:text-ink-primary",
          open && "text-signal",
        )}
      >
        <Bell size={20} strokeWidth={1.5} />
      </button>

      {open ? (
        <Panel
          elevated
          role="menu"
          aria-label="Notifications"
          className="absolute right-0 top-full z-overlay mt-2 w-80"
        >
          <div className="border-b border-line px-4 py-2 text-caption uppercase tracking-wide text-ink-muted">
            Notifications
          </div>
          <EmptyState message="No notifications. Anomaly alerts will appear here." />
        </Panel>
      ) : null}
    </div>
  );
}
