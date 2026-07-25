/**
 * Criminal Network — `/network` (E.6, §14.4, §30.6). The ten named queries as an
 * instrument: a left query rail (Q1–Q10, each its plain-language question), the
 * central GraphCanvas, and results as an InsightCard ABOVE the graph — "never a
 * bare graph" (§14.4), with the co-accusal trust caveat by default.
 *
 * The selected query lives in the URL (`?q=q2`, §C). Running a query calls
 * `/network/query/{q}` — which has no backend endpoint yet, so the graph shows
 * its empty state with a "live graph intelligence unavailable" banner and no
 * relationships are fabricated. Node selection opens the persistent Inspector.
 */
import { useMemo, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useNetworkQuery } from "@/api";
import { GraphSurface } from "@/components/graph";
import { InspectorPanel } from "@/components/inspector";
import { InsightCard } from "@/components/insight";
import { TrustBadge } from "@/components/trust";
import type { EntityRef } from "@/components/entity";
import type { GraphNode } from "@/types/graph";
import { useInspector } from "@/hooks/useInspector";
import { writeParams } from "@/utils/urlState";
import { cn } from "@/utils/cn";

import { NAMED_QUERIES } from "./namedQueries";

export default function NetworkPage() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const selectedQ = params.get("q");

  const query = useNetworkQuery(selectedQ);
  const { selection, select, clear } = useInspector();
  const refCache = useRef<Map<string, EntityRef>>(new Map());

  function onSelectEntity(ref: EntityRef) {
    refCache.current.set(`${ref.kind}:${ref.id}`, ref);
    select(ref);
  }

  function onOpenNode(node: GraphNode) {
    if (node.href) navigate(node.href);
  }

  const selectedRef: EntityRef | null = useMemo(() => {
    if (!selection) return null;
    const token = `${selection.kind}:${selection.id}`;
    return (
      refCache.current.get(token) ?? {
        kind: selection.kind,
        id: selection.id,
        label: selection.id,
      }
    );
  }, [selection]);

  const insight = query.data?.insight;
  const graph = query.data?.graph;

  return (
    <div className="relative isolate flex min-h-0 w-full flex-1 overflow-hidden">
      {/* Query rail (§14.4) */}
      <nav
        aria-label="Named network queries"
        className="w-72 shrink-0 overflow-auto border-r border-line bg-panel p-3"
      >
        <h1 className="mb-1 font-display text-panel-title text-ink-primary">
          Network
        </h1>
        <p className="mb-3 text-caption text-ink-muted">
          Ten named queries. Select one to run it against the knowledge graph.
        </p>
        <ul className="flex flex-col gap-1">
          {NAMED_QUERIES.map((nq) => {
            const active = nq.id === selectedQ;
            return (
              <li key={nq.id}>
                <button
                  type="button"
                  onClick={() => setParams(writeParams(params, { q: nq.id }))}
                  aria-pressed={active}
                  className={cn(
                    "flex w-full flex-col items-start gap-0.5 rounded border px-3 py-2 text-left",
                    "transition-colors duration-DEFAULT ease-ease",
                    active
                      ? "border-signal/50 bg-raised"
                      : "border-line hover:border-signal/40 hover:bg-raised",
                  )}
                >
                  <span className="font-mono text-caption text-ink-faint">
                    {nq.id.toUpperCase()}
                  </span>
                  <span className="text-caption text-ink-primary">
                    {nq.question}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Result: insight above graph (§14.4) */}
      <div className="flex min-w-0 flex-1 flex-col">
        {insight ? (
          <div className="border-b border-line p-4">
            <InsightCard insight={insight} defaultExpanded />
          </div>
        ) : selectedQ ? (
          <div className="border-b border-line px-4 py-2">
            <TrustBadge context="network" />
          </div>
        ) : null}

        <div className="relative min-h-0 flex-1">
          <GraphSurface
            payload={graph}
            isLoading={query.isLoading}
            error={query.error}
            onSelect={onSelectEntity}
            onOpen={onOpenNode}
            selectedId={selection?.id ?? null}
            emptyMessage={
              selectedQ
                ? "No results for this query."
                : "Select a named query from the rail to explore the network."
            }
            degradedMessage="Live graph intelligence is unavailable — the network endpoint is not yet served. No relationships are shown."
          />
        </div>
      </div>

      {selectedRef ? (
        <div className="absolute inset-y-0 right-0 z-inspector max-w-full">
          <InspectorPanel entity={selectedRef} onClose={clear} />
        </div>
      ) : null}
    </div>
  );
}
