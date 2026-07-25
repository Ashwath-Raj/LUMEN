/**
 * Geo Intelligence contract types (E.2, §30.3).
 *
 * ── GENERATION NOTE (arch §G) ────────────────────────────────────────────
 * Transcribed from the backend's authoritative sources — §29.1 (`/geo/districts`,
 * `/geo/hotspots`, `/geo/units/{id}`, `/geo/delay`), §30.3 (the four query
 * levels + five layers), §3.2 fact 5 (reporting delay), and the frozen
 * `PredictionContract` output vocabulary (§13: `district_risk`, `hotspots`,
 * `reporting_delay`). §7 leaves each prediction `output` an open dict, so — as in
 * Sessions 1/2 — these shapes are transcribed with this note and wired to the
 * canonical §29.1 paths; they connect unchanged when `/geo/*` lands and drift
 * then fails typecheck. Coordinates are [lat, lng] as Leaflet consumes them.
 * ─────────────────────────────────────────────────────────────────────────
 */
import type { RiskBand } from "@/design/tokens";

/** `GET /geo/districts` — one district's choropleth cell (§30.3 risk choropleth). */
export interface GeoDistrict {
  district_id: string;
  district_name: string;
  /** Derived risk band (§13 district_risk). §8 invariant 1 keeps the numeric
   *  score inside the district's risk Insight; §5.2 quality numerics come from
   *  `/quality/scores`. */
  risk_band: RiskBand;
  case_count: number;
}

/** A DBSCAN hotspot cluster (§13 hotspots · §30.3 density). */
export interface GeoHotspot {
  hotspot_id: string;
  /** Cluster centroid [lat, lng]. */
  center: [number, number];
  case_count: number;
  radius_m: number;
  risk_band: RiskBand;
  /** The dominant crime head in the cluster, if the backend supplies it. */
  crime_head: string | null;
}

/** A single incident point (§30.3 incident points layer). */
export interface GeoIncident {
  case_master_id: string;
  crime_no: string;
  point: [number, number];
  crime_head: string | null;
  risk_band: RiskBand | null;
}

/** `GET /geo/hotspots` payload — clusters + the incident points behind them. */
export interface GeoHotspotsResult {
  hotspots: GeoHotspot[];
  incidents: GeoIncident[];
}

/** A police-station catchment unit (§30.3 station catchment, §2.1 Station). */
export interface GeoUnit {
  unit_id: string;
  unit_name: string;
  district_id: string;
  /** Catchment centroid [lat, lng]. */
  center: [number, number];
  case_count: number;
  risk_band: RiskBand | null;
}

/** `GET /geo/units/{district_id}` — the district's stations (drill level 3). */
export interface GeoUnitsResult {
  district_id: string;
  units: GeoUnit[];
}

/** `GET /geo/delay` — reporting-delay layer (§3.2 fact 5; the unique layer). */
export interface GeoDelayUnit {
  unit_id: string;
  unit_name: string;
  district_id: string;
  center: [number, number];
  /** Median days between incident and registration for the unit. */
  median_delay_days: number;
  /** Whether the delay is anomalously high (§13 reporting_delay). */
  anomalous: boolean;
}

export interface GeoDelayResult {
  units: GeoDelayUnit[];
}

/** The four §30.3 drill levels. */
export type GeoLevel = "state" | "district" | "station" | "cluster";

/** The five §30.3 toggleable layers. */
export type GeoLayer =
  | "risk_choropleth"
  | "incident_points"
  | "density"
  | "station_catchment"
  | "reporting_delay";
