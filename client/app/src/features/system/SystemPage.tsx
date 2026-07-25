/**
 * System — `/system` (E.10, §22/§24/§25/§17.4). Judge-facing ops surfaces, all
 * real: health (dependency states + §24.2 ladder), metrics (insight counts, AI
 * latency, fallback rate), registries (services · models · prompts), and the
 * eval scorecard (question count / last run — states plainly when no eval run
 * has been recorded yet).
 */
import {
  useSystemEval,
  useSystemHealth,
  useSystemMetrics,
  useSystemRegistry,
} from "@/api";
import { QueryBoundary } from "@/components/states";
import { Badge, Panel } from "@/design/primitives";

export default function SystemPage() {
  const health = useSystemHealth();
  const metrics = useSystemMetrics();
  const registry = useSystemRegistry();
  const evalQ = useSystemEval();

  return (
    <div className="min-h-0 flex-1 overflow-auto">
      <div className="mx-auto flex max-w-5xl flex-col gap-4 p-6">
        <h1 className="font-display text-page-title text-ink-primary">System</h1>

        <Panel className="p-4">
          <h2 className="mb-3 text-caption uppercase tracking-wide text-ink-muted">
            Health · §24.2 degradation ladder
          </h2>
          <QueryBoundary
            query={health}
            emptyMessage="No health report available."
            degradedMessage="The health surface is unavailable."
            skeletonLines={3}
          >
            {(h) => (
              <div className="flex flex-col gap-2">
                <p className="font-mono text-body text-signal">{h.degradation_label}</p>
                <div className="flex flex-wrap gap-1.5">
                  {h.dependencies.map((d) => (
                    <Badge
                      key={d.dependency}
                      tone={d.state === "up" ? "var(--confidence-high)" : d.state === "unknown" ? undefined : "var(--state-degraded)"}
                    >
                      {d.dependency} · {d.state}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </QueryBoundary>
        </Panel>

        <Panel className="p-4">
          <h2 className="mb-3 text-caption uppercase tracking-wide text-ink-muted">
            Metrics · §25
          </h2>
          <QueryBoundary
            query={metrics}
            emptyMessage="No metrics recorded yet."
            degradedMessage="The metrics surface is unavailable."
            skeletonLines={4}
          >
            {(mx) => (
              <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-caption md:grid-cols-3">
                <Metric label="insights total" value={mx.insight_counts.total} />
                {Object.entries(mx.insight_counts.by_kind).map(([k, v]) => (
                  <Metric key={k} label={`· ${k}`} value={v} />
                ))}
                <Metric label="AI queries" value={mx.ai.ai_queries_total} />
                <Metric label="fallback rate" value={`${Math.round(mx.ai.fallback_rate * 100)}%`} />
                <Metric label="AI p95 latency" value={`${mx.ai.ai_latency_ms?.p95_ms ?? "—"} ms`} />
                <Metric label="policy denials" value={mx.policy_denials.total} />
              </dl>
            )}
          </QueryBoundary>
        </Panel>

        <Panel className="p-4">
          <h2 className="mb-3 text-caption uppercase tracking-wide text-ink-muted">
            Registries · §22
          </h2>
          <QueryBoundary
            query={registry}
            emptyMessage="No registry entries."
            degradedMessage="The registry surface is unavailable."
            skeletonLines={4}
          >
            {(r) => (
              <div className="flex flex-col gap-2">
                <p className="text-caption text-ink-muted">
                  services {r.services.total} · models {r.models.total}
                  {r.prompts ? ` · prompts ${r.prompts.total}` : ""}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {r.models.items.map((mdl) => (
                    <Badge key={String(mdl.model_id ?? mdl.name)} tone={mdl.active ? "var(--signal)" : undefined}>
                      <span className="font-mono">{String(mdl.model_id ?? mdl.name)}</span>
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </QueryBoundary>
        </Panel>

        <Panel className="p-4">
          <h2 className="mb-3 text-caption uppercase tracking-wide text-ink-muted">
            Eval scorecard · §17.4
          </h2>
          <QueryBoundary
            query={evalQ}
            emptyMessage="No evaluation run recorded."
            degradedMessage="The eval surface is unavailable."
            skeletonLines={2}
          >
            {(e) =>
              e.run_id ? (
                <div className="flex flex-col gap-3">
                  <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-caption md:grid-cols-3">
                    <Metric label="run" value={e.run_id} />
                    <Metric label="golden questions" value={e.question_count} />
                    <Metric label="prompt" value={e.prompt_version ?? "—"} />
                  </dl>
                  <div className="flex flex-col gap-1.5 border-t border-line pt-3">
                    <ScoreLine label="groundedness" value={e.groundedness} target={1.0} />
                    <ScoreLine label="answer correctness" value={e.correctness} target={0.85} />
                    <ScoreLine
                      label="hallucinated ids"
                      value={e.hallucinated_ids_total}
                      target={0}
                      lowerIsBetter
                      raw
                    />
                  </div>
                </div>
              ) : (
                <p className="text-caption text-ink-muted">
                  No golden-set evaluation has been run against this deployment
                  yet. Run <span className="font-mono">scripts/eval.py</span> to
                  populate the §17 scorecard.
                </p>
              )
            }
          </QueryBoundary>
        </Panel>
      </div>
    </div>
  );
}

/** One §17.2 metric against its target — pass/fail is stated, never implied. */
function ScoreLine({
  label,
  value,
  target,
  lowerIsBetter = false,
  raw = false,
}: {
  label: string;
  value: number | undefined;
  target: number;
  lowerIsBetter?: boolean;
  raw?: boolean;
}) {
  if (value === undefined) return null;
  const pass = lowerIsBetter ? value <= target : value >= target;
  return (
    <div className="flex items-center gap-3 text-caption">
      <span className="w-40 shrink-0 text-ink-muted">{label}</span>
      <span className="w-16 font-mono text-ink-primary">
        {raw ? value : value.toFixed(3)}
      </span>
      <span className="w-24 text-ink-faint">target {raw ? target : target.toFixed(2)}</span>
      <Badge tone={pass ? "var(--confidence-high)" : "var(--risk-high)"}>
        {pass ? "PASS" : "FAIL"}
      </Badge>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="contents">
      <dt className="text-ink-faint">{label}</dt>
      <dd className="font-mono text-ink-primary">{value}</dd>
    </div>
  );
}
