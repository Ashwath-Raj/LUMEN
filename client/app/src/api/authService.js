import { mockOperator } from '@/app/mocks/operator.js';

/**
 * Catalyst Authentication (LUMEN_MASTER_SPEC_V3 §20.2, §26.1 — "replaces
 * bespoke JWT entirely"). Login itself is not an API call this app makes —
 * Catalyst serves its own hosted login page at `/__catalyst/auth/login`
 * (configured via `client-package.json`'s `homepage`/`login_redirect`
 * fields), and the browser is redirected there directly. This module only
 * checks/reports session state via the Catalyst Web SDK
 * (`window.catalyst.auth`, loaded in `index.html`) and triggers sign-out.
 *
 * The Web SDK is only present when the app is served through Catalyst Web
 * Client Hosting — it does not exist under `npm run dev` locally. The
 * existing mock-fallback pattern (`VITE_USE_MOCKS`) covers that case so
 * local development is unaffected.
 */

const MOCK_SESSION_KEY = 'lumen_mock_session';
const shouldUseMocks = () => import.meta.env.VITE_USE_MOCKS !== 'false';
const HOSTED_LOGIN_PATH = '/__catalyst/auth/login';

function toOperator(catalystUser) {
  return {
    id: catalystUser.user_id ?? catalystUser.zuid,
    name: [catalystUser.first_name, catalystUser.last_name].filter(Boolean).join(' ') || catalystUser.email_id,
    email: catalystUser.email_id,
  };
}

/** Redirect the browser to Catalyst's hosted login page. There is no
 * request/response here — this is a full-page navigation, not an API call. */
export function redirectToLogin() {
  window.location.href = HOSTED_LOGIN_PATH;
}

export async function fetchCurrentOperator() {
  if (typeof window === 'undefined' || !window.catalyst?.auth) {
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
  if (typeof window !== 'undefined' && window.catalyst?.auth) {
    window.catalyst.auth.signOut(HOSTED_LOGIN_PATH);
    return;
  }
  redirectToLogin();
}
