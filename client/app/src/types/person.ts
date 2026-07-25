/**
 * Person (identity) contract types (§6.4, E.5) — transcribed from the REAL,
 * DB-backed `/persons/{id}` router (`api/lumen/api/routers/persons.py`), which
 * returns live data from `lumen_person` / `lumen_person_link`.
 *
 * §6.4 presentation rules the shape carries: resolution confidence is ALWAYS
 * present (P10); auto-linked members carry their `match_features` "see why";
 * candidates (0.65–0.85) are returned SEPARATELY, never mixed into `linked`.
 * Language is "person associated with N case records" — never "criminal".
 */

/** One resolution link — an accused record matched to this person (§6.4). */
export interface PersonLink {
  accused_master_id: number;
  confidence: number;
  /** The "see why" match features. */
  match_features: Record<string, unknown> | null;
  state: string;
}

/** `GET /persons/{id}` — dossier with resolution evidence (§29.1, §6.4). */
export interface PersonDetail {
  person_id: string;
  canonical_name: string;
  /** §6.4 language: "person associated with N case records". */
  description: string;
  case_count: number;
  district_count: number;
  /** Always shown (P10). */
  resolution_confidence: number;
  method_version: string;
  first_seen: string | null;
  last_seen: string | null;
  /** Auto-linked members with their match features. */
  linked: PersonLink[];
  /** Candidate matches (0.65–0.85), visually separated, excluded from metrics. */
  candidates: PersonLink[];
}

/** `GET /persons` list row. */
export interface PersonListItem {
  person_id: string;
  canonical_name: string;
  description: string;
  case_count: number;
  district_count: number;
  resolution_confidence: number;
  method_version: string;
}

export interface PersonList {
  total: number;
  persons: PersonListItem[];
}
