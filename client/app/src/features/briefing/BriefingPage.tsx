/**
 * Intelligence Briefing — `/briefing` (C.3). The shift-start page: one overview
 * call + the top insights, every number a link onward. Reached any time via the
 * shell wordmark. All real data (`/dashboard/summary`, `/intelligence/workbench`).
 */
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";

import { useInsights, useOverview } from "@/api";
import { InsightCard } from "@/components/insight";
import { QueryBoundary } from "@/components/states";
import { Button, Stat } from "@/design/primitives";
import { useSession } from "@/providers/sessionContext";

export default function BriefingPage() {
  const navigate = useNavigate();
  const { operator } = useSession();
  const overview = useOverview();
  const top = useInsights({ limit: 6 });

  const today = new Date().toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <div className="min-h-0 flex-1 overflow-auto">
      <div className="mx-auto flex max-w-4xl flex-col gap-6 p-8">
        <header className="flex flex-col gap-1">
          <h1 className="font-display text-page-title text-ink-primary">
            Good day{operator ? `, ${operator.name}` : ""}
          </h1>
          <p className="text-caption text-ink-muted">{today} · scope: statewide</p>
        </header>

        <QueryBoundary
          query={overview}
          emptyMessage="No overview available for this shift."
          degradedMessage="The overview service is unavailable — headline figures return when it is."
          skeletonLines={4}
        >
          {(o) => (
            <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
              <Stat label="Priority cases" value={o.counts.priority_cases} onClick={() => navigate("/cases?gravity=1")} />
              <Stat label="Active anomalies" value={o.counts.active_anomalies} onClick={() => navigate("/anomalies")} />
              <Stat label="High-risk districts" value={o.counts.high_band_districts} onClick={() => navigate("/geo")} />
              <Stat label="Awaiting review" value={o.counts.recommendations_awaiting_review} onClick={() => navigate("/ask")} />
            </div>
          )}
        </QueryBoundary>

        <section className="flex flex-col gap-2">
          <h2 className="text-caption uppercase tracking-wide text-ink-muted">
            Top insights since last session
          </h2>
          <QueryBoundary
            query={top}
            emptyMessage="No new intelligence since your last session."
            degradedMessage="The insight feed is unavailable."
            isEmpty={(d) => d.items.length === 0}
            skeletonLines={5}
          >
            {(d) => (
              <div className="flex flex-col gap-2">
                {d.items.map((i) => (
                  <InsightCard key={i.id} insight={i} />
                ))}
              </div>
            )}
          </QueryBoundary>
        </section>

        <div>
          <Link to="/command">
            <Button variant="primary">
              Begin — open Command Center
              <ArrowRight size={14} aria-hidden />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
