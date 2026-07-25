/**
 * `ErrorState` — maps each §29.3 error code to its rendering (arch §E table).
 * The single place error → UI mapping lives (arch §G). A panel-scoped error
 * boundary renders this; the page never white-screens.
 *
 * Key architectural stances encoded here:
 *  - SCOPE_DENIED is a calm GOVERNANCE notice, visually distinct from failure
 *    ("access is logged") — governance made visible is a feature (§B, §20).
 *  - INTERNAL shows the trace_id; the panel fails, the page survives.
 *  - DEPENDENCY_UNAVAILABLE / DEGRADED_RESULT render with a staleness note (the
 *    shell pill reflects the level from the envelope meta).
 */
import type { ReactNode } from "react";
import { Lock, SearchX, Clock, AlertTriangle, WifiOff } from "lucide-react";

import type { ApiError } from "@/api/client";
import { cn } from "@/utils/cn";

interface ErrorStateProps {
  error: ApiError;
  /** Optional retry affordance (used for RATE_LIMITED / transient failures). */
  onRetry?: () => void;
}

interface Rendering {
  icon: ReactNode;
  title: string;
  body: (error: ApiError) => string;
  /** Governance notices are styled calm, not as failures (§B). */
  tone: "governance" | "failure" | "info";
}

const RENDERING: Record<string, Rendering> = {
  SCOPE_DENIED: {
    icon: <Lock size={16} />,
    title: "Outside your jurisdiction scope",
    body: () => "Access is logged.",
    tone: "governance",
  },
  NOT_FOUND: {
    icon: <SearchX size={16} />,
    title: "No record for this reference",
    body: () => "Check the identifier or search for it.",
    tone: "info",
  },
  RATE_LIMITED: {
    icon: <Clock size={16} />,
    title: "Rate limited",
    body: () => "Please retry shortly.",
    tone: "info",
  },
  DEPENDENCY_UNAVAILABLE: {
    icon: <WifiOff size={16} />,
    title: "Serving what we can",
    body: () => "A dependency is unavailable — showing cached or partial data.",
    tone: "info",
  },
  DEGRADED_RESULT: {
    icon: <WifiOff size={16} />,
    title: "Degraded result",
    body: () => "Content may be stale; the system status reflects the level.",
    tone: "info",
  },
  VALIDATION_FAILED: {
    icon: <AlertTriangle size={16} />,
    title: "Check your input",
    body: (e) => e.message,
    tone: "info",
  },
  INTERNAL: {
    icon: <AlertTriangle size={16} />,
    title: "Something went wrong in this panel",
    body: (e) => (e.traceId ? `Trace ${e.traceId}` : "The rest of the page is unaffected."),
    tone: "failure",
  },
};

const TONE_CLASS: Record<Rendering["tone"], string> = {
  governance: "border-signal/40 text-ink-primary",
  info: "border-line text-ink-muted",
  failure: "border-risk-critical/50 text-ink-primary",
};

export function ErrorState({ error, onRetry }: ErrorStateProps) {
  const r = RENDERING[error.code] ?? RENDERING.INTERNAL;
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-start gap-2 rounded border bg-panel px-4 py-3",
        TONE_CLASS[r.tone],
      )}
    >
      <div className="flex items-center gap-2 text-body text-ink-primary">
        {r.icon}
        <span>{r.title}</span>
      </div>
      <p className="text-caption text-ink-muted">{r.body(error)}</p>
      {onRetry && error.retryable ? (
        <button
          type="button"
          onClick={onRetry}
          className="text-caption text-signal hover:underline"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}
