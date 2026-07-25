/**
 * Board tab (E.4) — the investigation graph: case ⇄ resolved persons ⇄ arrests
 * ⇄ officers ⇄ linked cases (§30.4), rendered with the shared `GraphSurface`
 * (Cytoscape, D8). Node selection opens the persistent Inspector; double-click
 * drills into an entity.
 *
 * Backed by `GET /cases/{id}/graph` — no backend endpoint yet, so the board
 * shows its empty state with the "live graph intelligence unavailable" banner
 * and fabricates nothing. Expanding a node (1-hop) is wired to the same endpoint
 * and degrades identically until it lands.
 */
import { useCaseGraph } from "@/api";
import { GraphSurface } from "@/components/graph";
import type { EntityRef } from "@/components/entity";
import type { GraphNode } from "@/types/graph";

interface BoardTabProps {
  caseId: string;
  onSelect: (ref: EntityRef) => void;
  onOpen: (node: GraphNode) => void;
  selectedId: string | null;
}

export function BoardTab({ caseId, onSelect, onOpen, selectedId }: BoardTabProps) {
  const graph = useCaseGraph(caseId);
  return (
    <div className="h-full min-h-0">
      <GraphSurface
        payload={graph.data}
        isLoading={graph.isLoading}
        error={graph.error}
        onSelect={onSelect}
        onOpen={onOpen}
        selectedId={selectedId}
        emptyMessage="No investigation-board relationships for this case yet."
        degradedMessage="Live graph intelligence is unavailable — the investigation board populates when the graph endpoint is served. No relationships are fabricated."
      />
    </div>
  );
}
