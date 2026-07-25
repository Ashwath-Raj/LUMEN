/**
 * `GraphErrorBoundary` — catches a Cytoscape load/render failure (the lazy graph
 * chunk failing to import, or a runtime error in the canvas) and renders the
 * table fallback instead (D8). A data-unavailable (501/no endpoint) case does NOT
 * reach here — that renders the empty/degraded state inside the canvas.
 */
import { Component, type ReactNode } from "react";

import { GraphTableFallback } from "./GraphTableFallback";
import type { GraphPayload } from "@/types/graph";

interface Props {
  children: ReactNode;
  payload: GraphPayload | undefined;
}
interface State {
  failed: boolean;
}

export class GraphErrorBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  render() {
    if (this.state.failed) return <GraphTableFallback payload={this.props.payload} />;
    return this.props.children;
  }
}
