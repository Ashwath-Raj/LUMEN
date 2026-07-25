/**
 * Insights tab (E.4) — the case's §8 insights as `InsightCard`s. Each card
 * already renders summary, confidence + breakdown, factors, evidence,
 * limitations, recommendation, lineage, the §11 trust caveat, and the
 * classification/lifecycle badges  — so "no insight may render
 * without limitations" is structurally guaranteed here, not re-checked.
 *
 * Cards are compact-expandable in the feed; selecting one opens it in the
 * InspectorPanel (expanded) too, without leaving the workspace.
 */
import { useCaseInsights } from "@/api";
import { InsightCard } from "@/components/insight";
import { QueryBoundary } from "@/components/states";
import type { EntityRef } from "@/components/entity";
import type { Insight } from "@/types/contracts";

interface InsightsTabProps {
  caseId: string;
  onSelectInsight: (ref: EntityRef, insight: Insight) => void;
}

export function InsightsTab({ caseId, onSelectInsight }: InsightsTabProps) {
  const insights = useCaseInsights(caseId);

  return (
    <QueryBoundary
      query={insights}
      emptyMessage="No insights generated for this case yet. They appear here once the intelligence engine has run."
      isEmpty={(data) => data.length === 0}
      skeletonLines={8}
    >
      {(data) => (
        <div className="flex flex-col gap-3">
          {data.map((insight) => (
            <div key={insight.id} className="flex flex-col gap-1">
              <InsightCard insight={insight} />
              <button
                type="button"
                onClick={() =>
                  onSelectInsight(
                    { kind: "insight", id: insight.id, label: insight.headline },
                    insight,
                  )
                }
                className="self-start text-caption text-signal hover:underline"
              >
                Open in inspector
              </button>
            </div>
          ))}
        </div>
      )}
    </QueryBoundary>
  );
}
