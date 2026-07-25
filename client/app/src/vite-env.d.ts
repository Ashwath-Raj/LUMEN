/// <reference types="vite/client" />

/**
 * Typed Vite env for the LUMEN frontend. Only `VITE_`-prefixed variables reach
 * the browser bundle (see vite.config.js); the root `.env` keeps everything
 * else backend-only.
 */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  /** Dev-only mock toggle (unset or ≠ 'false' → mocks on). See authService.ts. */
  readonly VITE_USE_MOCKS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
