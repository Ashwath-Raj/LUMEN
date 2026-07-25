/**
 * Graph component family (D8, §14) — the Cytoscape canvas, its table fallback,
 * error boundary, and shared node/edge vocabulary. `GraphCanvas` owns the
 * cytoscape dependency and is lazy-loaded by feature pages (arch §G chunking).
 */
export { GraphCanvas } from "./GraphCanvas";
export { GraphSurface } from "./GraphSurface";
export { GraphTableFallback } from "./GraphTableFallback";
export { GraphErrorBoundary } from "./GraphErrorBoundary";
export {
  NODE_GLYPH,
  NODE_LABEL,
  EDGE_LABEL,
  nodeColor,
} from "./graphStyle";
