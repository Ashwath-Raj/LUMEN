/**
 * `QualityBadge` (D12) — a §5.2 data-quality score (0–1) as a pill. Quality is
 * an intelligence product, not a defect list (§5.3): a badge shows the score for
 * a scope or a single dimension (completeness, validity, consistency, integrity,
 * uniqueness, timeliness).
 *
 * Higher is better, so the colour band is the confidence palette (green→amber→
 * grey), and the numeric score always accompanies the colour (§F a11y). Used in
 * the case header (`n findings`), the `/quality` grid, and lineage panels.
 */
import { Badge } from "@/design/primitives/Badge";
import { CONFIDENCE_TOKEN, confidenceBand } from "@/design/tokens";

/** The six §5.2 dimensions (label is optional context on the badge). */
export type QualityDimension =
  | "completeness"
  | "validity"
  | "consistency"
  | "integrity"
  | "uniqueness"
  | "timeliness";

interface QualityBadgeProps {
  /** 0–1 quality score for the scope/dimension. */
  score: number;
  /** Optional dimension label, e.g. "completeness". */
  dimension?: QualityDimension;
}

export function QualityBadge({ score, dimension }: QualityBadgeProps) {
  // Quality goodness maps onto the same ≥0.80 / ≥0.55 bands as confidence (§9).
  const band = confidenceBand(score);
  const label = dimension ? `${dimension} ` : "quality ";
  return (
    <Badge
      tone={CONFIDENCE_TOKEN[band]}
      title={`${label.trim()} score ${score.toFixed(2)} (§5.2)`}
    >
      {label}
      {score.toFixed(2)}
    </Badge>
  );
}
