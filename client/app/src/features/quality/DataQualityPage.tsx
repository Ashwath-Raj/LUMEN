/**
 * Data Quality — `/quality` (E.9, §5.3, §30.9). An administrative product, not
 * a defect list: the six §5.2 dimensions per district (real `/quality/scores`)
 * and the top rules firing (real `/quality/findings`, Q01–Q18 with plain
 * names). Framed as "which stations would benefit from data-entry support."
 */
import { useMemo } from "react";

import { useQualityFindings, useQualityScores } from "@/api";
import { QueryBoundary } from "@/components/states";
import { QualityBadge } from "@/components/trust";
import { DataGrid, Panel, type Column } from "@/design/primitives";
import type { QualityFindingRow } from "@/api";

/** §5.1 rule catalogue — plain-language names (subset actually fired shows). */
const RULE_NAME: Record<string, string> = {
  Q01: "Missing coordinates",
  Q02: "Impossible coordinates",
  Q03: "Malformed CrimeNo",
  Q04: "CrimeNo/unit mismatch",
  Q05: "Incident after registration",
  Q06: "Info received before incident",
  Q07: "Chargesheet before registration",
  Q08: "Arrest before incident",
  Q09: "Orphan child row",
  Q10: "Broken lookup reference",
  Q11: "Head/sub-head disagreement",
  Q12: "Duplicate case suspicion",
  Q13: "Implausible age",
  Q14: "Accused with no PersonID",
  Q15: "Case with no charges",
  Q16: "Stale open case",
  Q17: "Inactive act/section in use",
  Q18: "Empty BriefFacts",
};

const FINDING_COLUMNS: Column<QualityFindingRow>[] = [
  {
    key: "rule",
    header: "Rule",
    render: (f) => (
      <span className="text-ink-primary">
        <span className="font-mono text-ink-muted">{f.rule_id}</span>{" "}
        {RULE_NAME[f.rule_id] ?? ""}
      </span>
    ),
  },
  { key: "severity", header: "Severity", render: (f) => <span className="text-ink-muted">{f.severity}</span> },
  {
    key: "entity",
    header: "Entity",
    render: (f) => (
      <span className="font-mono text-ink-muted">
        {f.entity_type} {f.entity_id}
      </span>
    ),
  },
  { key: "detail", header: "Detail", render: (f) => <span className="text-ink-faint">{f.detail ?? "—"}</span> },
];

export default function DataQualityPage() {
  const scores = useQualityScores("district");
  const findings = useQualityFindings(undefined, 100);

  return (
    <div className="min-h-0 flex-1 overflow-auto">
      <div className="mx-auto flex max-w-5xl flex-col gap-4 p-6">
        <header className="flex flex-col gap-1">
          <h1 className="font-display text-page-title text-ink-primary">Data Quality</h1>
          <p className="text-caption text-ink-muted">
            §5.2 dimension scores per district — an administrative view of which
            scopes would benefit from data-entry support.
          </p>
        </header>

        <Panel className="p-4">
          <h2 className="mb-3 text-caption uppercase tracking-wide text-ink-muted">
            District dimension scores
          </h2>
          <QueryBoundary
            query={scores}
            emptyMessage="No quality scores computed yet — the quality precompute has not produced district scopes."
            degradedMessage="The quality service is unavailable."
            isEmpty={(d) => d.scores.length === 0}
            skeletonLines={4}
          >
            {(d) => <ScoreGrid rows={d.scores} />}
          </QueryBoundary>
        </Panel>

        <Panel className="p-4">
          <h2 className="mb-3 text-caption uppercase tracking-wide text-ink-muted">
            Findings (Q01–Q18)
          </h2>
          <QueryBoundary
            query={findings}
            emptyMessage="No open quality findings — every rule passed on the last run."
            degradedMessage="The findings service is unavailable."
            isEmpty={(d) => d.findings.length === 0}
            skeletonLines={6}
          >
            {(d) => (
              <DataGrid<QualityFindingRow>
                columns={FINDING_COLUMNS}
                rows={d.findings}
                rowKey={(f) => String(f.finding_id)}
                caption="Quality findings"
              />
            )}
          </QueryBoundary>
        </Panel>
      </div>
    </div>
  );
}

function ScoreGrid({
  rows,
}: {
  rows: Array<{ scope_id: string; dimension: string; score: number }>;
}) {
  const byDistrict = useMemo(() => {
    const map = new Map<string, Array<{ dimension: string; score: number }>>();
    for (const r of rows) {
      const list = map.get(r.scope_id) ?? [];
      list.push({ dimension: r.dimension, score: r.score });
      map.set(r.scope_id, list);
    }
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [rows]);

  return (
    <div className="flex flex-col gap-3">
      {byDistrict.map(([district, dims]) => (
        <div key={district} className="flex flex-wrap items-center gap-2">
          <span className="w-28 shrink-0 text-body text-ink-primary">
            District {district}
          </span>
          {dims
            .sort((a, b) => a.dimension.localeCompare(b.dimension))
            .map((d) => (
              <QualityBadge
                key={d.dimension}
                score={d.score}
                dimension={d.dimension as never}
              />
            ))}
        </div>
      ))}
    </div>
  );
}
