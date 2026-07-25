/**
 * Graph table fallback (D8: "Table fallback (DataGrid of nodes/edges) … the
 * accessible alternative"). Renders when Cytoscape fails to load (via
 * `GraphErrorBoundary`) or as the a11y alternative. Same node/edge data as the
 * canvas, keyboard-navigable; never fabricates rows.
 */
import { DataGrid, type Column } from "@/design/primitives";
import type { GraphEdge, GraphNode, GraphPayload } from "@/types/graph";
import { EDGE_LABEL, NODE_GLYPH, NODE_LABEL } from "./graphStyle";

const NODE_COLUMNS: Column<GraphNode>[] = [
  {
    key: "kind",
    header: "Type",
    render: (n) => (
      <span className="text-ink-muted">
        <span aria-hidden className="mr-1 text-signal">
          {NODE_GLYPH[n.kind]}
        </span>
        {NODE_LABEL[n.kind]}
      </span>
    ),
  },
  {
    key: "label",
    header: "Label",
    render: (n) => <span className="text-ink-primary">{n.label}</span>,
  },
];

const EDGE_COLUMNS: Column<GraphEdge>[] = [
  { key: "source", header: "From", render: (e) => <span className="font-mono text-ink-muted">{e.source}</span> },
  { key: "rel", header: "Relationship", render: (e) => <span className="text-ink-primary">{EDGE_LABEL[e.rel] ?? e.rel}</span> },
  { key: "target", header: "To", render: (e) => <span className="font-mono text-ink-muted">{e.target}</span> },
];

export function GraphTableFallback({ payload }: { payload: GraphPayload | undefined }) {
  const nodes = payload?.nodes ?? [];
  const edges = payload?.edges ?? [];

  if (nodes.length === 0) {
    return (
      <div className="p-6 text-caption text-ink-muted">
        Graph view unavailable and no graph data to tabulate.
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-4 overflow-auto p-6">
      <p className="text-caption text-ink-muted">
        Graph rendering unavailable — showing nodes and edges as tables (same
        data, keyboard-navigable).
      </p>
      <section className="rounded border border-line bg-panel">
        <h3 className="border-b border-line px-3 py-2 text-caption uppercase tracking-wide text-ink-muted">
          Nodes ({nodes.length})
        </h3>
        <DataGrid<GraphNode> columns={NODE_COLUMNS} rows={nodes} rowKey={(n) => n.id} caption="Graph nodes" />
      </section>
      <section className="rounded border border-line bg-panel">
        <h3 className="border-b border-line px-3 py-2 text-caption uppercase tracking-wide text-ink-muted">
          Edges ({edges.length})
        </h3>
        <DataGrid<GraphEdge> columns={EDGE_COLUMNS} rows={edges} rowKey={(e) => e.id} caption="Graph edges" />
      </section>
    </div>
  );
}
