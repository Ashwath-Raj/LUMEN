/**
 * `DegradedState` — the calm "not available yet / temporarily unavailable" panel
 * for `DEPENDENCY_UNAVAILABLE` / `DEGRADED_RESULT` (§24.2, §29.3). Distinct from
 * `ErrorState`'s red failure styling: an unimplemented or degraded endpoint is an
 * expected operational state, not a defect, so it reads as a status notice — the
 * §B stance that governance/degradation are features, not errors.
 *
 * Used by `QueryBoundary` when a query fails with an unavailability code, so
 * pages (e.g. the Case Registry against a 501 backend) show a proper degraded UI
 * rather than an error boundary.
 */
import { CloudOff } from "lucide-react";

import { Button } from "@/design/primitives";

interface DegradedStateProps {
  message?: string;
  onRetry?: () => void;
}

export function DegradedState({ message, onRetry }: DegradedStateProps) {
  return (
    <div
      role="status"
      className="flex flex-col items-center justify-center gap-3 px-6 py-12 text-center"
    >
      <CloudOff size={24} strokeWidth={1.5} className="text-degraded" aria-hidden />
      <p className="max-w-sm text-body text-ink-primary">
        {message ?? "This data isn’t available yet."}
      </p>
      <p className="max-w-sm text-caption text-ink-muted">
        The service will populate this view automatically once its endpoint is
        live. Nothing is wrong with your session.
      </p>
      {onRetry ? (
        <Button variant="secondary" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}
