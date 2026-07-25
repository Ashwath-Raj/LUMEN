/**
 * Map style helpers — resolve design tokens to concrete colour strings Leaflet's
 * path options require (Leaflet cannot consume `var(--token)`). Values are read
 * live from the tokens via `token()`; a literal fallback (the §31.1 hex, kept in
 * sync with tokens.css) guards the rare case where the computed value is empty,
 * so a district is never left unstyled. Colour is never the only signal — the
 * map pairs every band with a legend label (§F a11y).
 */
import { RISK_TOKEN, token, type RiskBand } from "@/design/tokens";

/** §31.1 literal fallbacks, kept in sync with tokens.css. */
const RISK_HEX: Record<RiskBand, string> = {
  critical: "#ff5a5a",
  high: "#ff9548",
  medium: "#ffd166",
  low: "#4ade9b",
};

/** Concrete colour for a risk band (resolves the token var, else the hex). */
export function riskColor(band: RiskBand): string {
  const varName = RISK_TOKEN[band].replace(/^var\(|\)$/g, "");
  return token(varName) || RISK_HEX[band];
}

/** The signal (interactive/live) colour, concrete. */
export function signalColor(): string {
  return token("--signal") || "#35e0d4";
}

/** A neutral line colour for boundaries with no data band. */
export function lineColor(): string {
  return token("--line") || "#1e3350";
}
