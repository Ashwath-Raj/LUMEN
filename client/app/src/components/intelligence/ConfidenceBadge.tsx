/**
 * `ConfidenceBadge` — compact §9 confidence pill: band label + value, never
 * colour alone (§F a11y). The dense-workbench counterpart of `ConfidenceMeter`
 * (which stays the expandable meter for card bodies); both share the §9 band
 * vocabulary so they can never disagree.
 */
import { Badge } from "@/design/primitives";
import { CONFIDENCE_TOKEN, confidenceBand } from "@/design/tokens";

const BAND_LABEL: Record<string, string> = {
  high: "High",
  moderate: "Moderate",
  low: "Low",
};

export function ConfidenceBadge({ value }: { value: number }) {
  const band = confidenceBand(value);
  return (
    <Badge
      tone={CONFIDENCE_TOKEN[band]}
      title={`Confidence ${value.toFixed(2)} (§9 ${BAND_LABEL[band]})`}
    >
      {BAND_LABEL[band]} · {value.toFixed(2)}
    </Badge>
  );
}
