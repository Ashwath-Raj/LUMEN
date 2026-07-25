/**
 * `ConfidenceBreakdown` (D2) — the five §9 components as labelled bars, with the
 * limiting (weakest) component named and emphasised: *"limited by identity match
 * confidence (0.61)"*. This is what the composite meter expands into (§9, D2:
 * "click opens five labelled bars, limiting component named").
 *
 * Each component is coloured by its own band so a single weak link is visible at
 * a glance; the value text always accompanies the colour (§F a11y). The
 * multiplicative composite line closes the panel so the arithmetic is legible.
 */
import { Bar } from "./Bar";
import {
  CONFIDENCE_COMPONENTS,
  CONFIDENCE_LABEL,
  limitingFactor,
} from "./confidence";
import { CONFIDENCE_TOKEN, confidenceBand } from "@/design/tokens";
import type { ConfidenceBreakdown as Breakdown } from "@/types/contracts";

interface ConfidenceBreakdownProps {
  breakdown: Breakdown;
}

export function ConfidenceBreakdown({ breakdown }: ConfidenceBreakdownProps) {
  const limiting = limitingFactor(breakdown);
  return (
    <div className="flex flex-col gap-3" role="group" aria-label="Confidence breakdown">
      <div className="flex flex-col gap-2">
        {CONFIDENCE_COMPONENTS.map((key) => {
          const value = breakdown[key];
          const isLimiting = key === limiting.component;
          return (
            <Bar
              key={key}
              label={CONFIDENCE_LABEL[key]}
              value={value}
              tone={CONFIDENCE_TOKEN[confidenceBand(value)]}
              note={isLimiting ? "limiting" : undefined}
              emphasis={isLimiting}
            />
          );
        })}
      </div>
      <p className="border-t border-line pt-2 text-caption text-ink-faint">
        Composite is multiplicative (§9): a chain of inferences is only as strong
        as its weakest link — here,{" "}
        <span className="text-ink-muted">
          {limiting.label} ({limiting.value.toFixed(2)})
        </span>
        .
      </p>
    </div>
  );
}
