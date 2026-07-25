/**
 * `Overview` contract — master spec §29.1 (`GET /overview`) + arch C.3/E.1.
 *
 * ── GENERATION NOTE (arch §G) ────────────────────────────────────────────
 * Like `contracts.ts`, these types are meant to be GENERATED from the backend's
 * Pydantic contract once `GET /overview` lands. As of this session the backend
 * exposes only legacy prototype stubs (`/dashboard/*` → HTTP 501); the canonical
 * §29.1 `/overview` endpoint is deferred to a later backend session. §7 gives no
 * field-level Pydantic model for the overview payload, so the shape below is a
 * faithful transcription of what §29.1 ("counts, trend, risk bands, anomalies,
 * top network figures, quality score") and the surfaces that read it (C.3
 * Briefing, E.1 Command) require — nothing is invented beyond those two sources.
 * When the endpoint is generated this file is replaced; a drift then fails the
 * typecheck, which is the architectural point (arch §G).
 * ─────────────────────────────────────────────────────────────────────────
 */
import type { RiskBand } from "@/design/tokens";

/** One district's headline risk standing (§29.1 "risk bands"). */
export interface DistrictRisk {
  district_id: string;
  district_name: string;
  /** Band only — §8 invariant 1 keeps the numeric score inside the Insight. */
  band: RiskBand;
  case_count: number;
}

/** One point in a 12-month per-crime-head trend series (E.1 sparklines). */
export interface TrendPoint {
  /** ISO month, e.g. "2026-03". */
  month: string;
  count: number;
}

/** A top-5 crime-head trend series (E.1 bottom sparklines). */
export interface CrimeHeadTrend {
  crime_head: string;
  points: TrendPoint[];
}

/** A network-central person figure (§29.1 "top network figures"). */
export interface NetworkFigure {
  person_id: string;
  label: string;
  centrality: number;
}

/**
 * The four Briefing / Command counters (C.3, E.1) — each is a navigable Stat.
 * Kept as named fields (not a generic map) so the UI cannot silently drop one.
 */
export interface OverviewCounts {
  period_cases: number;
  active_anomalies: number;
  high_band_districts: number;
  network_central_persons: number;
  priority_cases: number;
  recommendations_awaiting_review: number;
}

/** `GET /overview` payload (envelope `data`). */
export interface Overview {
  counts: OverviewCounts;
  district_risk: DistrictRisk[];
  trends: CrimeHeadTrend[];
  network_figures: NetworkFigure[];
}
