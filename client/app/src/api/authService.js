import apiClient from './axiosClient.js';
import { mockOperator } from '@/app/mocks/operator.js';

/**
 * Maps to FastAPI auth endpoints.
 *
 * When VITE_USE_MOCKS=false (backend is running), all three functions call
 * the real API. When the backend is unavailable and VITE_USE_MOCKS is true,
 * the mock session fallback activates automatically.
 */

const MOCK_SESSION_KEY = 'lumen_mock_session';
const shouldUseMocks = () => import.meta.env.VITE_USE_MOCKS !== 'false';

export async function loginRequest({ clearanceId, passphrase }) {
  try {
    const { data } = await apiClient.post('/auth/login', {
      clearance_id: clearanceId,
      passphrase,
    });
    if (data.token) localStorage.setItem('lumen_token', data.token);
    return data.operator;
  } catch (err) {
    if (!shouldUseMocks()) throw err;
    // Mock fallback — only used when backend is unavailable
    console.warn('[LUMEN] Backend unavailable — activating mock session.');
    if (!clearanceId || !passphrase) {
      throw new Error('Clearance ID and passphrase are required.');
    }
    localStorage.setItem(MOCK_SESSION_KEY, 'true');
    return mockOperator;
  }
}

export async function logoutRequest() {
  try {
    await apiClient.post('/auth/logout');
  } catch (err) {
    if (!shouldUseMocks()) throw err;
  } finally {
    localStorage.removeItem('lumen_token');
    localStorage.removeItem(MOCK_SESSION_KEY);
  }
}

export async function fetchCurrentOperator() {
  try {
    const { data } = await apiClient.get('/auth/me');
    return data;
  } catch (err) {
    // 401 = genuinely unauthenticated — let AuthProvider set operator to null
    if (err?.response?.status === 401) return null;
    // Non-auth error + mocks enabled = offline mock session
    if (shouldUseMocks() && localStorage.getItem(MOCK_SESSION_KEY) === 'true') {
      return mockOperator;
    }
    throw err;
  }
}
