/**
 * `TrustBadge` (D12) — renders a §11 trust statement as a component DEFAULT, not
 * page content, so it can never be forgotten (§B: "Trust is rendered, not
 * claimed"). The statements and the kind→context mapping live in
 * `trustStatements.ts`; an `InsightCard` shows the right caveat by default via
 * `trustContextFor(insight.kind)` without per-card wiring.
 */
import { Info } from "lucide-react";

import { cn } from "@/utils/cn";
import { TRUST_STATEMENT, type TrustContext } from "./trustStatements";

interface TrustBadgeProps {
  context: TrustContext;
  /** Extra text appended after the statement, e.g. "Confidence 0.91." */
  suffix?: string;
  className?: string;
}

export function TrustBadge({ context, suffix, className }: TrustBadgeProps) {
  return (
    <p
      className={cn(
        "flex items-start gap-2 text-caption text-ink-muted",
        className,
      )}
      role="note"
    >
      <Info size={12} strokeWidth={1.5} className="mt-0.5 shrink-0" aria-hidden />
      <span>
        {TRUST_STATEMENT[context]}
        {suffix ? ` ${suffix}` : null}
      </span>
    </p>
  );
}
