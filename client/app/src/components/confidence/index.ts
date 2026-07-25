/**
 * Confidence component family (D2, §9) — the decomposed-confidence UI: a
 * band-coloured meter that expands into five labelled component bars naming the
 * limiting link, plus factor bars for the §8 `Factor[]`.
 */
export { ConfidenceMeter } from "./ConfidenceMeter";
export { ConfidenceBreakdown } from "./ConfidenceBreakdown";
export { FactorBars } from "./FactorBars";
export {
  CONFIDENCE_COMPONENTS,
  CONFIDENCE_LABEL,
  limitingFactor,
  limitingSentence,
  type ConfidenceComponent,
  type LimitingFactor,
} from "./confidence";
