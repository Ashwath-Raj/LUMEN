/**
 * Evidence tab (E.4) — the case's evidence rendered with `EvidenceSection` /
 * `EvidenceRow` / `EvidenceChip` (D3). §8 models evidence as part of each
 * insight (`Insight.evidence`), and §29.1 defines no separate case-evidence
 * endpoint, so the case's evidence is the DEDUPED union of evidence across its
 * insights — not invented. Each item is a link (§8), carries expandable metadata
 * (the row variant), and shows the restricted state where masked (§4.2).
 *
 * Grouped by entity type so a large evidence set stays navigable. Restriction is
 * an optional predicate; role×classification masking is applied
 * server-side (§4.2) and the UI renders the masked state faithfully.
 */
import { useMemo } from "react";

import { useCaseInsights } from "@/api";
import { EvidenceSection } from "@/components/evidence";
import { QueryBoundary } from "@/components/states";
import type { Evidence } from "@/types/contracts";

/** Human labels for the §8 evidence entity groups. */
const GROUP_LABEL: Record<string, string> = {
  case: "Cases",
  person: "People",
  participant: "Participants",
  officer: "Officers",
  station: "Stations",
  jurisdiction: "Jurisdictions",
  court: "Courts",
  charge: "Charges",
  process_event: "Process events",
  kb_document: "Knowledge base",
};

function dedupe(evidence: Evidence[]): Evidence[] {
  const seen = new Map<string, Evidence>();
  for (const item of evidence) {
    seen.set(`${item.entity}:${item.id}`, item);
  }
  return [...seen.values()];
}

function groupByEntity(evidence: Evidence[]): Array<[string, Evidence[]]> {
  const groups = new Map<string, Evidence[]>();
  for (const item of evidence) {
    const list = groups.get(item.entity) ?? [];
    list.push(item);
    groups.set(item.entity, list);
  }
  return [...groups.entries()];
}

export function EvidenceTab({ caseId }: { caseId: string }) {
  const insights = useCaseInsights(caseId);

  // Grouping is computed at the top level (not inside the render prop) so the
  // hook order is stable regardless of the query state (Rules of Hooks).
  const groups = useMemo(() => {
    const items = insights.data ?? [];
    return groupByEntity(dedupe(items.flatMap((i) => i.evidence)));
  }, [insights.data]);

  return (
    <QueryBoundary
      query={insights}
      emptyMessage="No evidence linked to this case yet. Evidence appears here as insights cite canonical records."
      isEmpty={(data) => data.every((i) => i.evidence.length === 0)}
      skeletonLines={6}
    >
      {() => (
        <div className="flex flex-col gap-6">
          {groups.map(([entity, items]) => (
            <EvidenceSection
              key={entity}
              label={`${GROUP_LABEL[entity] ?? entity} (${items.length})`}
              evidence={items}
              variant="rows"
            />
          ))}
        </div>
      )}
    </QueryBoundary>
  );
}
