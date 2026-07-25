/**
 * `ActionRecommendationCard` — one suggested next action. The §11 caveat
 * ("Suggestion for officer review. Not an instruction.") is the component
 * default via `TrustBadge` — an action can never render without it. The
 * sibling of Session-1's `RecommendationSection` (which renders a
 * recommendation-KIND insight); this one renders a bare action string on
 * leads and AI answers.
 */
import { ArrowRight } from "lucide-react";

import { TrustBadge } from "@/components/trust";

export function ActionRecommendationCard({ action }: { action: string }) {
  return (
    <div className="flex flex-col gap-1 rounded border border-signal/30 bg-raised/40 px-3 py-2">
      <p className="flex items-start gap-1.5 text-caption text-ink-primary">
        <ArrowRight size={12} strokeWidth={1.5} className="mt-0.5 shrink-0 text-signal" aria-hidden />
        {action}
      </p>
      <TrustBadge context="recommendation" />
    </div>
  );
}
