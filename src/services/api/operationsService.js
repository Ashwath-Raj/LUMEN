import apiClient from './axiosClient.js';
import { withMockFallback } from '@/utils/apiFallback.js';
import {
  mockIncidentQueue,
  mockResourceMetrics,
  mockCoordinationLog,
  mockTheatreHotspots,
  mockOperatorDossier,
  mockFirUploadLookup,
  mockOperationsSuspects,
} from '@/mocks/operations.js';

/** Operations: tactical deployment, operator dossier, FIR upload, suspect profiles. */

export async function fetchTacticalOverview() {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/operations/tactical-overview');
    return data;
  }, {
    incidentQueue: mockIncidentQueue,
    resourceMetrics: mockResourceMetrics,
    coordinationLog: mockCoordinationLog,
    hotspots: mockTheatreHotspots,
  });
}

export async function fetchOperatorDossier(operatorId) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get(`/operations/operators/${operatorId}`);
    return data;
  }, mockOperatorDossier);
}

export async function updateOperatorPreferences(operatorId, preferences) {
  return withMockFallback(async () => {
    const { data } = await apiClient.patch(`/operations/operators/${operatorId}/preferences`, preferences);
    return data;
  }, { ...mockOperatorDossier, preferences });
}

export async function submitFirUpload(formData) {
  return withMockFallback(async () => {
    const { data } = await apiClient.post('/operations/fir-upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  }, { success: true, ...mockFirUploadLookup });
}

export async function fetchSuspectPreviousRecords(suspectId) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get(`/operations/suspects/${suspectId}/records`);
    return data;
  }, mockFirUploadLookup.suspectPreviousRecords);
}

export async function fetchOperationsSuspects(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/operations/suspects', { params });
    return data;
  }, mockOperationsSuspects);
}
