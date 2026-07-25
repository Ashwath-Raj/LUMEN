/**
 * `Panel` — the level-0 surface primitive (arch §F elevation): bg-panel, 1px
 * --line border, no shadow. Floating panels add `elevated` for the single
 * level-1 shadow. Every page region is a Panel.
 */
import type { HTMLAttributes } from "react";

import { cn } from "@/utils/cn";

interface PanelProps extends HTMLAttributes<HTMLDivElement> {
  /** Level-1 floating surface (inspector-overlay, ⌘K, tray, tooltip). */
  elevated?: boolean;
}

export function Panel({ elevated = false, className, ...rest }: PanelProps) {
  return (
    <div
      className={cn(
        "rounded border border-line bg-panel",
        elevated && "shadow-panel",
        className,
      )}
      {...rest}
    />
  );
}
