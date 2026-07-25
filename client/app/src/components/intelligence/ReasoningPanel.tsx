/**
 * `ReasoningPanel` — the collapsible "how the AI got here" block (Part 2
 * collapsible reasoning; Part 7 explainability): confidence decomposition,
 * contributing factors, counterfactuals, and full lineage. COMPOSES the
 * Session-1 insight sub-components — one rendering of each concept everywhere
 * (no duplicated UI logic).
 */
import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

import { ConfidenceBreakdown, FactorBars } from "@/components/confidence";
import { CounterfactualsNote, LineagePanel } from "@/components/insight";
import type { Insight } from "@/types/contracts";

export function ReasoningPanel({
  insight,
  defaultOpen = false,
}: {
  insight: Insight;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section aria-label="Reasoning" className="flex flex-col gap-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex items-center gap-1.5 text-caption uppercase tracking-wide text-ink-muted hover:text-ink-primary"
      >
        {open ? (
          <ChevronDown size={14} aria-hidden />
        ) : (
          <ChevronRight size={14} aria-hidden />
        )}
        Reasoning
      </button>

      {open ? (
        <div className="flex flex-col gap-4 border-l border-line pl-4">
          <ConfidenceBreakdown breakdown={insight.confidence_breakdown} />
          {insight.factors.length ? (
            <FactorBars factors={insight.factors} />
          ) : null}
          <CounterfactualsNote counterfactuals={insight.counterfactuals} />
          <LineagePanel lineage={insight.lineage} />
        </div>
      ) : null}
    </section>
  );
}
