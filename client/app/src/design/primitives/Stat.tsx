/**
 * `Stat` — always clickable (arch §F primitives; §30.2 "every element is an
 * entry point"). A labelled figure that navigates. Never a decorative oversized
 * stat card (forbidden, §B).
 */
import type { ReactNode } from "react";

import { cn } from "@/utils/cn";

interface StatProps {
  label: string;
  value: ReactNode;
  onClick: () => void;
  hint?: string;
  className?: string;
}

export function Stat({ label, value, onClick, hint, className }: StatProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex w-full flex-col items-start gap-1 rounded border border-line",
        "bg-panel px-4 py-3 text-left transition-colors duration-DEFAULT ease-ease",
        "hover:border-signal/40 hover:bg-raised",
        className,
      )}
    >
      <span className="text-caption uppercase tracking-wide text-ink-muted">
        {label}
      </span>
      <span className="font-display text-panel-title text-ink-primary">
        {value}
      </span>
      {hint ? <span className="text-caption text-ink-faint">{hint}</span> : null}
    </button>
  );
}
