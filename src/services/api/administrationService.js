import apiClient from './axiosClient.js';
import { withMockFallback } from '@/utils/apiFallback.js';
import { mockSecurityPosture, mockPersonnelRoster, mockForensicAuditLog } from '@/mocks/administration.js';

/** Administration: governance & security, personnel roster, audit log. */

export async function fetchSecurityPosture() {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/administration/security-posture');
    return data;
  }, mockSecurityPosture);
}

export async function fetchPersonnelRoster(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/administration/personnel', { params });
    return data;
  }, mockPersonnelRoster);
}

export async function fetchAuditLog(params) {
  return withMockFallback(async () => {
    const { data } = await apiClient.get('/administration/audit-log', { params });
    return data;
  }, mockForensicAuditLog);
}

/** Composite fetch for the Governance & Security landing page. */
export async function fetchGovernanceOverview() {
  const [posture, personnel, auditLog] = await Promise.all([
    fetchSecurityPosture(),
    fetchPersonnelRoster(),
    fetchAuditLog(),
  ]);
  return { posture, personnel, auditLog };
}
