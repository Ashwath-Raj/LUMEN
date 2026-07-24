import apiClient from './axiosClient.js';
import { withMockFallback } from '@/app/utils/apiFallback.js';
import {
  mockCases,
  mockCaseDetails,
  mockSuspectProfiles,
  mockWatchlist,
  mockEvidenceLocker,
  mockFirIntelligence,
  mockInterviewTranscripts,
  mockDeviceForensics,
  mockInvestigationReports,
} from '@/app/mocks/investigation.js';

/** Investigation: cases, suspects, evidence, timeline, network, FIR intelligence, forensics. */

export async function fetchCases(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/investigation/cases', { params });
    return data;
  }, mockCases);
}

export async function fetchCaseById(caseId) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get(`/investigation/cases/${caseId}`);
    return data;
  }, mockCaseDetails[caseId] ?? Object.values(mockCaseDetails)[0]);
}

export async function fetchSuspectProfiles(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/investigation/suspects', { params });
    return data;
  }, mockSuspectProfiles);
}

export async function fetchWatchlist(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/investigation/watchlist', { params });
    return data;
  }, mockWatchlist);
}

export async function fetchEvidenceLocker(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/investigation/evidence-locker', { params });
    return data;
  }, mockEvidenceLocker);
}

export async function fetchFirIntelligence(firId) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get(`/investigation/fir-intelligence/${firId ?? 'latest'}`);
    return data;
  }, mockFirIntelligence);
}

export async function submitFirDocument(formData) {
  return withMockFallback(async () => {
    const { data } = await apiClient.post('/investigation/fir-intelligence', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  }, mockFirIntelligence);
}

export async function fetchInterviewTranscript(interviewId) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get(`/investigation/interviews/${interviewId}`);
    return data;
  }, mockInterviewTranscripts[interviewId] ?? Object.values(mockInterviewTranscripts)[0]);
}

export async function fetchDeviceForensics(deviceId) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get(`/investigation/forensics/${deviceId}`);
    return data;
  }, mockDeviceForensics[deviceId] ?? Object.values(mockDeviceForensics)[0]);
}

export async function fetchInvestigationArchive(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/investigation/archive', { params });
    return data;
  }, mockCases.filter((c) => c.status === 'CLOSED'));
}

export async function fetchCaseReports(caseId) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get(`/investigation/cases/${caseId}/reports`);
    return data;
  }, mockInvestigationReports[caseId] ?? []);
}
