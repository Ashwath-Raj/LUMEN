/**
 * `ConfidenceMeter` (D2) — the band-coloured composite meter (§9). Confidence is
 * never a bare number: the meter shows the band LABEL (High/Moderate/Low), the
 * value, and — when low — the limiting-component sentence inline, de-emphasised
 * per §9 ("Low-confidence insights render in a de-emphasised state with the
 * weakest component named").
 *
 * A confidence value may not appear without its breakdown (§A). This meter is
 * therefore the click target that opens `ConfidenceBreakdown`; a value passed
 * without a breakdown is a type error at the call site (the `InsightCard` always
 * has one from §8).
 */
import { ChevronDown, ChevronRight } from "lucide-react";

import { Bar } from "./Bar";
import { limitingSentence } from "./confidence";
import {
  CONFIDENCE_TOKEN,
  confidenceBand,
  type ConfidenceBand,
} from "@/design/tokens";
import type { ConfidenceBreakdown } from "@/types/contracts";
import { cn } from "@/utils/cn";

interface ConfidenceMeterProps {
  breakdown: ConfidenceBreakdown;
  /** When provided, the meter is a button that toggles the breakdown. */
  onToggle?: () => void;
  /** Whether the breakdown is currently expanded (drives the chevron + aria). */
  expanded?: boolean;
}

const BAND_LABEL: Record<ConfidenceBand, string> = {
  high: "High",
  moderate: "Moderate",
  low: "Low",
};

export function ConfidenceMeter({
  breakdown,
  onToggle,
  expanded = false,
}: ConfidenceMeterProps) {
  const composite = breakdown.composite;
  const band = confidenceBand(composite);
  const tone = CONFIDENCE_TOKEN[band];
  const low = band === "low";

  const body = (
    <div className={cn("flex w-full flex-col gap-1", low && "opacity-90")}>
      <div className="flex items-center gap-2">
        {onToggle ? (
          expanded ? (
            <ChevronDown size={14} className="text-ink-faint" aria-hidden />
          ) : (
            <ChevronRight size={14} className="text-ink-faint" aria-hidden />
          )
        ) : null}
        <span className="text-caption uppercase tracking-wide text-ink-muted">
          Confidence
        </span>
        <span className="text-caption font-medium" style={{ color: tone }}>
          {BAND_LABEL[band]}
        </span>
        <span className="ml-auto font-mono text-caption text-ink-muted">
          {composite.toFixed(2)}
        </span>
      </div>
      <Bar label="composite" value={composite} tone={tone} />
      {low ? (
        <p className="text-caption text-ink-faint">{limitingSentence(breakdown)}</p>
      ) : null}
    </div>
  );

  if (!onToggle) return body;

  return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={expanded}
      className="flex w-full items-start rounded text-left hover:bg-raised"
    >
      {body}
    </button>
  );
}
