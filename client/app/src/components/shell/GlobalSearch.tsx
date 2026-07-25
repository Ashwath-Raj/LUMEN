/**
 * `GlobalSearch` — the ⌘K command palette trigger + shell (arch §D shell). The
 * palette resolves CrimeNo → /case, names → person/officer, districts → /geo
 * (backed by `GET /cases?q=` + semantic search) — that RESOLUTION is a later
 * session once those endpoints are wired. Session 1 ships the full interaction:
 * the trigger button, the ⌘K/Ctrl-K global shortcut, the modal overlay (Esc
 * closes, autofocused input, click-outside closes), and an instructional empty
 * state. Later sessions add the query + result list only.
 *
 * The overlay is a real modal (role="dialog", aria-modal, focus moved to the
 * input) so it is accessible from the start.
 */
import { useEffect, useRef, useState } from "react";
import { Search } from "lucide-react";

import { Panel, EmptyState } from "@/design/primitives";

export function GlobalSearch() {
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // ⌘K / Ctrl-K opens the palette from anywhere (§D shell).
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(true);
      } else if (e.key === "Escape") {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="flex flex-1 items-center gap-2 rounded border border-line bg-void px-3 py-2 text-caption text-ink-faint hover:border-signal/40"
        aria-label="Search cases, people, districts (Command K)"
        aria-haspopup="dialog"
      >
        <Search size={16} />
        <span>Search cases, people, districts…</span>
        <kbd className="ml-auto font-mono text-caption text-ink-faint">⌘K</kbd>
      </button>

      {open ? (
        <div
          className="fixed inset-0 z-overlay flex items-start justify-center bg-void/70 pt-[15vh]"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) setOpen(false);
          }}
        >
          <Panel
            elevated
            role="dialog"
            aria-modal="true"
            aria-label="Command palette"
            className="w-full max-w-xl"
          >
            <div className="flex items-center gap-2 border-b border-line px-4 py-3">
              <Search size={16} className="text-ink-faint" aria-hidden />
              <input
                ref={inputRef}
                type="text"
                placeholder="Search CrimeNo, person, officer, district…"
                className="flex-1 bg-transparent text-body text-ink-primary outline-none placeholder:text-ink-faint"
              />
              <kbd className="font-mono text-caption text-ink-faint">Esc</kbd>
            </div>
            <EmptyState message="Search is wired in a later session. It will resolve a CrimeNo to its case, a name to a person or officer, and a district to the map." />
          </Panel>
        </div>
      ) : null}
    </>
  );
}
