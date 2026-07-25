/**
 * Geo Intelligence hooks (E.2) — reconciled against the backend OpenAPI.
 *
 * Only `/geospatial/hotspots` exists as a live geo endpoint (currently 501). The
 * spec's `/geo/districts`, `/geo/delay`, `/geo/units/{id}` are NOT in the
 * OpenAPI, so their hooks do not request a non-existent path — they return a
 * disabled query flagged unavailable, and the map falls back to the static
 * district boundaries + degraded banner. District choropleth VALUES will wire up
 * when the backend adds a districts endpoint; boundaries never depended on it.
 *
 * One endpoint → one hook → one query key (arch §G); centralized paths from
 * `ENDPOINTS`. No bypassing Query, no invented routes.
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { rejectUnavailable } from "@/api/unavailable";
import { queryKeys } from "@/api/queryKeys";
import type {
  GeoDelayResult,
  GeoDistrict,
  GeoHotspotsResult,
  GeoUnitsResult,
} from "@/types/geo";

/** Shared geo filter params (district scope + time range + optional bbox). */
export interface GeoQueryParams {
  district?: string;
  date_from?: string;
  date_to?: string;
  /** Bounding box "south,west,north,east" for viewport-scoped queries. */
  bbox?: string;
}

function toQuery(params: GeoQueryParams): URLSearchParams {
  const q = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    q.set(key, String(value));
  }
  return q;
}

/**
 * District choropleth values. No backend endpoint exists (`ENDPOINTS.geoDistricts`
 * is null), so this never fires a request — it resolves to an empty, disabled
 * query. District BOUNDARIES come from the static asset (`useKarnatakaBoundaries`),
 * not this hook.
 */
export function useGeoDistricts() {
  return useQuery({
    queryKey: queryKeys.geoDistricts(),
    retry: false,
    queryFn: async ({ signal }) => {
      if (ENDPOINTS.geoDistricts === null) rejectUnavailable("District choropleth");
      const { data } = await apiFetch<GeoDistrict[]>(ENDPOINTS.geoDistricts, {
        signal,
      });
      return data;
    },
  });
}

/** A district's stations. No backend endpoint exists → disabled query. */
export function useGeoUnits(districtId: string | null) {
  return useQuery({
    queryKey: queryKeys.geoUnits(districtId ?? ""),
    enabled: !!districtId,
    retry: false,
    queryFn: async ({ signal }) => {
      if (ENDPOINTS.geoUnits === null) rejectUnavailable("Station catchment");
      const { data } = await apiFetch<GeoUnitsResult>(ENDPOINTS.geoUnits, {
        signal,
      });
      return data;
    },
  });
}

/** `GET /geospatial/hotspots` — the real hotspots endpoint (currently 501). */
export function useGeoHotspots(params: GeoQueryParams, enabled = true) {
  return useQuery({
    queryKey: queryKeys.geoHotspots(params as Record<string, unknown>),
    enabled: enabled && ENDPOINTS.geoHotspots !== null,
    queryFn: async ({ signal }) => {
      const { data } = await apiFetch<GeoHotspotsResult>(ENDPOINTS.geoHotspots, {
        signal,
        query: toQuery(params),
      });
      return data;
    },
  });
}

/** Reporting-delay layer. No backend endpoint exists → disabled query. */
export function useGeoDelay(params: GeoQueryParams, enabled = true) {
  return useQuery({
    queryKey: queryKeys.geoDelay(params as Record<string, unknown>),
    enabled,
    retry: false,
    queryFn: async ({ signal }) => {
      if (ENDPOINTS.geoDelay === null) rejectUnavailable("Reporting delay");
      const { data } = await apiFetch<GeoDelayResult>(ENDPOINTS.geoDelay, {
        signal,
        query: toQuery(params),
      });
      return data;
    },
  });
}
