/**
 * `QueryBoundary` — the one place a TanStack Query result is mapped to the panel
 * states every surface must handle (task 8): Loading · Error · Empty · Degraded ·
 * Restricted · No-data. Feature sessions wrap a query in this instead of
 * re-implementing the five states (quality req: no duplicated UI logic).
 *
 * Mapping:
 *   - pending            → DelayedSkeleton (300 ms delay, §F)
 *   - error (ApiError)   → ErrorState, which renders SCOPE_DENIED as a calm
 *                          governance notice and everything else per §29.3.
 *                          A non-ApiError is normalised to INTERNAL so the panel
 *                          never white-screens (§G error-per-panel).
 *   - success + empty    → EmptyState with caller copy (never a bare spinner, §F)
 *   - success            → children(data), preceded by the StalenessBanner when
 *                          the envelope reported degradation (≥ L1, arch §E)
 *
 * `isEmpty` lets the caller define emptiness for its own payload shape; the
 * default treats `null`/`undefined`/`[]` as empty.
 */
import type { ReactNode } from "react";
import type { UseQueryResult } from "@tanstack/react-query";

import { ApiError } from "@/api";
import { EmptyState, ErrorState } from "@/design/primitives";

import { DelayedSkeleton } from "./DelayedSkeleton";
import { StalenessBanner } from "./StalenessBanner";

interface QueryBoundaryProps<T> {
  query: UseQueryResult<T>;
  children: (data: T) => ReactNode;
  /** Copy for the empty state — required (an empty state without copy is a defect). */
  emptyMessage: string;
  /** Optional empty-state action (e.g. a "clear filters" button). */
  emptyAction?: ReactNode;
  /** Override emptiness for the payload shape. */
  isEmpty?: (data: T) => boolean;
  /** Skeleton line count while loading. */
  skeletonLines?: number;
}

function defaultIsEmpty(data: unknown): boolean {
  if (data == null) return true;
  if (Array.isArray(data)) return data.length === 0;
  return false;
}

function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  return new ApiError({
    code: "INTERNAL",
    message: error instanceof Error ? error.message : "Unexpected error",
    traceId: "",
    retryable: false,
    status: 0,
  });
}

export function QueryBoundary<T>({
  query,
  children,
  emptyMessage,
  emptyAction,
  isEmpty = defaultIsEmpty,
  skeletonLines = 3,
}: QueryBoundaryProps<T>) {
  if (query.isPending) {
    return <DelayedSkeleton loading lines={skeletonLines} />;
  }

  if (query.isError) {
    return (
      <ErrorState
        error={toApiError(query.error)}
        onRetry={() => query.refetch()}
      />
    );
  }

  const data = query.data;
  if (isEmpty(data)) {
    return <EmptyState message={emptyMessage} action={emptyAction} />;
  }

  return (
    <>
      <StalenessBanner className="mb-3" />
      {children(data)}
    </>
  );
}
