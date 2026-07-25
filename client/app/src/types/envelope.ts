/**
 * The §29 response envelope + §29.3 error codes.
 *
 * Every backend response uses this envelope (master spec §29):
 *   { data, meta, error }
 * The API client (api/client.ts) unwraps `data`, surfaces `meta` (for the
 * degradation banner), and raises a typed `ApiError` from `error` so the
 * `ErrorState` primitive can map each §29.3 code to its rendering (arch §E).
 */

/** §24.2 degradation ladder levels, carried on every envelope's meta. */
export type DegradationLevel = "L0" | "L1" | "L2" | "L3" | "L4";

/** §29 envelope meta. */
export interface EnvelopeMeta {
  generated_at: string;
  method: string;
  model_version: string;
  contract_version: string;
  cached: boolean;
  degradation_level: DegradationLevel;
  trace_id: string;
  /** Set on a deprecated major version (§29.4). */
  deprecated?: boolean;
}

/** §29.3 error codes — each maps to an ErrorState rendering (arch §E). */
export type ApiErrorCode =
  | "VALIDATION_FAILED"
  | "NOT_FOUND"
  | "SCOPE_DENIED"
  | "RATE_LIMITED"
  | "DEPENDENCY_UNAVAILABLE"
  | "DEGRADED_RESULT"
  | "INTERNAL";

/** §29.3 error body. */
export interface EnvelopeError {
  code: ApiErrorCode;
  message: string;
  trace_id: string;
  retryable: boolean;
}

/** The §29 envelope, generic over its `data` payload. */
export interface Envelope<T> {
  data: T | null;
  meta: EnvelopeMeta;
  error: EnvelopeError | null;
}
