/**
 * Intelligence Graph contract types (D8, §14).
 *
 * ── GENERATION NOTE (arch §G) ────────────────────────────────────────────
 * Shaped to the backend's frozen `GraphContract` (`contracts/graph.py`):
 * `{ contract_version, nodes: dict[], edges: dict[] }`, where §14.2 nodes carry a
 * semantic type + id and §14.3/§3.6 edges mirror src/dst/rel/weight/props. The
 * node/edge VOCABULARIES below are the display set the UI renders (glyph +
 * colour); the backend's §14.2 semantic vocabulary is narrower today, and the
 * GraphContract payload is open dicts, so this is a rendering superset — never
 * fabricated data. There is currently NO graph endpoint in the OpenAPI, so the
 * graph renders its empty/degraded state until one lands.
 * ─────────────────────────────────────────────────────────────────────────
 */

/** Node kinds the graph can render (Session-4 brief vocabulary). */
export type GraphNodeKind =
  | "person"
  | "case"
  | "vehicle"
  | "organization"
  | "phone"
  | "address"
  | "evidence"
  | "fir"
  | "officer";

/** Edge relationship kinds (Session-4 brief vocabulary; §14.3). */
export type GraphEdgeKind =
  | "ASSOCIATED_WITH"
  | "COMMUNICATED_WITH"
  | "OWNS"
  | "VISITED"
  | "INVESTIGATED_BY"
  | "RELATED_TO";

/** One graph node (§14.2 semantic node). */
export interface GraphNode {
  id: string;
  kind: GraphNodeKind;
  label: string;
  /** Optional drill-in target (e.g. `/case/123`, `/person/abc`). */
  href?: string | null;
  /** Free-form node properties (§14.2 props). */
  props?: Record<string, string | number | boolean | null>;
}

/** One graph edge (§14.3 / §3.6 lumen_graph_edge). */
export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  rel: GraphEdgeKind;
  /** Edge support/weight (§14.3 weight). */
  weight?: number;
  props?: Record<string, string | number | boolean | null>;
}

/** `GraphContract` v1 payload (nodes + edges). */
export interface GraphPayload {
  contract_version: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/** §14.4 result: an Insight PLUS the graph payload — "never a bare graph". */
import type { Insight } from "./contracts";
export interface GraphQueryResult {
  insight: Insight;
  graph: GraphPayload;
}

/** The ten named network queries (§14.4) — labels for the query rail (E.6). */
export interface NamedQuery {
  id: string; // q1..q10
  question: string;
}
