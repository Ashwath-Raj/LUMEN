/**
 * Graph node/edge presentation — the glyph + token colour per node kind and a
 * label per edge kind, in ONE place so the canvas, the legend and the table
 * fallback describe the graph identically (no duplicated vocabulary). Colours
 * resolve to concrete values (Cytoscape can't consume `var(--token)`), with the
 * §31.1 hex as fallback — kept in sync with tokens.css.
 */
import { token } from "@/design/tokens";
import type { GraphEdgeKind, GraphNodeKind } from "@/types/graph";

/** Fixed glyphs — shared entity types reuse the §F entity glyphs. */
export const NODE_GLYPH: Record<GraphNodeKind, string> = {
  person: "◉",
  case: "▣",
  vehicle: "⛢",
  organization: "⬢",
  phone: "☏",
  address: "⌖",
  evidence: "❏",
  fir: "▤",
  officer: "✦",
};

export const NODE_LABEL: Record<GraphNodeKind, string> = {
  person: "Person",
  case: "Case",
  vehicle: "Vehicle",
  organization: "Organization",
  phone: "Phone",
  address: "Address",
  evidence: "Evidence",
  fir: "FIR",
  officer: "Officer",
};

/** Token var per node kind (resolved at style-build time). */
const NODE_TOKEN: Record<GraphNodeKind, string> = {
  person: "--signal",
  case: "--risk-high",
  vehicle: "--confidence-med",
  organization: "--risk-medium",
  phone: "--ink-muted",
  address: "--ink-muted",
  evidence: "--confidence-high",
  fir: "--risk-high",
  officer: "--signal",
};

const HEX_FALLBACK: Record<string, string> = {
  "--signal": "#35e0d4",
  "--risk-high": "#ff9548",
  "--risk-medium": "#ffd166",
  "--confidence-med": "#ffd166",
  "--confidence-high": "#4ade9b",
  "--ink-muted": "#8ca3bf",
};

export function nodeColor(kind: GraphNodeKind): string {
  const v = NODE_TOKEN[kind];
  return token(v) || HEX_FALLBACK[v] || "#8ca3bf";
}

export const EDGE_LABEL: Record<GraphEdgeKind, string> = {
  ASSOCIATED_WITH: "associated with",
  COMMUNICATED_WITH: "communicated with",
  OWNS: "owns",
  VISITED: "visited",
  INVESTIGATED_BY: "investigated by",
  RELATED_TO: "related to",
};

export function resolved(varName: string): string {
  return token(varName) || HEX_FALLBACK[varName] || "#8ca3bf";
}
