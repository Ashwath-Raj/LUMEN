/**
 * Case Registry filter params + lookup option types (E.3).
 *
 * ── GENERATION NOTE (arch §G) ────────────────────────────────────────────
 * The filter keys are EXACTLY the §29.1 `GET /cases` params ("head, sub-head,
 * gravity, status, category, district, unit, date range, q full-text"), plus the
 * §29.2 `limit`/`offset` pagination and `sort`. Risk band and investigation
 * stage are filterable in the arch's E.3 FilterBar spec; they map to the derived
 * insight band (§9) and the ProcessEvent stage (§2.1) respectively. No param the
 * endpoint does not accept is invented — the FilterBar's add-filter menu is
 * "bound to the endpoint's params" (arch D11).
 *
 * Lookup options (crime heads, districts, stations…) populate the filter
 * selects. §29.1 has no dedicated lookups endpoint named, so `useLookups` reads
 * whatever `GET /cases` exposes as its facet metadata when the backend lands;
 * until then the selects fall back to free-text entry (see the FilterBar).
 * ─────────────────────────────────────────────────────────────────────────
 */
import type { RiskBand } from "@/design/tokens";
import type { TimelineEventKind } from "./timeline";

/** Multi-column sort (E.3 "multi-column sorting"). `-` prefix = descending. */
export type SortDirection = "asc" | "desc";

export interface SortSpec {
  field: string;
  direction: SortDirection;
}

/** §29.1 `GET /cases` filter params + §29.2 pagination + multi-sort. */
export interface CaseFilters {
  /** Full-text search (§29.1 `q`). */
  q?: string;
  crime_head?: string;
  crime_sub_head?: string;
  gravity?: string;
  status?: string;
  category?: string;
  district?: string;
  station?: string;
  /** E.3 filterable: derived risk band (§9). */
  risk_band?: RiskBand;
  /** E.3 filterable: investigation stage (§2.1 ProcessEvent kind). */
  stage?: TimelineEventKind;
  date_from?: string;
  date_to?: string;
  /** §29.2 pagination. */
  limit?: number;
  offset?: number;
  /** Multi-column sort, serialized to the URL as `sort=field:dir,field:dir`. */
  sort?: SortSpec[];
}

/** One selectable option for a lookup-backed filter. */
export interface LookupOption {
  id: string;
  label: string;
}

/** Facet lookups for the FilterBar selects (populated when the backend lands). */
export interface CaseLookups {
  crime_heads: LookupOption[];
  crime_sub_heads: LookupOption[];
  gravities: LookupOption[];
  statuses: LookupOption[];
  categories: LookupOption[];
  districts: LookupOption[];
  stations: LookupOption[];
}
