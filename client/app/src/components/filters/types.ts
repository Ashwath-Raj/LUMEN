/**
 * Declarative filter-field config for the shared `FilterBar` (D11). A filter set
 * is described as data, not markup, so ONE FilterBar implementation serves
 * `/cases`, `/anomalies`, the insight feed and `/quality` (arch D11 "One
 * implementation"). The config is bound to an endpoint's params (arch D11); the
 * FilterBar renders each field's control from its `kind`.
 */

export type FilterKind = "select" | "text" | "date" | "daterange";

/** One selectable option for a select field. */
export interface FilterOption {
  value: string;
  label: string;
}

/** One declarative filter field. */
export interface FilterField {
  /** The query-param key this field maps to (bound to the endpoint's params). */
  key: string;
  /** Human label shown in the add-filter menu and on the chip. */
  label: string;
  kind: FilterKind;
  /** Options for a `select`; when empty the FilterBar falls back to text entry. */
  options?: FilterOption[];
  /** For `daterange`: the paired keys. */
  rangeKeys?: { from: string; to: string };
  /** Map a raw value to its display label on the active chip (defaults to value). */
  formatValue?: (value: string) => string;
}

/** Current filter values keyed by param name (strings, as they live in the URL). */
export type FilterValues = Record<string, string | undefined>;
