/**
 * The Case Registry's declarative filter fields (E.3) — bound to the §29.1
 * `GET /cases` params. Consumed by the shared `FilterBar` (D11). Select options
 * come from `useCaseLookups` when available; risk band and investigation stage
 * are fixed enumerations (§9 / §2.1), so their options are inlined here.
 */
import type { FilterField, FilterOption } from "@/components/filters";
import type { CaseLookups } from "@/types/caseFilters";

const RISK_BAND_OPTIONS: FilterOption[] = [
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

const STAGE_OPTIONS: FilterOption[] = [
  { value: "incident", label: "Incident" },
  { value: "info_received", label: "Information received" },
  { value: "registered", label: "Registered" },
  { value: "arrest", label: "Arrest" },
  { value: "chargesheet", label: "Chargesheet" },
];

function toOptions(list: CaseLookups[keyof CaseLookups] | undefined): FilterOption[] {
  return (list ?? []).map((o) => ({ value: o.id, label: o.label }));
}

/**
 * Build the field config, injecting lookup options where the backend provides
 * them; fields with no options fall back to free-text entry in the FilterBar.
 */
export function buildCaseFilterFields(
  lookups: CaseLookups | undefined,
): FilterField[] {
  return [
    { key: "crime_head", label: "Crime Head", kind: "select", options: toOptions(lookups?.crime_heads) },
    { key: "crime_sub_head", label: "Crime Sub Head", kind: "select", options: toOptions(lookups?.crime_sub_heads) },
    { key: "district", label: "District", kind: "select", options: toOptions(lookups?.districts) },
    { key: "station", label: "Police Station", kind: "select", options: toOptions(lookups?.stations) },
    { key: "status", label: "Status", kind: "select", options: toOptions(lookups?.statuses) },
    { key: "category", label: "Category", kind: "select", options: toOptions(lookups?.categories) },
    { key: "gravity", label: "Priority", kind: "select", options: toOptions(lookups?.gravities) },
    { key: "risk_band", label: "Risk Band", kind: "select", options: RISK_BAND_OPTIONS },
    { key: "stage", label: "Investigation Stage", kind: "select", options: STAGE_OPTIONS },
    {
      key: "date_range",
      label: "Date Range",
      kind: "daterange",
      rangeKeys: { from: "date_from", to: "date_to" },
    },
  ];
}
