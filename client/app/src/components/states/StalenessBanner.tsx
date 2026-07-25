/**
 * `StalenessBanner` — the degraded-data notice (arch §E, §24.2). When the last
 * envelope reported `degradation_level ≠ L0`, content still renders but is
 * flagged as possibly stale ("serving cached data") and the shell pill turns
 * `--state-degraded`. This is the panel-level companion to the shell
 * `DegradationPill`.
 *
 * It reads the level from the session (published by the envelope client), so any
 * panel can show it without threading meta through props. At L0 it renders
 * nothing.
 */
import { CloudOff } from "lucide-react";

import { useSession } from "@/providers/sessionContext";
import { cn } from "@/utils/cn";

const NOTE: Record<string, string> = {
  L1: "Serving cached data — a dependency is slow or unavailable.",
  L2: "Serving precomputed data — live computation is unavailable.",
  L3: "Serving a deterministic fallback — the AI layer is unavailable.",
  L4: "Read-only — the system is serving retained data only.",
};

export function StalenessBanner({ className }: { className?: string }) {
  const { degradationLevel } = useSession();
  if (degradationLevel === "L0") return null;

  return (
    <div
      role="status"
      className={cn(
        "flex items-center gap-2 rounded border border-degraded/50 bg-panel px-3 py-2",
        "text-caption text-degraded",
        className,
      )}
    >
      <CloudOff size={14} strokeWidth={1.5} aria-hidden />
      <span>{NOTE[degradationLevel] ?? "Degraded — data may be stale."}</span>
    </div>
  );
}
