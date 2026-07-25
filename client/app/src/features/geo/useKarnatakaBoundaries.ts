/**
 * Loads the AUTHENTIC Karnataka boundary GeoJSON (state + 30 districts) from the
 * app's static assets (`public/map-data/`). These are reference geometry bundled
 * with the deploy — NOT the §29 API — so they load regardless of the `/geo/*`
 * intelligence endpoints' 501 state, guaranteeing boundaries are always drawable
 * (the Session-3 requirement: "show district boundaries" even when degraded).
 *
 * Cached forever (staleTime/gcTime Infinity) — administrative boundaries do not
 * change during a session. Fetched with plain `fetch` (static files, not the
 * envelope client) via TanStack Query so the map still gets one shared, retried,
 * de-duplicated load.
 */
import { useQuery } from "@tanstack/react-query";
import type { FeatureCollection, MultiPolygon, Polygon } from "geojson";

import { queryKeys } from "@/api/queryKeys";
import {
  KARNATAKA_DISTRICTS_URL,
  KARNATAKA_STATE_URL,
  type DistrictFeatureProps,
} from "./data/karnataka";

export type DistrictCollection = FeatureCollection<
  Polygon | MultiPolygon,
  DistrictFeatureProps
>;
export type StateCollection = FeatureCollection<
  Polygon | MultiPolygon,
  { name: string }
>;

export interface KarnatakaBoundaries {
  state: StateCollection;
  districts: DistrictCollection;
}

async function fetchJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`Failed to load boundary asset: ${url} (${res.status})`);
  return (await res.json()) as T;
}

export function useKarnatakaBoundaries() {
  return useQuery({
    queryKey: queryKeys.geoBoundaries(),
    staleTime: Infinity,
    gcTime: Infinity,
    queryFn: async ({ signal }): Promise<KarnatakaBoundaries> => {
      const [state, districts] = await Promise.all([
        fetchJson<StateCollection>(KARNATAKA_STATE_URL, signal),
        fetchJson<DistrictCollection>(KARNATAKA_DISTRICTS_URL, signal),
      ]);
      return { state, districts };
    },
  });
}
