/**
 * Risk legend — the band→colour key, so the choropleth/markers never rely on
 * colour alone (§F a11y: "band label text accompanies the colour"). Compact,
 * bottom-corner.
 */
import { Panel } from "@/design/primitives";
import { RISK_BANDS, RISK_LABEL, RISK_TOKEN } from "@/design/tokens";

export function MapLegend() {
  return (
    <Panel elevated className="flex items-center gap-3 px-3 py-2">
      <span className="text-caption uppercase tracking-wide text-ink-faint">
        Risk
      </span>
      {RISK_BANDS.map((band) => (
        <span key={band} className="flex items-center gap-1 text-caption text-ink-muted">
          <span
            aria-hidden
            className="inline-block h-2.5 w-2.5 rounded-sm"
            style={{ background: RISK_TOKEN[band] }}
          />
          {RISK_LABEL[band]}
        </span>
      ))}
    </Panel>
  );
}
