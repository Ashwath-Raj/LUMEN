/**
 * `GraphCanvas` (D8, §14) — the interactive intelligence graph. This module owns
 * the `cytoscape` dependency, so it is code-split into the graph chunk (arch §G:
 * "the graph and map libraries in their own chunks"). Feature pages lazy-load it.
 *
 * Interactions: pan/zoom (Cytoscape), node select → Inspector (via `onSelect`),
 * double-click → drill-in (`onOpen`, uses the node's href), neighbour highlight
 * on selection (others fade), text search (matches highlight, rest fade),
 * expand affordance (`onExpand`), fit/zoom toolbar, smooth force-directed layout
 * that respects `prefers-reduced-motion`.
 *
 * Empty/degraded: with no nodes the canvas shows an explicit empty state — it
 * NEVER fabricates nodes or edges. Node colour/glyph come from the shared graph
 * vocabulary so the canvas, legend and table fallback agree.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import cytoscape, { type Core, type ElementDefinition } from "cytoscape";
import { Search, Maximize2, Plus, X } from "lucide-react";

import { EmptyState } from "@/design/primitives";
import type { EntityRef, EntityRefKind } from "@/components/entity";
import type { GraphNode, GraphPayload } from "@/types/graph";
import { cn } from "@/utils/cn";

import { EDGE_LABEL, NODE_GLYPH, NODE_LABEL, nodeColor, resolved } from "./graphStyle";

interface GraphCanvasProps {
  payload: GraphPayload | undefined;
  /** Node select → Inspector. */
  onSelect: (ref: EntityRef) => void;
  /** Double-click a node → drill in (navigate to its href). */
  onOpen?: (node: GraphNode) => void;
  /** Expand a node's 1-hop neighbours (fetch more; degraded if no endpoint). */
  onExpand?: (node: GraphNode) => void;
  selectedId?: string | null;
  /** Empty-state copy when there are no nodes. */
  emptyMessage?: string;
}

/** Map a graph node kind to an inspector EntityRef kind. */
function toRefKind(kind: GraphNode["kind"]): EntityRefKind {
  switch (kind) {
    case "case":
    case "person":
    case "officer":
    case "evidence":
      return kind;
    case "address":
      return "location";
    case "fir":
      return "case";
    default:
      return "location"; // vehicle/organization/phone → generic inspector card
  }
}

function nodeToRef(node: GraphNode): EntityRef {
  return {
    kind: toRefKind(node.kind),
    id: node.id,
    label: node.label,
    sublabel: NODE_LABEL[node.kind],
    href: node.href ?? null,
    fields: node.props
      ? Object.entries(node.props).map(([label, value]) => ({
          label,
          value: String(value),
        }))
      : undefined,
  };
}

function prefersReducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
  );
}

