/**
 * Lightweight grid-based marker clustering for incident points — no extra
 * dependency (keeps the geo chunk lean; leaflet.markercluster + its CSS avoided).
 * Incidents within the same zoom-scaled grid cell collapse into one cluster
 * bubble with a count; at high zoom the cell shrinks until points separate.
 *
 * Deterministic (grid snap, no randomness), so the same inputs always cluster
 * the same way. Returns either singletons (render as markers) or clusters
 * (render as sized bubbles). Empty input → empty output (graceful with no data).
 */
import type { GeoIncident } from "@/types/geo";

export interface IncidentCluster {
  id: string;
  center: [number, number];
  count: number;
  /** The member incidents (for a singleton, length 1). */
  members: GeoIncident[];
}

/** Grid cell size in degrees for a given zoom — smaller cells as you zoom in. */
function cellSizeForZoom(zoom: number): number {
  // ~0.5° at z6 down to ~0.01° at z14; clamps keep it sane at the extremes.
  const base = 40 / Math.pow(2, zoom);
  return Math.min(0.5, Math.max(0.008, base));
}

export function clusterIncidents(
  incidents: GeoIncident[],
  zoom: number,
): IncidentCluster[] {
  if (incidents.length === 0) return [];
  const size = cellSizeForZoom(zoom);
  const cells = new Map<string, GeoIncident[]>();

  for (const inc of incidents) {
    const [lat, lng] = inc.point;
    const key = `${Math.round(lat / size)}:${Math.round(lng / size)}`;
    const list = cells.get(key) ?? [];
    list.push(inc);
    cells.set(key, list);
  }

  const clusters: IncidentCluster[] = [];
  for (const [key, members] of cells) {
    const lat = members.reduce((s, m) => s + m.point[0], 0) / members.length;
    const lng = members.reduce((s, m) => s + m.point[1], 0) / members.length;
    clusters.push({ id: key, center: [lat, lng], count: members.length, members });
  }
  return clusters;
}
