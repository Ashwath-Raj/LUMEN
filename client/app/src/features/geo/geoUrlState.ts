/**
 * Geo view state ⇄ URL (arch §C "URL is state": viewport, layers, time range and
 * selection serialize; §30.3 "Viewport and layers serialize to the URL"). Pure
 * functions over URLSearchParams built on the shared `urlState` helpers, so the
 * Geo page never hand-parses params and a shared link reproduces the exact map
 * view (centre, zoom, active layers, drill level, district, time range).
 */
import type { GeoLayer, GeoLevel } from "@/types/geo";
import {
  KARNATAKA_CENTER,
  KARNATAKA_ZOOM,
} from "./data/karnataka";

import { readNumber, readParam, writeParams } from "@/utils/urlState";

const ALL_LAYERS: readonly GeoLayer[] = [
  "risk_choropleth",
  "incident_points",
  "density",
  "station_catchment",
  "reporting_delay",
];
const LEVELS: readonly GeoLevel[] = ["state", "district", "station", "cluster"];

/** Default layers on first load — the risk choropleth (arch E.1/E.2). */
const DEFAULT_LAYERS: GeoLayer[] = ["risk_choropleth"];

export interface GeoViewState {
  center: [number, number];
  zoom: number;
  level: GeoLevel;
  layers: GeoLayer[];
  district: string | null;
  date_from: string | null;
  date_to: string | null;
  /** True when the URL already carried a viewport (shared link) — so the map
   *  should NOT auto-fit Karnataka over the user's chosen view. */
  hasExplicitViewport: boolean;
}

export function readGeoState(params: URLSearchParams): GeoViewState {
  const hasExplicitViewport =
    params.has("lat") || params.has("lng") || params.has("z");
  const lat = readNumber(params, "lat", KARNATAKA_CENTER[0]);
  const lng = readNumber(params, "lng", KARNATAKA_CENTER[1]);
  const zoom = readNumber(params, "z", KARNATAKA_ZOOM);

  const levelRaw = readParam(params, "level") as GeoLevel;
  const level = LEVELS.includes(levelRaw) ? levelRaw : "state";

  const layersRaw = readParam(params, "layers");
  const layers = layersRaw
    ? (layersRaw.split(",").filter((l) => ALL_LAYERS.includes(l as GeoLayer)) as GeoLayer[])
    : DEFAULT_LAYERS;

  const district = readParam(params, "district") || null;
  const date_from = readParam(params, "date_from") || null;
  const date_to = readParam(params, "date_to") || null;

  return {
    center: [lat, lng],
    zoom,
    level,
    layers: layers.length ? layers : DEFAULT_LAYERS,
    district,
    date_from,
    date_to,
    hasExplicitViewport,
  };
}

export function writeGeoState(
  current: URLSearchParams,
  patch: Partial<GeoViewState>,
): URLSearchParams {
  const flat: Record<string, string | number | null | undefined> = {};
  if (patch.center) {
    flat.lat = patch.center[0].toFixed(4);
    flat.lng = patch.center[1].toFixed(4);
  }
  if (patch.zoom !== undefined) flat.z = patch.zoom;
  if (patch.level !== undefined) flat.level = patch.level === "state" ? null : patch.level;
  if (patch.layers !== undefined) {
    flat.layers = patch.layers.length ? patch.layers.join(",") : null;
  }
  if ("district" in patch) flat.district = patch.district ?? null;
  if ("date_from" in patch) flat.date_from = patch.date_from ?? null;
  if ("date_to" in patch) flat.date_to = patch.date_to ?? null;
  return writeParams(current, flat);
}

/** Toggle a single layer in the active set. */
export function toggleLayer(layers: GeoLayer[], layer: GeoLayer): GeoLayer[] {
  return layers.includes(layer)
    ? layers.filter((l) => l !== layer)
    : [...layers, layer];
}
