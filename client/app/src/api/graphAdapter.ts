/**
 * Adapter: backend §7 `GraphContract` → the frontend `GraphPayload` the
 * `GraphCanvas` renders.
 *
 * The backend emits the contract exactly as §7/§14.3 specify — nodes as
 * `{type, id, label?}` and edges as the `lumen_graph_edge` column shape
 * `{src_type, src_id, dst_type, dst_id, rel, weight, props}`. The canvas wants
 * `{id, kind, label, href}` / `{id, source, target, rel}`. This is the ONE
 * place that translation happens, so the backend contract is never bent to suit
 * the UI and no component re-implements the mapping.
 */
import type { GraphEdge, GraphNode, GraphNodeKind, GraphPayload } from "@/types/graph";

/** Raw §7 GraphContract as the API returns it. */
export interface RawGraphContract {
  contract_version?: string;
  nodes: Array<{ type?: string; id: string; label?: string }>;
  edges: Array<{
    src_type?: string;
    src_id: string;
    dst_type?: string;
    dst_id: string;
    rel?: string;
    weight?: number;
    props?: Record<string, unknown>;
  }>;
}

const KNOWN_KINDS = new Set<GraphNodeKind>([
  "person", "participant", "case", "vehicle", "organization",
  "phone", "address", "evidence", "fir", "officer",
]);

function toKind(raw: string | undefined): GraphNodeKind {
  return raw && KNOWN_KINDS.has(raw as GraphNodeKind)
    ? (raw as GraphNodeKind)
    : "person";
}

/** Drill-in target per node kind (§B: every entity reference is navigation). */
function hrefFor(kind: GraphNodeKind, id: string): string | null {
  if (kind === "case" || kind === "fir") return `/case/${id}`;
  if (kind === "person") return `/person/${id}`;
  return null;
}

export function adaptGraph(raw: RawGraphContract | undefined): GraphPayload | undefined {
  if (!raw) return undefined;
  const nodes: GraphNode[] = (raw.nodes ?? []).map((n) => {
    const kind = toKind(n.type);
    return {
      id: n.id,
      kind,
      label: n.label ?? n.id,
      href: hrefFor(kind, n.id),
    };
  });
  const edges: GraphEdge[] = (raw.edges ?? []).map((e, i) => ({
    id: `${e.src_id}→${e.dst_id}:${e.rel ?? "REL"}:${i}`,
    source: e.src_id,
    target: e.dst_id,
    rel: e.rel ?? "RELATED_TO",
    weight: e.weight,
  }));
  return { contract_version: raw.contract_version ?? "v1", nodes, edges };
}
