import apiClient from './axiosClient.js';
import { withMockFallback } from '@/utils/apiFallback.js';
import {
  mockCrimeStatistics,
  mockCaseFiles,
  mockEvidenceVaultItems,
  mockFieldReports,
  mockSignalIntercepts,
  mockAnalyticsPersonnel,
  mockArchivedCases,
} from '@/mocks/analytics.js';

/** Analytics: pattern analysis, case files, evidence vault, field reports, signal intel, personnel, archive. */

export async function fetchCrimeStatistics(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/analytics/statistics', { params });
    return data;
  }, mockCrimeStatistics);
}

export async function fetchCaseFiles(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/analytics/case-files', { params });
    return data;
  }, mockCaseFiles);
}

export async function fetchEvidenceVault(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/analytics/evidence-vault', { params });
    return data;
  }, mockEvidenceVaultItems);
}

export async function fetchFieldReports(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/analytics/field-reports', { params });
    return data;
  }, mockFieldReports);
}

export async function fetchSignalIntercepts(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/analytics/signal-intelligence', { params });
    return data;
  }, mockSignalIntercepts);
}

export async function fetchPersonnel(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/analytics/personnel', { params });
    return data;
  }, mockAnalyticsPersonnel);
}

export async function fetchArchived(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/analytics/archived', { params });
    return data;
  }, mockArchivedCases);
}