export function GraphCanvas({
  payload,
  onSelect,
  onOpen,
  onExpand,
  selectedId,
  emptyMessage = "No graph data.",
}: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);
  const [search, setSearch] = useState("");

  // Keep callbacks in refs so the Cytoscape init effect can run ONCE (empty
  // deps) without tearing down/recreating the instance when a parent passes new
  // callback identities on each render.
  const onSelectRef = useRef(onSelect);
  const onOpenRef = useRef(onOpen);
  useEffect(() => {
    onSelectRef.current = onSelect;
    onOpenRef.current = onOpen;
  }, [onSelect, onOpen]);

  const nodeCount = payload?.nodes.length ?? 0;
  const isEmpty = nodeCount === 0;

  const elements = useMemo<ElementDefinition[]>(() => {
    if (!payload) return [];
    const nodes: ElementDefinition[] = payload.nodes.map((n) => ({
      data: {
        id: n.id,
        label: `${NODE_GLYPH[n.kind]}  ${n.label}`,
        kind: n.kind,
        color: nodeColor(n.kind),
        raw: n,
      },
    }));
    const edges: ElementDefinition[] = payload.edges.map((e) => ({
      data: {
        id: e.id,
        source: e.source,
        target: e.target,
        label: EDGE_LABEL[e.rel] ?? e.rel,
      },
    }));
    return [...nodes, ...edges];
  }, [payload]);

  // Initialise Cytoscape once.
  useEffect(() => {
    if (!containerRef.current || cyRef.current) return;
    const cy = cytoscape({
      container: containerRef.current,
      minZoom: 0.2,
      maxZoom: 3,
      wheelSensitivity: 0.2,
      style: [
        {
          selector: "node",
          style: {
            "background-color": "data(color)",
            "border-color": resolved("--bg-void"),
            "border-width": 2,
            label: "data(label)",
            color: resolved("--ink-primary"),
            "font-size": 11,
            "font-family": "Inter, sans-serif",
            "text-valign": "bottom",
            "text-margin-y": 4,
            width: 26,
            height: 26,
            "text-background-color": resolved("--bg-panel"),
            "text-background-opacity": 0.7,
            "text-background-padding": "2px",
          },
        },
        {
          selector: "edge",
          style: {
            width: 1.5,
            "line-color": resolved("--line"),
            "target-arrow-color": resolved("--line"),
            "target-arrow-shape": "triangle",
            "arrow-scale": 0.8,
            "curve-style": "bezier",
            label: "data(label)",
            "font-size": 9,
            color: resolved("--ink-faint"),
            "text-rotation": "autorotate",
            "text-opacity": 0,
          },
        },
        { selector: "edge:selected, edge.hl", style: { "text-opacity": 1, "line-color": resolved("--signal"), "target-arrow-color": resolved("--signal") } },
        { selector: "node:selected", style: { "border-color": resolved("--signal"), "border-width": 3 } },
        { selector: ".faded", style: { opacity: 0.15 } },
        { selector: ".match", style: { "border-color": resolved("--signal"), "border-width": 3 } },
      ],
    });
    cyRef.current = cy;

    cy.on("tap", "node", (evt) => {
      const node = evt.target;
      const raw = node.data("raw") as GraphNode;
      // Highlight closed neighbourhood, fade the rest.
      cy.elements().addClass("faded");
      node.closedNeighborhood().removeClass("faded").addClass("hl");
      onSelectRef.current(nodeToRef(raw));
    });
    cy.on("dbltap", "node", (evt) => {
      const raw = evt.target.data("raw") as GraphNode;
      onOpenRef.current?.(raw);
    });
    cy.on("tap", (evt) => {
      if (evt.target === cy) cy.elements().removeClass("faded hl");
    });

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
    // Init once — callbacks are read from refs to avoid re-instantiating cy.
  }, []);

  // Sync elements + run layout when the payload changes.
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().remove();
    if (elements.length) {
      cy.add(elements);
      cy.layout({
        name: "cose",
        animate: !prefersReducedMotion(),
        animationDuration: 400,
        padding: 30,
        nodeRepulsion: () => 8000,
      }).run();
      cy.fit(undefined, 40);
    }
  }, [elements]);

  // Reflect external selection (e.g. from the URL) onto the canvas.
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || !selectedId) return;
    const node = cy.getElementById(selectedId);
    if (node.nonempty()) {
      cy.elements().addClass("faded");
      node.closedNeighborhood().removeClass("faded");
      node.select();
    }
  }, [selectedId]);

  // Search: highlight matches, fade the rest.
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.nodes().removeClass("match");
    const term = search.trim().toLowerCase();
    if (!term) {
      cy.elements().removeClass("faded");
      return;
    }
    const matches = cy.nodes().filter((n) => {
      const raw = n.data("raw") as GraphNode;
      return raw.label.toLowerCase().includes(term);
    });
    cy.elements().addClass("faded");
    matches.removeClass("faded").addClass("match");
    matches.neighborhood().removeClass("faded");
  }, [search]);

  function fit() {
    cyRef.current?.fit(undefined, 40);
  }
  function expandSelected() {
    const cy = cyRef.current;
    const sel = cy?.$("node:selected").first();
    if (sel && sel.nonempty()) onExpand?.(sel.data("raw") as GraphNode);
  }

  return (
    <div className="relative h-full w-full" style={{ background: "var(--bg-void)" }}>
      {/* Toolbar */}
      <div className="absolute left-3 top-3 z-10 flex items-center gap-2">
        <div className="flex items-center gap-2 rounded border border-line bg-panel px-2 py-1.5 shadow-panel">
          <Search size={14} className="text-ink-faint" aria-hidden />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search nodes…"
            aria-label="Search graph nodes"
            className="w-40 bg-transparent text-caption text-ink-primary outline-none placeholder:text-ink-faint"
          />
          {search ? (
            <button
              type="button"
              onClick={() => setSearch("")}
              aria-label="Clear search"
              className="text-ink-faint hover:text-ink-primary"
            >
              <X size={12} />
            </button>
          ) : null}
        </div>
        <button
          type="button"
          onClick={fit}
          aria-label="Fit graph to view"
          className="rounded border border-line bg-panel p-1.5 text-ink-muted shadow-panel hover:text-signal"
        >
          <Maximize2 size={14} />
        </button>
        {onExpand ? (
          <button
            type="button"
            onClick={expandSelected}
            aria-label="Expand selected node"
            className="rounded border border-line bg-panel p-1.5 text-ink-muted shadow-panel hover:text-signal"
          >
            <Plus size={14} />
          </button>
        ) : null}
      </div>

      {/* Cytoscape mount */}
      <div ref={containerRef} className={cn("h-full w-full", isEmpty && "opacity-40")} />

      {/* Empty state overlay — never fabricates nodes. */}
      {isEmpty ? (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center p-6">
          <div className="pointer-events-auto max-w-sm">
            <EmptyState message={emptyMessage} />
          </div>
        </div>
      ) : null}
    </div>
  );
}
