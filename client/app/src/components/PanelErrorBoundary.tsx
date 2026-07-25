/**
 * `PanelErrorBoundary` — error boundaries per PANEL, not per page (arch §G):
 * "a graph crash degrades one panel to its table fallback; the workspace around
 * it survives." Wrap each panel/region; a thrown render error renders the
 * INTERNAL `ErrorState` in place, and the rest of the page keeps working.
 */
import { Component, type ErrorInfo, type ReactNode } from "react";

import { ApiError } from "@/api/client";
import { ErrorState } from "@/design/primitives";

interface Props {
  children: ReactNode;
  /** Optional custom fallback (e.g. a graph panel's DataGrid table fallback). */
  fallback?: ReactNode;
}
interface State {
  error: Error | null;
}

export class PanelErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Panel-scoped; the page survives. Logged for the operator console.
    console.error("Panel error boundary caught:", error, info.componentStack);
  }

  render(): ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;
    if (this.props.fallback) return this.props.fallback;

    const apiError =
      error instanceof ApiError
        ? error
        : new ApiError({
            code: "INTERNAL",
            message: error.message,
            traceId: "",
            retryable: false,
            status: 0,
          });
    return <ErrorState error={apiError} />;
  }
}
