/**
 * Basemap configuration for the MapCanvas (user brief "Multiple basemaps").
 * Three tile layers: a dark intelligence map (default, matches the app's dark
 * palette — CARTO dark-matter), standard OpenStreetMap, and Esri satellite.
 *
 * All are public tile services requiring no key. Attribution is set per §
 * governance/etiquette (tile providers require attribution). The dark basemap is
 * the command-center default (minimal labels, high contrast).
 */
export type BasemapId = "dark" | "standard" | "satellite";

export interface Basemap {
  id: BasemapId;
  label: string;
  url: string;
  attribution: string;
  /** Max zoom the provider supports. */
  maxZoom: number;
}

export const BASEMAPS: Record<BasemapId, Basemap> = {
  dark: {
    id: "dark",
    label: "Intelligence",
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    maxZoom: 20,
  },
  standard: {
    id: "standard",
    label: "Standard",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  },
  satellite: {
    id: "satellite",
    label: "Satellite",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution:
      "Tiles &copy; Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
    maxZoom: 19,
  },
};

export const DEFAULT_BASEMAP: BasemapId = "dark";
