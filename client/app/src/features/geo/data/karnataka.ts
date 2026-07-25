/**
 * Karnataka administrative reference — viewport constants + types for the
 * AUTHENTIC boundary GeoJSON served from `public/map-data/`.
 *
 * The geometry itself is NOT in this file anymore : the
 * hand-drawn rectangles are replaced by real Survey-of-India-derived district
 * boundaries (see `useKarnatakaBoundaries`). This module holds only the map
 * frame — centre, bounds, zoom limits — plus the feature property shape.
 *
 * These are public administrative boundaries (reference geometry), never crime
 * data; live intelligence still degrades gracefully when `/geo/*` is 501.
 */

/** Karnataka default viewport (state centroid) + zoom (arch E.2). */
export const KARNATAKA_CENTER: [number, number] = [15.05, 76.0];
export const KARNATAKA_ZOOM = 7;

/**
 * State bounds [[south, west], [north, east]] — used for `maxBounds` (so the map
 * cannot scroll off into an infinite world) and initial `fitBounds`. Padded
 * slightly beyond the true extent (11.6–18.5 N, 74.0–78.6 E) so edge districts
 * are not clipped against the viewport edge.
 */
export const KARNATAKA_BOUNDS: [[number, number], [number, number]] = [
  [11.0, 73.4],
  [19.2, 79.2],
];

/** Zoom limits (§F/GIS): min keeps Karnataka framed; max allows street detail. */
export const GEO_MIN_ZOOM = 6;
export const GEO_MAX_ZOOM = 16;

/** Properties on each authentic district feature (from the source GeoJSON). */
export interface DistrictFeatureProps {
  district_name: string;
  /** Census 2011 district code (string). */
  district_id: string;
  /** LGD (Local Government Directory) district code. */
  lgd: number;
}

/** Public-asset URLs for the authentic boundary GeoJSON (served from public/). */
export const KARNATAKA_STATE_URL = "/map-data/karnataka-state.geojson";
export const KARNATAKA_DISTRICTS_URL = "/map-data/karnataka-districts.geojson";
