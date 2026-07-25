/**
 * Trust component family (D12) — the shared governance badges (§4.1, §5.2, §10,
 * §11). Reusable everywhere headers, cards and rows appear.
 */
export { RiskBand } from "./RiskBand";
export { riskBandFromScore } from "./riskScore";
export { ClassificationBadge } from "./ClassificationBadge";
export { QualityBadge, type QualityDimension } from "./QualityBadge";
export { TrustBadge } from "./TrustBadge";
export {
  TRUST_STATEMENT,
  trustContextFor,
  type TrustContext,
} from "./trustStatements";
export { LifecycleBadge } from "./LifecycleBadge";
