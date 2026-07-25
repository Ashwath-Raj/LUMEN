/**
 * Risk score → band mapping (§9 / §5.2), kept separate from the `RiskBand`
 * component so that file stays component-only (React Fast Refresh). Callers pass
 * a raw score and get a band without re-implementing the thresholds.
 */
import type { RiskBand as RiskBandValue } from "@/design/tokens";

/** §9 thresholds; ≥0.80 critical follows §5.2 severity intent. */
export function riskBandFromScore(score: number): RiskBandValue {
  if (score >= 0.8) return "critical";
  if (score >= 0.6) return "high";
  if (score >= 0.4) return "medium";
  return "low";
}
