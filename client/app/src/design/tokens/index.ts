/**
 * Typed accessors for the design tokens declared in `tokens.css`.
 *
 * These mirror the CSS custom properties so TypeScript code (chart libraries,
 * canvas renderers, inline styles) can reference the SAME token values the CSS
 * uses — never a second hard-coded copy (spec §31, §33 row-16). The CSS file
 * remains the runtime source of truth; this is the compile-time view of it.
 */

/** Read a token's live value from the document root (browser only). */
export function token(name: string): string {
  if (typeof window === "undefined") return "";
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** §31.1 risk bands (spec §5.2 / §9). Colour is never the only signal (§F a11y). */
export const RISK_BANDS = ["critical", "high", "medium", "low"] as const;
export type RiskBand = (typeof RISK_BANDS)[number];

export const RISK_TOKEN: Record<RiskBand, string> = {
  critical: "var(--risk-critical)",
  high: "var(--risk-high)",
  medium: "var(--risk-medium)",
  low: "var(--risk-low)",
};

/** Human label for a risk band — the text that ALWAYS accompanies the colour. */
export const RISK_LABEL: Record<RiskBand, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

/** §9 confidence display bands: ≥0.80 High · 0.55–0.79 Moderate · <0.55 Low. */
export type ConfidenceBand = "high" | "moderate" | "low";

export function confidenceBand(composite: number): ConfidenceBand {
  if (composite >= 0.8) return "high";
  if (composite >= 0.55) return "moderate";
  return "low";
}

export const CONFIDENCE_TOKEN: Record<ConfidenceBand, string> = {
  high: "var(--confidence-high)",
  moderate: "var(--confidence-med)",
  low: "var(--confidence-low)",
};

/**
 * §F entity-type glyphs — fixed and global; the same glyph everywhere an entity
 * type appears (chips, nodes, cards, search results). Semantic vocabulary §2.1.
 */
export const ENTITY_GLYPH = {
  case: "▣",
  person: "◉",
  officer: "✦",
  station: "⌂",
  district: "⬡",
  charge: "§",
  insight: "◆",
} as const;

export type EntityGlyphKind = keyof typeof ENTITY_GLYPH;

/**
 * §8 `Evidence.entity` glyphs — a superset of ENTITY_GLYPH covering the evidence
 * vocabulary (participant, jurisdiction, court, process_event, kb_document). The
 * shared entity types keep the SAME glyph as ENTITY_GLYPH (§F "the same glyph
 * everywhere an entity type appears"); the evidence-only kinds add their own.
 */
export const EVIDENCE_GLYPH = {
  case: ENTITY_GLYPH.case,
  person: ENTITY_GLYPH.person,
  participant: ENTITY_GLYPH.person,
  officer: ENTITY_GLYPH.officer,
  station: ENTITY_GLYPH.station,
  jurisdiction: ENTITY_GLYPH.district,
  court: "⚖",
  charge: ENTITY_GLYPH.charge,
  process_event: "◷",
  kb_document: "❏",
} as const;

export type EvidenceEntity = keyof typeof EVIDENCE_GLYPH;
