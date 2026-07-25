/**
 * Catalyst Authentication (master spec §20.2, §26.1 row 17 — "replaces bespoke
 * JWT entirely"), with explicit environment detection. Salvaged from the
 * prototype's hard-won detection logic and ported to TypeScript.
 *
 * Two runtime environments exist and the difference is structural:
 *
 * 1. Catalyst runtime (deployed Web Client Hosting, or local `catalyst serve`):
 *    Catalyst serves the hosted login at `/__catalyst/auth/login` and the Web
 *    SDK bootstrap at `/__catalyst/sdk/init.js`, so `window.catalyst.auth`
 *    exists. Login is a full-page redirect; session checks go through
 *    `window.catalyst.auth.isUserAuthenticated()`.
 *
 * 2. Plain Vite (`npm run dev`): neither `/__catalyst/*` path exists — Vite
 *    proxies only `/api/*` — so the SDK never initialises. Redirecting to the
 *    hosted login there can only 404, so when mocks are enabled
 *    (VITE_USE_MOCKS unset or ≠ 'false', the dev default) login establishes a
 *    local mock session instead.
 *
 * Detection is build-mode-first: `import.meta.env.DEV` is true only under Vite,
 * and the Catalyst runtime always serves the production build — so DEV
 * deterministically means "not Catalyst". Capability sniffing alone is
 * insufficient: the CDN SDK global loads under Vite too but stays uninitialised
 * (init.js 404s), a husk that cannot authenticate.
 */
import type { Operator } from "@/types/session";

const MOCK_SESSION_KEY = "lumen_mock_session";
const HOSTED_LOGIN_PATH = "/__catalyst/auth/login";

/** Minimal shape of the Catalyst Web SDK we rely on. */
interface CatalystAuth {
  isUserAuthenticated: () => Promise<CatalystUser> | CatalystUser;
  signIn?: (redirectPath: string) => void;
}
interface CatalystGlobal {
  auth?: CatalystAuth;
}
interface CatalystUser {
  user_id?: string;
  zuid?: string;
  first_name?: string;
  last_name?: string;
  email_id?: string;
}

declare global {
  interface Window {
    catalyst?: CatalystGlobal;
  }
}

const shouldUseMocks = (): boolean => import.meta.env.VITE_USE_MOCKS !== "false";

const catalystAuthAvailable = (): boolean =>
  !import.meta.env.DEV &&
  typeof window !== "undefined" &&
  Boolean(window.catalyst?.auth);

const MOCK_OPERATOR: Operator = {
  id: "dev-operator",
  name: "Dev Operator",
  email: "dev@lumen.local",
};

function toOperator(user: CatalystUser): Operator {
  return {
    id: user.user_id ?? user.zuid ?? "",
    name:
      [user.first_name, user.last_name].filter(Boolean).join(" ") ||
      user.email_id ||
      "Operator",
    email: user.email_id ?? "",
  };
}

/**
 * Begin a login. Returns the operator when a session is established locally
 * (dev mock bypass), or `null` after initiating a full-page redirect to the
 * Catalyst hosted login (the page navigates away, so the return is unobserved).
 */
export async function login(): Promise<Operator | null> {
  if (catalystAuthAvailable()) {
    window.location.assign(HOSTED_LOGIN_PATH);
    return null;
  }
  if (shouldUseMocks()) {
    localStorage.setItem(MOCK_SESSION_KEY, "true");
    return MOCK_OPERATOR;
  }
  throw new Error(
    "Catalyst Authentication is unavailable and mocks are disabled. " +
      "Serve the production build via `catalyst serve` or a deployed host.",
  );
}

/** Resolve the current operator, or null if unauthenticated. */
export async function fetchCurrentOperator(): Promise<Operator | null> {
  if (catalystAuthAvailable()) {
    try {
      const user = await window.catalyst!.auth!.isUserAuthenticated();
      return user ? toOperator(user) : null;
    } catch {
      return null;
    }
  }
  if (shouldUseMocks() && localStorage.getItem(MOCK_SESSION_KEY) === "true") {
    return MOCK_OPERATOR;
  }
  return null;
}

/** End the local session (the Catalyst hosted logout is a deploy concern). */
export function logout(): void {
  localStorage.removeItem(MOCK_SESSION_KEY);
}
