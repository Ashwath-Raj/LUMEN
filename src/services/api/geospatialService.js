import apiClient from './axiosClient.js';
import { withMockFallback } from '@/utils/apiFallback.js';
import { mockHotspots, mockSectorIntel, mockGeoParameters } from '@/mocks/geospatial.js';

/** Geospatial: hotspots, heatmap layers, sector intel, filter parameters. */

export async function fetchPriorityHotspots(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/geospatial/hotspots', { params });
    return data;
  }, mockHotspots);
}

export async function fetchSectorIntel(sectorId) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get(`/geospatial/sector-intel/${sectorId}`);
    return data;
  }, mockSectorIntel);
}

export async function fetchGeoParameters() {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/geospatial/parameters');
    return data;
  }, mockGeoParameters);
}

export async function applyGeoParameters(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.post('/geospatial/parameters', params);
    return data;
  }, { ...params, applied: true });
}

/** Composite fetch for the Geospatial page — one loading/error state for the whole screen. */
export async function fetchGeospatialData() {
  const [hotspots, sectorIntel, parameters] = await Promise.all([
    fetchPriorityHotspots(),
    fetchSectorIntel('default'),
    fetchGeoParameters(),
  ]);
  return { hotspots, sectorIntel, parameters };
}
