/**
 * `Badge` — the shared pill primitive every trust/quality/lifecycle badge is
 * built from, so pill markup (border, radius, caption type, 12px min) lives in
 * ONE place (quality req: no duplicated UI logic). Colour is supplied by the
 * caller as a token var; the badge never hard-codes a colour (§31.2).
 *
 * A11y (§F): risk/confidence/quality bands never rely on colour alone — callers
 * always pass label text, and `tone` only tints the border/text of that text.
 */
import type { ReactNode } from "react";

import { cn } from "@/utils/cn";

interface BadgeProps {
  children: ReactNode;
  /** A design-token colour var, e.g. `var(--risk-high)`. Tints border + text. */
  tone?: string;
  /** Optional leading glyph/icon (already sized by the caller). */
  icon?: ReactNode;
  /** Neutral badge uses --line/--ink-muted; set false only via `tone`. */
  className?: string;
  title?: string;
}

export function Badge({ children, tone, icon, className, title }: BadgeProps) {
  return (
    <span
      title={title}
      className={cn(
        "inline-flex items-center gap-1 rounded border px-2 py-0.5",
        "text-caption leading-caption",
        !tone && "border-line text-ink-muted",
        className,
      )}
      style={
        tone
          ? {
              // Token-driven; color-mix keeps the fill subtle while the text/
              // border carry the band colour (one accent per region, §31.2).
              borderColor: `color-mix(in srgb, ${tone} 50%, transparent)`,
              color: tone,
            }
          : undefined
      }
    >
      {icon}
      {children}
    </span>
  );
}
