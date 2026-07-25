/**
 * `RecommendationSection` (part of D1) — the "what should the officer do next"
 * answer (§A question 7, §18 decision support). In the §8 model a recommendation
 * IS an insight (`kind="recommendation"`, `headline` = the plain suggestion), so
 * this section surfaces the headline as the action and always attaches the §11
 * recommendation caveat ("Suggestion for officer review. Not an instruction.")
 * as a default — LUMEN stops at the human decision (§11).
 *
 * Only rendered for recommendation-kind insights; the card decides when to show
 * it. Kept a component so the "next step" framing is consistent everywhere.
 */
import { ArrowRight } from "lucide-react";

import { TrustBadge } from "@/components/trust";

interface RecommendationSectionProps {
  headline: string;
}

export function RecommendationSection({ headline }: RecommendationSectionProps) {
  return (
    <section
      aria-label="Recommended next step"
      className="flex flex-col gap-1.5 rounded border border-signal/30 bg-raised/40 px-3 py-2"
    >
      <h4 className="flex items-center gap-1.5 text-caption uppercase tracking-wide text-signal">
        <ArrowRight size={12} strokeWidth={1.5} aria-hidden />
        Recommended next step
      </h4>
      <p className="text-body text-ink-primary">{headline}</p>
      <TrustBadge context="recommendation" />
    </section>
  );
}
