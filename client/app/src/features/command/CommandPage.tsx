/**
 * Command Center — `/command` (E.1, §30.2). The operational landing page:
 * statewide situational awareness where EVERY element is an entry point.
 *
 * All widgets consume real endpoints: `/dashboard/summary` (counts · district
 * risk · trends · network figures · quality), `/dashboard/alerts` (anomaly
 * insights), `/intelligence/workbench` (live insight feed), `/investigation/
 * cases` (recent investigations), `/system/health` (§24.2 ladder). Widgets with
 * no rows render production empty states — never placeholder copy.
 */
import { Link, useNavigate } from "react-router-dom";
import { ArrowUpRight, Zap } from "lucide-react";

import {
  useActiveAlerts,
  useCases,
  useInsights,
  useOverview,
  useQualityScores,
  useSystemHealth,
} from "@/api";
import { CrimeNoDecoder } from "@/components/case/CrimeNoDecoder";
import { InsightCard } from "@/components/insight";
import { QueryBoundary } from "@/components/states";
import { RiskBand } from "@/components/trust";
import { Panel, Stat } from "@/design/primitives";
import type { RiskBand as RiskBandValue } from "@/design/tokens";

export default function CommandPage() {
  const navigate = useNavigate();
  const overview = useOverview();
  const insights = useInsights({ limit: 8 });
  const alerts = useActiveAlerts();
  const recentCases = useCases({ limit: 5, offset: 0 });
  const health = useSystemHealth();
  const quality = useQualityScores();
  // §5.2 statewide quality = mean of the recorded dimension scores. Numeric
  // quality lives on the quality surface (§8 invariant 1 keeps it off /overview).
  const statewideQuality =
    quality.data && quality.data.scores.length
      ? quality.data.scores.reduce((sum, r) => sum + r.score, 0) /
        quality.data.scores.length
      : null;

  return (
    <div className="min-h-0 flex-1 overflow-auto">
      <div className="mx-auto flex max-w-[1500px] flex-col gap-4 p-6">
        <header className="flex flex-wrap items-baseline gap-3">
          <h1 className="font-display text-page-title text-ink-primary">
            Command Center
          </h1>
          <span className="text-caption text-ink-muted">
            Statewide situational awareness · every figure is an entry point
          </span>
          {health.data ? (
            <span className="ml-auto font-mono text-caption text-ink-muted">
              system {health.data.degradation_label}
            </span>
          ) : null}
        </header>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[280px_1fr_360px]">
          {/* ── LEFT · KPI stats (each navigates, §30.2) ─────────────────── */}
          <div className="flex flex-col gap-2">
            <QueryBoundary
              query={overview}
              emptyMessage="No overview data in the current window."
              degradedMessage="The overview service is unavailable — counters return when it is."
              skeletonLines={8}
            >
              {(o) => (
                <>
                  <Stat label="Period cases" value={o.counts.period_cases} onClick={() => navigate("/cases")} />
                  <Stat label="Active anomalies" value={o.counts.active_anomalies} onClick={() => navigate("/anomalies")} />
                  <Stat label="High-band districts" value={o.counts.high_band_districts} onClick={() => navigate("/geo")} />
                  <Stat label="Priority cases" value={o.counts.priority_cases} hint="Heinous gravity" onClick={() => navigate("/cases?gravity=1")} />
                  <Stat label="Awaiting review" value={o.counts.recommendations_awaiting_review} hint="insights pre-approval" onClick={() => navigate("/ask")} />
                  <Stat
                    label="Statewide quality"
                    value={statewideQuality !== null ? statewideQuality.toFixed(2) : "—"}
                    hint="§5.2 mean of dimensions"
                    onClick={() => navigate("/quality")}
                  />

                </>
              )}
            </QueryBoundary>

            {/* Quick actions */}
            <Panel className="flex flex-col gap-1.5 p-3">
              <h3 className="flex items-center gap-1.5 text-caption uppercase tracking-wide text-ink-muted">
                <Zap size={12} aria-hidden /> Quick actions
              </h3>
              <QuickLink to="/cases" label="Search the case registry" />
              <QuickLink to="/ask" label="Ask the intelligence layer" />
              <QuickLink to="/geo" label="Open the Karnataka map" />
              <QuickLink to="/network" label="Run a network query" />
            </Panel>
          </div>

          {/* ── CENTRE · district risk + trends + recent cases ───────────── */}
          <div className="flex min-w-0 flex-col gap-4">
            <Panel className="p-4">
              <h2 className="mb-3 text-caption uppercase tracking-wide text-ink-muted">
                District risk summary
              </h2>
              <QueryBoundary
                query={overview}
                emptyMessage="No district risk has been computed for this window."
                degradedMessage="District risk is unavailable until the prediction tables are served."
                isEmpty={(o) => o.district_risk.length === 0}
                skeletonLines={4}
              >
                {(o) => (
                  <div className="flex flex-col gap-1.5">
                    {o.district_risk.map((d) => (
                      <button
                        key={d.district_id}
                        type="button"
                        onClick={() => navigate(`/geo?district=${d.district_id}`)}
                        className="flex items-center gap-3 rounded border border-line px-3 py-2 text-left hover:border-signal/40 hover:bg-raised"
                      >
                        <span className="min-w-0 flex-1 truncate text-body text-ink-primary">
                          {d.district_name}
                        </span>
                        <span className="font-mono text-caption text-ink-muted">
                          {d.case_count} cases
                        </span>
                        <RiskBand band={d.band as RiskBandValue} />
                        <ArrowUpRight size={14} className="text-ink-faint" aria-hidden />
                      </button>
                    ))}
                  </div>
                )}
              </QueryBoundary>
            </Panel>

            <Panel className="p-4">
              <h2 className="mb-3 text-caption uppercase tracking-wide text-ink-muted">
                12-month trend by crime head
              </h2>
              <QueryBoundary
                query={overview}
                emptyMessage="No registered cases in the trend window."
                degradedMessage="Trends are unavailable."
                isEmpty={(o) => o.trends.length === 0}
                skeletonLines={3}
              >
                {(o) => (
                  <div className="flex flex-col gap-3">
                    {o.trends.map((t) => (
                      <TrendRow key={t.crime_head} label={t.crime_head} points={t.points} />
                    ))}
                  </div>
                )}
              </QueryBoundary>
            </Panel>

            <Panel className="p-4">
              <h2 className="mb-3 text-caption uppercase tracking-wide text-ink-muted">
                Recent investigations
              </h2>
              <QueryBoundary
                query={recentCases}
                emptyMessage="No investigations registered yet."
                degradedMessage="The case service is unavailable."
                isEmpty={(d) => d.items.length === 0}
                skeletonLines={5}
              >
                {(d) => (
                  <div className="flex flex-col gap-1.5">
                    {d.items.map((c) => (
                      <button
                        key={c.case_master_id}
                        type="button"
                        onClick={() => navigate(`/case/${c.case_master_id}`)}
                        className="flex items-center gap-3 rounded border border-line px-3 py-2 text-left hover:border-signal/40 hover:bg-raised"
                      >
                        <CrimeNoDecoder crimeNo={c.crime_no} variant="compact" />
                        <span className="min-w-0 flex-1 truncate text-caption text-ink-muted">
                          {c.title} · {c.station_name}
                        </span>
                        <span className="font-mono text-caption text-ink-faint">
                          {c.crime_registered_date ?? ""}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </QueryBoundary>
            </Panel>
          </div>

          {/* ── RIGHT · alerts + live insight feed ───────────────────────── */}
          <div className="flex flex-col gap-4">
            <Panel className="p-4">
              <h2 className="mb-3 text-caption uppercase tracking-wide text-ink-muted">
                Recent alerts
              </h2>
              <QueryBoundary
                query={alerts}
                emptyMessage="No anomalies detected in the current window."
                degradedMessage="The alert feed is unavailable."
                skeletonLines={2}
              >
                {(rows) => (
                  <div className="flex flex-col gap-1.5">
                    {rows.map((a) => (
                      <button
                        key={a.id}
                        type="button"
                        onClick={() => navigate("/anomalies")}
                        className="flex flex-col gap-0.5 rounded border border-degraded/40 px-3 py-2 text-left hover:bg-raised"
                      >
                        <span className="text-caption text-ink-primary">{a.headline}</span>
                        <span className="font-mono text-[10px] text-ink-faint">
                          {a.subject_type} {a.subject_id} · {a.generated_at.slice(0, 10)}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </QueryBoundary>
            </Panel>

            <div className="flex flex-col gap-2">
              <h2 className="text-caption uppercase tracking-wide text-ink-muted">
                Live intelligence
              </h2>
              <QueryBoundary
                query={insights}
                emptyMessage="No intelligence generated yet — insights appear as the engine runs."
                degradedMessage="The insight feed is unavailable."
                isEmpty={(d) => d.items.length === 0}
                skeletonLines={6}
              >
                {(d) => (
                  <div className="flex flex-col gap-2">
                    {d.items.map((i) => (
                      <InsightCard key={i.id} insight={i} />
                    ))}
                  </div>
                )}
              </QueryBoundary>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function QuickLink({ to, label }: { to: string; label: string }) {
  return (
    <Link
      to={to}
      className="flex items-center gap-2 rounded px-2 py-1.5 text-caption text-ink-muted hover:bg-raised hover:text-signal"
    >
      <ArrowUpRight size={12} aria-hidden />
      {label}
    </Link>
  );
}

/** Minimal inline trend bars — §B forbids decorative charts; this is data-dense. */
function TrendRow({
  label,
  points,
}: {
  label: string;
  points: Array<{ month: string; count: number }>;
}) {
  const max = Math.max(...points.map((p) => p.count), 1);
  return (
    <div className="flex items-center gap-3">
      <span className="w-36 shrink-0 truncate text-caption text-ink-muted">{label}</span>
      <div className="flex h-8 flex-1 items-end gap-0.5" role="img" aria-label={`${label} monthly counts`}>
        {points.map((p) => (
          <div
            key={p.month}
            title={`${p.month}: ${p.count}`}
            className="min-w-[6px] flex-1 rounded-t bg-signal/40"
            style={{ height: `${Math.max(8, (p.count / max) * 100)}%` }}
          />
        ))}
      </div>
      <span className="w-10 shrink-0 text-right font-mono text-caption text-ink-muted">
        {points.reduce((s, p) => s + p.count, 0)}
      </span>
    </div>
  );
}
