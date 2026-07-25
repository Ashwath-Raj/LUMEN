/**
 * `LineagePanel` (part of D1) — the §8 `Lineage`, the "what produced this"
 * answer (§A question 6, §11 gate 3): method, model version, prompt version,
 * features used, queries executed, source row count, quality score, and when it
 * was computed. This is the auditable provenance of the claim.
 *
 * The quality score reuses `QualityBadge` (§5.2) so provenance quality reads on
 * the same scale as everywhere else. Identifiers render in mono (§F: mono is for
 * identifiers only).
 */
import type { ReactNode } from "react";

import { QualityBadge } from "@/components/trust";
import type { Lineage } from "@/types/contracts";

interface LineagePanelProps {
  lineage: Lineage;
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <>
      <dt className="text-ink-faint">{label}</dt>
      <dd className="text-ink-muted">{children}</dd>
    </>
  );
}

export function LineagePanel({ lineage }: LineagePanelProps) {
  return (
    <section aria-label="Lineage" className="flex flex-col gap-2">
      <h4 className="text-caption uppercase tracking-wide text-ink-muted">
        Lineage
      </h4>
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-caption">
        <Row label="method">{lineage.method}</Row>
        <Row label="model">
          <span className="font-mono">{lineage.model_version}</span>
        </Row>
        {lineage.prompt_version ? (
          <Row label="prompt">
            <span className="font-mono">{lineage.prompt_version}</span>
          </Row>
        ) : null}
        <Row label="features">
          {lineage.features_used.length ? (
            <span className="font-mono">{lineage.features_used.join(", ")}</span>
          ) : (
            "—"
          )}
        </Row>
        <Row label="queries">
          {lineage.query_ids.length ? (
            <span className="font-mono">{lineage.query_ids.join(", ")}</span>
          ) : (
            "—"
          )}
        </Row>
        <Row label="source rows">{lineage.source_row_count.toLocaleString()}</Row>
        <Row label="data quality">
          <QualityBadge score={lineage.quality_score} />
        </Row>
        <Row label="computed">
          <span className="font-mono">{lineage.computed_at}</span>
        </Row>
      </dl>
    </section>
  );
}
