/**
 * Insight-kind presentation metadata (§8 `kind`) — the glyph and plain label for
 * each of the eight kinds, in one place so every surface names a kind
 * identically. The glyph is the fixed insight glyph family; kinds share the
 * global "insight" mark (◆) with a kind label rather than inventing eight new
 * glyphs (§F: glyphs are for entity TYPES, not sub-kinds).
 */
import type { InsightKind } from "@/types/contracts";

export const INSIGHT_KIND_LABEL: Record<InsightKind, string> = {
  risk: "Risk",
  anomaly: "Anomaly",
  linkage: "Linkage",
  network: "Network",
  forecast: "Forecast",
  summary: "Summary",
  recommendation: "Recommendation",
  data_quality: "Data quality",
};
