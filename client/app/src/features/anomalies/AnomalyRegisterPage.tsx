/**
 * Anomaly Register — `/anomalies` (E.8, §13). The anomaly-kind insights from
 * the real feed (`/intelligence/workbench?kind=anomaly`), ranked newest first —
 * where the Command stat and the alert tray land. Each renders as a full
 * InsightCard (baseline · σ · limitations per §13).
 */
import { useInsights } from "@/api";
import { InsightCard } from "@/components/insight";
import { QueryBoundary } from "@/components/states";

export default function AnomalyRegisterPage() {
  const anomalies = useInsights({ kind: "anomaly", limit: 100 });

  return (
    <div className="min-h-0 flex-1 overflow-auto">
      <div className="mx-auto flex max-w-4xl flex-col gap-4 p-6">
        <header className="flex flex-col gap-1">
          <h1 className="font-display text-page-title text-ink-primary">
            Anomaly Register
          </h1>
          <p className="text-caption text-ink-muted">
            Volume anomalies against the district baseline (§13) — detections,
            not conclusions; each carries its limitations.
          </p>
        </header>

        <QueryBoundary
          query={anomalies}
          emptyMessage="No anomalies detected in the current window."
          degradedMessage="The anomaly feed is unavailable — detections appear when the insight service is reachable."
          isEmpty={(d) => d.items.length === 0}
          skeletonLines={6}
        >
          {(d) => (
            <div className="flex flex-col gap-2">
              {d.items.map((i) => (
                <InsightCard key={i.id} insight={i} defaultExpanded />
              ))}
            </div>
          )}
        </QueryBoundary>
      </div>
    </div>
  );
}
