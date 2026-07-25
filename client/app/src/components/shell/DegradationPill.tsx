/**
 * `DegradationPill` (D13) — the §24.2 ladder in the shell. Reads the current
 * level from the session (which the envelope client publishes on every
 * response). L0 is neutral; ≥ L1 turns `--state-degraded` (arch §D13, §E:
 * "serving cached data from HH:MM"). Per-dependency detail lives on `/system`.
 */
import { useSession } from "@/providers/sessionContext";
import { cn } from "@/utils/cn";

const LABEL: Record<string, string> = {
  L0: "L0 · Full",
  L1: "L1 · Cached",
  L2: "L2 · Precomputed",
  L3: "L3 · Deterministic",
  L4: "L4 · Read-only",
};

export function DegradationPill() {
  const { degradationLevel } = useSession();
  const degraded = degradationLevel !== "L0";
  return (
    <span
      className={cn(
        "rounded border px-2 py-1 text-caption",
        degraded
          ? "border-degraded/50 text-degraded"
          : "border-line text-ink-muted",
      )}
      title="System degradation level (§24.2)"
    >
      {LABEL[degradationLevel] ?? degradationLevel}
    </span>
  );
}
