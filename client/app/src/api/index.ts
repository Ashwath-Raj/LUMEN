/** Barrel for the API layer (arch §G api/). */
export { apiFetch, ApiError, onDegradation } from "./client";
export type { ApiResult, RequestOptions } from "./client";
export { queryKeys } from "./queryKeys";

// Insights + overview (Session 1)
export { useOverview } from "./hooks/useOverview";
export { useInsights } from "./hooks/useInsights";
export type { InsightFeed, InsightFeedParams } from "./hooks/useInsights";
export {
  useInsightFeedback,
  useInsightApproval,
} from "./hooks/useInsightActions";
export type { InsightFeedback } from "./hooks/useInsightActions";

// Case Registry + Workspace (Session 2)
export { useCases, caseFiltersToQuery } from "./hooks/useCases";
export { useCase } from "./hooks/useCase";
export { useCaseTimeline } from "./hooks/useCaseTimeline";
export { useCaseInsights } from "./hooks/useCaseInsights";
export { useCaseActivity } from "./hooks/useCaseActivity";
export { useCaseLinked } from "./hooks/useCaseLinked";
export type { LinkedCase } from "./hooks/useCaseLinked";
export { useCaseLookups } from "./hooks/useCaseLookups";

// Geo Intelligence (Session 3)
export {
  useGeoDistricts,
  useGeoUnits,
  useGeoHotspots,
  useGeoDelay,
} from "./hooks/useGeo";
export type { GeoQueryParams } from "./hooks/useGeo";

// Intelligence graph + person dossier (Session 4)
export { useCaseGraph, useNetworkQuery, usePersonNetwork } from "./hooks/useGraph";
export { usePerson } from "./hooks/usePerson";
