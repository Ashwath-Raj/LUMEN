/**
 * Wraps a real API call so that, in development only, an unreachable
 * FastAPI backend falls back to fixture data instead of leaving every
 * screen stuck in an error state. In production this never swallows an
 * error — real failures still surface to the UI's error handling.
 *
 * Usage inside a services/api/*Service.js function:
 *
 *   export async function fetchCommandCenterSummary() {
 *     return withMockFallback(
 *       async () => {
 *         const { data } = await apiClient.get('/dashboard/summary');
 *         return data;
 *       },
 *       mockCommandCenterSummary
 *     );
 *   }
 *
 * Set VITE_USE_MOCKS=false in .env to force real-network behavior even
 * in dev (useful once the backend is actually running locally).
 */
export async function withMockFallback(request, mockData) {
  const mocksDisabled = import.meta.env.VITE_USE_MOCKS === 'false';

  if (!import.meta.env.DEV || mocksDisabled) {
    return request();
  }

  try {
    return await request();
  } catch (err) {
    console.warn('[LUMEN] Backend unavailable, using mock data.', err?.message ?? err);
    return mockData;
  }
}
