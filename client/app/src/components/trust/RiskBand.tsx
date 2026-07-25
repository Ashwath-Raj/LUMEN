/**
 * `RiskBand` (D12) — the risk pill (spec §5.2 / §9). Renders a gravity/risk band
 * as a coloured pill with its band LABEL, never colour alone (§F a11y).
 *
 * Reusable everywhere a risk band appears: case-registry gravity column, case
 * header, forecast rows, command stats. Accepts either a band directly or a raw
 * score (mapped via the shared §9 bands) so callers never re-implement the
 * threshold logic.
 */
import { Badge } from "@/design/primitives/Badge";
import {
  RISK_LABEL,
  RISK_TOKEN,
  type RiskBand as RiskBandValue,
} from "@/design/tokens";
import { riskBandFromScore } from "./riskScore";

interface RiskBandProps {
  /** The band to render. Provide this OR `score`. */
  band?: RiskBandValue;
  /** A raw 0–1 risk score, mapped to a band via §9 thresholds. */
  score?: number;
  /** Show the numeric score alongside the label (e.g. "High · 0.72"). */
  showScore?: boolean;
}

export function RiskBand({ band, score, showScore = false }: RiskBandProps) {
  const resolved: RiskBandValue =
    band ?? (score !== undefined ? riskBandFromScore(score) : "low");
  const label = RISK_LABEL[resolved];
  return (
    <Badge tone={RISK_TOKEN[resolved]} title={`Risk band: ${label}`}>
      {label}
      {showScore && score !== undefined ? ` · ${score.toFixed(2)}` : null}
    </Badge>
  );
}
