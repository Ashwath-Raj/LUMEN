import apiClient from './axiosClient.js';
import { withMockFallback } from '@/utils/apiFallback.js';
import {
  mockAnalysisEngine,
  mockGeneratedLeads,
  mockTemporalAlignment,
  mockActionableDirectives,
  mockEvidenceNexus,
  mockQueryHistory,
} from '@/mocks/intelligence.js';

/** Intelligence: AI Workbench query, generated leads, actionable directives. */

export async function fetchWorkbenchData() {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/intelligence/workbench');
    return data;
  }, {
    analysisEngine: mockAnalysisEngine,
    generatedLeads: mockGeneratedLeads,
    temporalAlignment: mockTemporalAlignment,
    actionableDirectives: mockActionableDirectives,
    evidenceNexus: mockEvidenceNexus,
    queryHistory: mockQueryHistory,
  });
}

export async function submitIntelligenceQuery(query) {
  return withMockFallback(async () => {
    const { data } = await apiClient.post('/intelligence/query', { query });
    return data;
  }, {
    id: `q-${Date.now()}`,
    query,
    timestamp: new Date().toISOString().substring(11, 19),
  });
}

export async function fetchGeneratedLeads(sessionId) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get(`/intelligence/leads/${sessionId}`);
    return data;
  }, mockGeneratedLeads);
}
