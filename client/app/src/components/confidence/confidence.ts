/**
 * Shared confidence logic (§9) — the labels for the five multiplicative
 * components and the "limiting factor" computation, in ONE place so the meter,
 * the breakdown and any consumer name the weakest link identically (no
 * duplicated logic).
 *
 * §9 composite = evidence_quality × model_confidence × data_completeness
 *              × identity_confidence × graph_confidence
 * The limiting component is the smallest of the five — the sentence
 * "limited by identity match confidence (0.61)" is worth more than the number.
 */
import type { ConfidenceBreakdown } from "@/types/contracts";

/** The five §9 component keys, in the spec's order. */
export const CONFIDENCE_COMPONENTS = [
  "evidence_quality",
  "model_confidence",
  "data_completeness",
  "identity_confidence",
  "graph_confidence",
] as const;

export type ConfidenceComponent = (typeof CONFIDENCE_COMPONENTS)[number];

/** Plain-language labels (§9 table). */
export const CONFIDENCE_LABEL: Record<ConfidenceComponent, string> = {
  evidence_quality: "evidence quality",
  model_confidence: "model confidence",
  data_completeness: "data completeness",
  identity_confidence: "identity match confidence",
  graph_confidence: "graph support",
};

export interface LimitingFactor {
  component: ConfidenceComponent;
  value: number;
  label: string;
}

/** The weakest of the five components — the chain's limiting link (§9). */
export function limitingFactor(breakdown: ConfidenceBreakdown): LimitingFactor {
  let component: ConfidenceComponent = CONFIDENCE_COMPONENTS[0];
  let value = breakdown[component];
  for (const key of CONFIDENCE_COMPONENTS) {
    if (breakdown[key] < value) {
      value = breakdown[key];
      component = key;
    }
  }
  return { component, value, label: CONFIDENCE_LABEL[component] };
}

/** "limited by identity match confidence (0.61)" — the §9 sentence. */
export function limitingSentence(breakdown: ConfidenceBreakdown): string {
  const { label, value } = limitingFactor(breakdown);
  return `limited by ${label} (${value.toFixed(2)})`;
}
