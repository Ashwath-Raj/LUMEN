/**
 * The envelope API client — arch §E, §G ("the envelope client ... lives here,
 * once"). Master spec §29 envelope, §29.3 error codes.
 *
 * Responsibilities (all in this one module, never in components):
 *  - fetch a §29 endpoint and unwrap `data`;
 *  - raise a typed `ApiError` from an `error` body so the `ErrorState` primitive
 *    can map each §29.3 code to its rendering;
 *  - surface `meta` (especially `degradation_level`) so the shell's degradation
 *    banner/pill can react (arch §E: "renders the staleness banner automatically
 *    when meta.degradation_level ≠ L0").
 *
 * Built on `fetch` (no axios) against the `/api` base, which Vite proxies to
 * FastAPI in dev and which Web Client Hosting serves alongside AppSail in
 * production. Auth is the Catalyst session cookie (credentials: 'include');
 * there is no bespoke JWT (spec §26.1 row 17).
 */
import type {
  ApiErrorCode,
  Envelope,
  EnvelopeMeta,
  DegradationLevel,
} from "@/types/envelope";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

/** A typed error carrying the §29.3 code + trace_id for `ErrorState`. */
export class ApiError extends Error {
  readonly code: ApiErrorCode;
  readonly traceId: string;
  readonly retryable: boolean;
  readonly status: number;

  constructor(params: {
    code: ApiErrorCode;
    message: string;
    traceId: string;
    retryable: boolean;
    status: number;
  }) {
    super(params.message);
    this.name = "ApiError";
    this.code = params.code;
    this.traceId = params.traceId;
    this.retryable = params.retryable;
    this.status = params.status;
  }
}

/**
 * A single subscribable sink for the latest degradation level seen on any
 * envelope. The session provider subscribes; the shell pill reads from session.
 * Kept here so degradation handling lives in one place (arch §G).
 */
type DegradationListener = (level: DegradationLevel) => void;
const degradationListeners = new Set<DegradationListener>();

export function onDegradation(listener: DegradationListener): () => void {
  degradationListeners.add(listener);
  return () => degradationListeners.delete(listener);
}

function publishDegradation(meta: EnvelopeMeta | undefined): void {
  if (!meta) return;
  for (const listener of degradationListeners) listener(meta.degradation_level);
}

/**
 * Infer a §29.3 error code from an HTTP status when the response body is not a
 * §29 envelope (e.g. an endpoint that isn't implemented yet returns a bare
 * FastAPI 501). 501/502/503/504 are "the capability isn't available" → a
 * degraded state, not a failure.
 */
function codeForStatus(status: number): ApiErrorCode {
  switch (status) {
    case 400:
    case 422:
      return "VALIDATION_FAILED";
    case 403:
      return "SCOPE_DENIED";
    case 404:
      return "NOT_FOUND";
    case 429:
      return "RATE_LIMITED";
    case 501:
    case 502:
    case 503:
    case 504:
      return "DEPENDENCY_UNAVAILABLE";
    default:
      return "INTERNAL";
  }
}

function messageForStatus(status: number): string {
  if (status === 501) return "This capability is not available yet.";
  if (status === 502 || status === 503 || status === 504)
    return "The service is temporarily unavailable.";
  return `Request failed (${status})`;
}

function isRetryableStatus(status: number): boolean {
  return status === 502 || status === 503 || status === 504;
}

export interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  signal?: AbortSignal;
  /** Extra query params appended to the path. */
  query?: URLSearchParams;
}

/** The result of an envelope request: unwrapped data plus its meta. */
export interface ApiResult<T> {
  data: T;
  meta: EnvelopeMeta;
}

/**
 * Perform one §29 request. Resolves to `{ data, meta }` on success; throws
 * `ApiError` (typed by §29.3 code) on an error envelope or transport failure.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {},
): Promise<ApiResult<T>> {
  const { method = "GET", body, signal, query } = options;
  const qs = query && [...query.keys()].length ? `?${query.toString()}` : "";
  const url = `${API_BASE}${path}${qs}`;

  let response: Response;
  try {
    response = await fetch(url, {
      method,
      credentials: "include", // Catalyst session cookie (§26.1 row 17)
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (cause) {
    // Network/transport failure — treat as a dependency being unavailable.
    throw new ApiError({
      code: "DEPENDENCY_UNAVAILABLE",
      message: cause instanceof Error ? cause.message : "Network request failed",
      traceId: "",
      retryable: true,
      status: 0,
    });
  }

  let envelope: Envelope<T> | null = null;
  try {
    envelope = (await response.json()) as Envelope<T>;
  } catch {
    envelope = null;
  }

  // A well-formed envelope always drives behaviour — including its meta.
  if (envelope && typeof envelope === "object" && "meta" in envelope) {
    publishDegradation(envelope.meta);
  }

  if (!response.ok || !envelope || envelope.error) {
    const err = envelope?.error;
    throw new ApiError({
      // Prefer the envelope's §29.3 code; otherwise infer from the HTTP status
      // so a non-envelope failure (e.g. a FastAPI 501 `HTTPException`, or the
      // dev proxy's 502) degrades gracefully instead of reading as a hard
      // INTERNAL error. This is what lets an unimplemented endpoint render a
      // calm "not available yet" state rather than a red failure panel.
      code: (err?.code as ApiErrorCode) ?? codeForStatus(response.status),
      message: err?.message ?? messageForStatus(response.status),
      traceId: err?.trace_id ?? "",
      retryable: err?.retryable ?? isRetryableStatus(response.status),
      status: response.status,
    });
  }

  if (envelope.data === null) {
    throw new ApiError({
      code: "INTERNAL",
      message: "Envelope contained no data",
      traceId: envelope.meta?.trace_id ?? "",
      retryable: false,
      status: response.status,
    });
  }

  return { data: envelope.data, meta: envelope.meta };
}
