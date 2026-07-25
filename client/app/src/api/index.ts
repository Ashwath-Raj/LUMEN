/** Barrel for the API layer (arch §G api/). */
export { apiFetch, ApiError, onDegradation } from "./client";
export type { ApiResult, RequestOptions } from "./client";
export { queryKeys } from "./queryKeys";

// Insights + overview
export { useOverview } from "./hooks/useOverview";
export { useInsights } from "./hooks/useInsights";
export type { InsightFeed, InsightFeedParams } from "./hooks/useInsights";
export {
  useInsightFeedback,
  useInsightApproval,
} from "./hooks/useInsightActions";
export type { InsightFeedback } from "./hooks/useInsightActions";

// Case Registry + Workspace
export { useCases, caseFiltersToQuery } from "./hooks/useCases";
export { useCase } from "./hooks/useCase";
export { useCaseTimeline } from "./hooks/useCaseTimeline";
export { useCaseInsights } from "./hooks/useCaseInsights";
export { useCaseActivity } from "./hooks/useCaseActivity";
export { useCaseLinked } from "./hooks/useCaseLinked";
export { useCaseLookups } from "./hooks/useCaseLookups";

// Geo Intelligence
export {
  useGeoDistricts,
  useGeoUnits,
  useGeoHotspots,
  useGeoDelay,
} from "./hooks/useGeo";
export type { GeoQueryParams } from "./hooks/useGeo";

// Intelligence graph + person dossier
export { useCaseGraph, useNetworkQuery, usePersonNetwork } from "./hooks/useGraph";
export type { NetworkQueryParams } from "./hooks/useGraph";
export { adaptGraph } from "./graphAdapter";
export { usePerson } from "./hooks/usePerson";

// Intelligence workbench
export {
  useAiAsk,
  useIntelligenceLeads,
  useActiveAlerts,
  usePersons,
} from "./hooks/useIntelligence";
export type { ActiveAlert } from "./hooks/useIntelligence";

// Ops + quality surfaces
export {
  useQualityScores,
  useQualityFindings,
  useSystemHealth,
  useSystemMetrics,
  useSystemRegistry,
  useSystemEval,
} from "./hooks/useOps";
export type {
  QualityScoreRow,
  QualityFindingRow,
  SystemHealth,
  SystemMetrics,
  SystemRegistry,
  SystemEval,
} from "./hooks/useOps";
