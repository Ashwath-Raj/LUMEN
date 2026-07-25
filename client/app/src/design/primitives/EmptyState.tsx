/**
 * `EmptyState` — always has copy, never a bare spinner (arch §F, §30.2).
 * Session 0 ships the primitive; feature sessions supply meaningful copy.
 */
import type { ReactNode } from "react";

interface EmptyStateProps {
  /** Required — an empty state without copy is a defect (arch §F). */
  message: string;
  action?: ReactNode;
}

export function EmptyState({ message, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-12 text-center">
      <p className="max-w-sm text-body text-ink-muted">{message}</p>
      {action}
    </div>
  );
}
