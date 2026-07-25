/**
 * Insight component family (D1, §8) — the platform's core component and its
 * sub-sections. The sub-sections are exported so surfaces that show one part of
 * an insight (e.g. a lineage-only inspector block) reuse the same rendering.
 */
export { InsightCard } from "./InsightCard";
export { LimitationsNote } from "./LimitationsNote";
export { LineagePanel } from "./LineagePanel";
export { CounterfactualsNote } from "./CounterfactualsNote";
export { RecommendationSection } from "./RecommendationSection";
export { InsightActions } from "./InsightActions";
export { INSIGHT_KIND_LABEL } from "./insightKind";
