import apiClient from './axiosClient.js';
import { withMockFallback } from '@/app/utils/apiFallback.js';
import {
  mockCommandCenterSummary,
  mockCrimeTrend,
  mockRecentAlerts,
  mockHeatmapHotspots,
} from '@/app/mocks/dashboard.js';

/** Command Center: KPI strip, crime trend, heatmap, alerts, command actions. */

export async function fetchCommandCenterSummary() {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/dashboard/summary');
    return data;
  }, mockCommandCenterSummary);
}

export async function fetchCrimeTrend(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/dashboard/crime-trend', { params });
    return data;
  }, mockCrimeTrend);
}

export async function fetchRecentAlerts() {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/dashboard/alerts');
    return data;
  }, mockRecentAlerts);
}

export async function fetchHeatmapHotspots() {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/dashboard/heatmap');
    return data;
  }, mockHeatmapHotspots);
}

/** Composite fetch for the Command Center page — one loading/error state for the whole screen. */
export async function fetchCommandCenterData() {
  const [summary, crimeTrend, alerts, hotspots] = await Promise.all([
    fetchCommandCenterSummary(),
    fetchCrimeTrend(),
    fetchRecentAlerts(),
    fetchHeatmapHotspots(),
  ]);
  return { summary, crimeTrend, alerts, hotspots };
}
