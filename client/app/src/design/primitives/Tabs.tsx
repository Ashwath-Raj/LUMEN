/**
 * `Tabs` — a controlled, accessible tablist primitive. The active tab is owned by
 * the caller (the Case Workspace keeps it in the URL, §C "selected tab
 * serializes to query params"), so this component only renders the tablist and
 * calls back. Content is rendered by the caller (a single active panel), which
 * keeps each tab's data-fetching lazy.
 *
 * A11y: role="tablist"/"tab" with aria-selected, roving arrow-key focus
 * (←/→ move, Home/End jump), and aria-controls wiring left to the caller's
 * panel id. Matches §F focus behaviour.
 */
import { useRef, type KeyboardEvent } from "react";

import { cn } from "@/utils/cn";

export interface TabItem {
  id: string;
  label: string;
}

interface TabsProps {
  tabs: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  /** Prefix for aria ids, so panels can set aria-labelledby={`${idBase}-${id}`}. */
  idBase?: string;
}

export function Tabs({ tabs, activeId, onChange, idBase = "tab" }: TabsProps) {
  const refs = useRef<Record<string, HTMLButtonElement | null>>({});

  function onKeyDown(e: KeyboardEvent) {
    const index = tabs.findIndex((t) => t.id === activeId);
    if (index === -1) return;
    let next = index;
    if (e.key === "ArrowRight") next = (index + 1) % tabs.length;
    else if (e.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = tabs.length - 1;
    else return;
    e.preventDefault();
    const id = tabs[next].id;
    onChange(id);
    refs.current[id]?.focus();
  }

  return (
    <div
      role="tablist"
      aria-label="Workspace sections"
      onKeyDown={onKeyDown}
      className="flex items-center gap-1 border-b border-line"
    >
      {tabs.map((tab) => {
        const active = tab.id === activeId;
        return (
          <button
            key={tab.id}
            ref={(el) => {
              refs.current[tab.id] = el;
            }}
            role="tab"
            id={`${idBase}-${tab.id}`}
            aria-selected={active}
            aria-controls={`${idBase}-panel-${tab.id}`}
            tabIndex={active ? 0 : -1}
            onClick={() => onChange(tab.id)}
            className={cn(
              "-mb-px border-b-2 px-4 py-2 text-body transition-colors duration-DEFAULT ease-ease",
              active
                ? "border-signal text-ink-primary"
                : "border-transparent text-ink-muted hover:text-ink-primary",
            )}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
