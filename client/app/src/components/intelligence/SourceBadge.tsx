/**
 * `SourceBadge` — source attribution for an AI answer (Part 7 explainability):
 * the generation method (with the §16.4 `deterministic_fallback` made VISIBLE,
 * never hidden), the model version, and how many evidence records ground the
 * answer. Everything comes from the §8 lineage — no attribution is invented.
 */
import { Badge } from "@/design/primitives";
import type { Insight } from "@/types/contracts";

export function SourceBadge({ insight }: { insight: Insight }) {
  const method = insight.lineage.method;
  const fallback = method === "deterministic_fallback";
  return (
    <span className="inline-flex flex-wrap items-center gap-1.5">
      <Badge
        tone={fallback ? "var(--state-degraded)" : undefined}
        title={`Generation method: ${method} · model ${insight.lineage.model_version}`}
      >
        {fallback ? "deterministic fallback" : method || "method unknown"}
      </Badge>
      <Badge title="Evidence records grounding this answer (§8)">
        {insight.evidence.length} source
        {insight.evidence.length === 1 ? "" : "s"}
      </Badge>
    </span>
  );
}
