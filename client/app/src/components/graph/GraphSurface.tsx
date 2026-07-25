/**
 * `GraphSurface` — the shared graph rendering path: lazy `GraphCanvas` (cytoscape
 * chunk) wrapped in a `GraphErrorBoundary` (→ table fallback if cytoscape fails)
 * and a Suspense fallback, plus the state handling every graph surface needs.
 *
 * Degradation (Session-4 brief): when live graph intelligence is unavailable, the
 * EMPTY GRAPH STAYS VISIBLE with a non-blocking banner ("live graph intelligence
 * unavailable") — it does NOT collapse to a text panel and NEVER fabricates
 * relationships. A genuine (non-availability) error shows `ErrorState`.
 *
 * Reused by the Network page (E.6), the Case Workspace board tab (E.4), and the
 * Person Dossier ego graph (E.5).
 */
import { Suspense, lazy } from "react";
import { CloudOff } from "lucide-react";

import { ApiError } from "@/api";
import type { EntityRef } from "@/components/entity";
import { EmptyState, ErrorState } from "@/design/primitives";
import type { GraphNode, GraphPayload } from "@/types/graph";

import { GraphErrorBoundary } from "./GraphErrorBoundary";

const GraphCanvas = lazy(() =>
  import("./GraphCanvas").then((m) => ({ default: m.GraphCanvas })),
);

interface GraphSurfaceProps {
  payload: GraphPayload | undefined;
  isLoading: boolean;
  error: unknown;
  onSelect: (ref: EntityRef) => void;
  onOpen?: (node: GraphNode) => void;
  onExpand?: (node: GraphNode) => void;
  selectedId?: string | null;
  emptyMessage?: string;
  degradedMessage?: string;
}

function isUnavailable(error: unknown): boolean {
  return (
    error instanceof ApiError &&
    (error.code === "DEPENDENCY_UNAVAILABLE" || error.code === "DEGRADED_RESULT")
  );
}

export function GraphSurface({
  payload,
  isLoading,
  error,
  onSelect,
  onOpen,
  onExpand,
  selectedId,
  emptyMessage = "No relationships to display.",
  degradedMessage = "Live graph intelligence is unavailable — no relationships are shown.",
}: GraphSurfaceProps) {
  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <EmptyState message="Loading graph…" />
      </div>
    );
  }

  // A real (non-availability) failure: surface it. Availability failures fall
  // through and render the empty canvas + banner below.
  if (error && !isUnavailable(error)) {
    return (
      <div className="p-6">
        <ErrorState
          error={
            error instanceof ApiError
              ? error
              : new ApiError({
                  code: "INTERNAL",
                  message: "Graph failed to load",
                  traceId: "",
                  retryable: false,
                  status: 0,
                })
          }
        />
      </div>
    );
  }

  const degraded = isUnavailable(error);

  return (
    <div className="relative h-full w-full">
      <GraphErrorBoundary payload={payload}>
        <Suspense
          fallback={
            <div className="flex h-full items-center justify-center">
              <EmptyState message="Loading graph…" />
            </div>
          }
        >
          <GraphCanvas
            payload={payload}
            onSelect={onSelect}
            onOpen={onOpen}
            onExpand={onExpand}
            selectedId={selectedId}
            emptyMessage={degraded ? degradedMessage : emptyMessage}
          />
        </Suspense>
      </GraphErrorBoundary>

      {degraded ? (
        <div className="pointer-events-none absolute right-3 top-3 z-10 flex items-center gap-2 rounded border border-degraded/50 bg-panel/90 px-3 py-2 text-caption text-degraded backdrop-blur">
          <CloudOff size={14} strokeWidth={1.5} aria-hidden />
          <span>Live graph intelligence unavailable.</span>
        </div>
      ) : null}
    </div>
  );
}
