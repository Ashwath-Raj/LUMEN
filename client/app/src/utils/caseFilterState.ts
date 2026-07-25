/**
 * Case Registry filter ⇄ URL serialization (arch §C "URL is state", E.3 "every
 * filter must synchronize with the URL"). Pure functions over URLSearchParams,
 * built on the shared `urlState` helpers — the one place `CaseFilters` maps to
 * query params, so the page never hand-rolls param parsing (no duplicated logic).
 *
 * Multi-column sort serializes as `sort=field:dir,field:dir` (E.3 multi-sort).
 * Pagination uses the shared §29.2 `limit`/`offset` convention.
 */
import type { RiskBand } from "@/design/tokens";
import type {
  CaseFilters,
  SortDirection,
  SortSpec,
} from "@/types/caseFilters";
import type { TimelineEventKind } from "@/types/timeline";

import { readNumber, readParam, writeParams } from "./urlState";

const RISK_BANDS: readonly RiskBand[] = ["critical", "high", "medium", "low"];
const STAGES: readonly TimelineEventKind[] = [
  "incident",
  "info_received",
  "registered",
  "arrest",
  "chargesheet",
];

/** The string filter keys that map 1:1 to a query param. */
const STRING_KEYS = [
  "q",
  "crime_head",
  "crime_sub_head",
  "gravity",
  "status",
  "category",
  "district",
  "station",
  "date_from",
  "date_to",
] as const;

function parseSort(raw: string): SortSpec[] {
  if (!raw) return [];
  return raw
    .split(",")
    .map((token) => token.trim())
    .filter(Boolean)
    .map((token) => {
      const [field, dir] = token.split(":");
      const direction: SortDirection = dir === "desc" ? "desc" : "asc";
      return field ? { field, direction } : null;
    })
    .filter((s): s is SortSpec => s !== null);
}

function serializeSort(sort: SortSpec[] | undefined): string {
  if (!sort || sort.length === 0) return "";
  return sort.map((s) => `${s.field}:${s.direction}`).join(",");
}

/** Read `CaseFilters` from the URL params (the single source of view state). */
export function readCaseFilters(params: URLSearchParams): CaseFilters {
  const filters: CaseFilters = {
    limit: readNumber(params, "limit", 50),
    offset: readNumber(params, "offset", 0),
  };

  for (const key of STRING_KEYS) {
    const value = readParam(params, key);
    if (value) filters[key] = value;
  }

  const riskBand = readParam(params, "risk_band") as RiskBand;
  if (RISK_BANDS.includes(riskBand)) filters.risk_band = riskBand;

  const stage = readParam(params, "stage") as TimelineEventKind;
  if (STAGES.includes(stage)) filters.stage = stage;

  const sort = parseSort(readParam(params, "sort"));
  if (sort.length) filters.sort = sort;

  return filters;
}

/**
 * Merge a filter patch into the URL params. Changing any filter (except paging)
 * resets `offset` to 0 so a new query starts at page one — unless the patch sets
 * offset explicitly (pagination controls do).
 */
export function writeCaseFilters(
  current: URLSearchParams,
  patch: Partial<CaseFilters>,
): URLSearchParams {
  const flat: Record<string, string | number | null | undefined> = {};

  for (const [key, value] of Object.entries(patch)) {
    if (key === "sort") {
      flat.sort = serializeSort(value as SortSpec[] | undefined) || null;
    } else if (value === undefined || value === null || value === "") {
      flat[key] = null;
    } else {
      flat[key] = value as string | number;
    }
  }

  // Any non-paging change returns to page one.
  const changedNonPaging = Object.keys(patch).some(
    (k) => k !== "limit" && k !== "offset",
  );
  if (changedNonPaging && patch.offset === undefined) flat.offset = null;

  return writeParams(current, flat);
}

/** The active, user-facing filter chips (everything except paging/sort/q). */
export function activeFilterEntries(
  filters: CaseFilters,
): Array<{ key: keyof CaseFilters; value: string }> {
  const entries: Array<{ key: keyof CaseFilters; value: string }> = [];
  const skip = new Set(["q", "limit", "offset", "sort"]);
  for (const [key, value] of Object.entries(filters)) {
    if (skip.has(key) || value === undefined || value === null || value === "") {
      continue;
    }
    entries.push({ key: key as keyof CaseFilters, value: String(value) });
  }
  return entries;
}
