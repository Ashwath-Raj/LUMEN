/**
 * Case Registry — `/cases` (E.3). The analyst's worklist and the product's text
 * entry point: "the Whitefield burglary from March" is findable without its
 * number. FilterBar (D11) + DataGrid, server-side pagination, multi-column sort,
 * every filter round-tripping through the URL (§C "URL is state").
 *
 * This is feature ASSEMBLY only (arch §G): all reusable parts come from
 * `components/` and `design/` — the page owns the URL↔filter wiring, the query,
 * and the row→workspace navigation, nothing reusable-looking.
 *
 * States: the grid is wrapped in `QueryBoundary`, so Loading (delayed skeleton),
 * Error (§29.3-mapped, incl. SCOPE_DENIED governance notice), Empty ("no cases
 * match"), and Degraded (staleness banner) are all handled without bespoke code.
 */
import { useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useCases, useCaseLookups } from "@/api";
import { FilterBar } from "@/components/filters";
import { QueryBoundary } from "@/components/states";
import { DataGrid, Pagination, type SortTerm } from "@/design/primitives";
import type { CaseListItem } from "@/types/case";
import type { CaseFilters } from "@/types/caseFilters";
import {
  activeFilterEntries,
  readCaseFilters,
  writeCaseFilters,
} from "@/utils/caseFilterState";
import { writeParams } from "@/utils/urlState";

import { buildCaseFilterFields } from "./caseFilterFields";
import { CASE_COLUMNS } from "./caseColumns";

export default function CaseRegistryPage() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();

  const filters = useMemo(() => readCaseFilters(params), [params]);
  const casesQuery = useCases(filters);
  const lookupsQuery = useCaseLookups();

  const fields = useMemo(
    () => buildCaseFilterFields(lookupsQuery.data),
    [lookupsQuery.data],
  );

  // Filter values as flat strings for the FilterBar (from the URL).
  const filterValues = useMemo(() => {
    const values: Record<string, string | undefined> = {};
    for (const { key, value } of activeFilterEntries(filters)) {
      values[key] = value;
    }
    values.date_from = filters.date_from;
    values.date_to = filters.date_to;
    return values;
  }, [filters]);

  function patch(next: Partial<CaseFilters>) {
    setParams(writeCaseFilters(params, next));
  }

  /** FilterBar sets arbitrary param keys (bound to endpoint params); write the
   *  raw key to the URL and reset paging, mirroring writeCaseFilters' policy. */
  function setFilterValue(key: string, value: string | undefined) {
    const nextParams = writeParams(params, {
      [key]: value ?? null,
      offset: null,
    });
    setParams(nextParams);
  }

  const sortTerms: SortTerm[] = filters.sort ?? [];

  function toggleSort(field: string) {
    const existing = sortTerms.find((s) => s.field === field);
    let next: SortTerm[];
    if (!existing) {
      next = [...sortTerms, { field, direction: "asc" }];
    } else if (existing.direction === "asc") {
      next = sortTerms.map((s) =>
        s.field === field ? { ...s, direction: "desc" as const } : s,
      );
    } else {
      next = sortTerms.filter((s) => s.field !== field);
    }
    patch({ sort: next });
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 p-6">
      <header className="flex items-baseline justify-between">
        <h1 className="font-display text-page-title text-ink-primary">Cases</h1>
        <span className="text-caption text-ink-muted">Your assigned scope</span>
      </header>

      <FilterBar
        fields={fields}
        values={filterValues}
        onChange={setFilterValue}
        q={filters.q ?? ""}
        onSearch={(q) => patch({ q })}
        onClearAll={() => setParams(new URLSearchParams())}
      />

      <div className="min-h-0 flex-1 overflow-auto rounded border border-line bg-panel">
        <QueryBoundary
          query={casesQuery}
          emptyMessage="No cases match these filters. Adjust or clear them to widen the search."
          degradedMessage="The case registry isn’t available yet. It will populate automatically once the /cases endpoint is live."
          isEmpty={(data) => data.items.length === 0}
          skeletonLines={10}
        >
          {(data) => (
            <>
              <DataGrid<CaseListItem>
                columns={CASE_COLUMNS}
                rows={data.items}
                rowKey={(c) => c.case_master_id}
                caption="Case registry"
                sort={sortTerms}
                onToggleSort={toggleSort}
                onOpen={(c) => navigate(`/case/${c.case_master_id}`)}
              />
              <Pagination
                total={data.total}
                limit={data.limit}
                offset={data.offset}
                onOffsetChange={(offset) => patch({ offset })}
              />
            </>
          )}
        </QueryBoundary>
      </div>
    </div>
  );
}
