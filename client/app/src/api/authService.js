import { mockOperator } from '@/app/mocks/operator.js';

/**
 * Catalyst Authentication (LUMEN_MASTER_SPEC_V3 §20.2, §26.1 — "replaces
 * bespoke JWT entirely"), with explicit environment detection.
 *
 * Two runtime environments exist and the difference is structural, not
 * cosmetic:
 *
 * 1. **Catalyst runtime** (deployed Web Client Hosting, or local
 *    `catalyst serve`): Catalyst's infrastructure serves the hosted login
 *    page at `/__catalyst/auth/login` and the Web SDK bootstrap at
 *    `/__catalyst/sdk/init.js`, so `window.catalyst.auth` exists. Login is
 *    a full-page redirect to the hosted page; session checks go through
 *    `window.catalyst.auth.isUserAuthenticated()`.
 *
 * 2. **Plain Vite** (`npm run dev`): neither `/__catalyst/*` path exists —
 *    Vite only proxies `/api/*` (see vite.config.js) — so the SDK never
 *    loads and `window.catalyst` is undefined. Redirecting to the hosted
 *    login here can only ever 404. In this environment, when mocks are
 *    enabled (`VITE_USE_MOCKS` unset or not 'false', the dev default),
 *    login instead establishes the local mock session — the same
 *    mock-first dev pattern every other service in this app already uses
 *    via `withMockFallback`.
 *
 * Environment detection is build-mode-first, capability-second:
 * `import.meta.env.DEV` is true only under the Vite dev server, and the
 * Catalyst runtime always serves the production build (`client/dist`, per
 * catalyst.json) — so DEV deterministically means "not Catalyst".
 * Capability sniffing (`window.catalyst?.auth`) alone is NOT sufficient:
 * the CDN-hosted catalystWebSDK.js loads even under Vite and defines the
 * global, but `/__catalyst/sdk/init.js` (which calls `catalyst.initApp`
 * with the project config) 404s there — leaving an SDK object that exists
 * but is uninitialized and cannot authenticate. Treating that husk as
 * "Catalyst available" is exactly what sent dev users to a 404.
 */

const MOCK_SESSION_KEY = 'lumen_mock_session';
const HOSTED_LOGIN_PATH = '/__catalyst/auth/login';

const shouldUseMocks = () => import.meta.env.VITE_USE_MOCKS !== 'false';
const catalystAuthAvailable = () =>
  !import.meta.env.DEV &&
  typeof window !== 'undefined' &&
  Boolean(window.catalyst?.auth);

function toOperator(catalystUser) {
  return {
    id: catalystUser.user_id ?? catalystUser.zuid,
    name: [catalystUser.first_name, catalystUser.last_name].filter(Boolean).join(' ') || catalystUser.email_id,
    email: catalystUser.email_id,
  };
}

/**
 * Begin a login. Returns the operator when the session could be
 * established locally (dev mock bypass), or `null` after initiating a
 * full-page redirect to Catalyst's hosted login (real flow — the page
 * navigates away, so the return value is never observed).
 */
export async function loginRequest() {
  if (catalystAuthAvailable()) {
    window.location.href = HOSTED_LOGIN_PATH;
    return null;
  }
  if (shouldUseMocks()) {
    console.warn('[LUMEN] Catalyst SDK not present (npm run dev) — using mock session.');
    localStorage.setItem(MOCK_SESSION_KEY, 'true');
    return mockOperator;
  }
  throw new Error(
    'Catalyst Authentication is unavailable: the Web SDK did not load and mocks are disabled. ' +
      'Run through `catalyst serve` (or deployed hosting) for the real login flow, ' +
      'or unset VITE_USE_MOCKS for the dev mock session.'
  );
}

export async function fetchCurrentOperator() {
  if (!catalystAuthAvailable()) {
    if (shouldUseMocks() && localStorage.getItem(MOCK_SESSION_KEY) === 'true') {
      return mockOperator;
    }
    return null;
  }

  try {
    const result = await window.catalyst.auth.isUserAuthenticated();
    return toOperator(result.content);
  } catch (err) {
    return null;
  }
}

export async function logoutRequest() {
  localStorage.removeItem(MOCK_SESSION_KEY);
  if (catalystAuthAvailable()) {
    // Real flow: Catalyst clears the session and navigates to its login page.
    window.catalyst.auth.signOut(HOSTED_LOGIN_PATH);
    return;
  }
  // Dev flow: clearing the mock session is the whole logout. ProtectedRoute
  // bounces to the app's own /login route — never to /__catalyst/*, which
  // does not exist under Vite.
}
