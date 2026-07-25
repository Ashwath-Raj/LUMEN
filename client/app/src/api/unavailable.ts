/**
 * Helper for hooks whose backend endpoint does not exist in the OpenAPI yet.
 * Instead of requesting a non-existent path (a 404 that reads as a failure) or
 * disabling the query (which would leave a `QueryBoundary` on an infinite
 * skeleton), the hook's queryFn calls this to reject IMMEDIATELY with a
 * `DEPENDENCY_UNAVAILABLE` error — so the boundary renders the calm
 * "not available yet" DegradedState and no network call is made. When the
 * endpoint lands, the hook is repointed at it (one line) and this is removed.
 */
import { ApiError } from "./client";

export function rejectUnavailable(what: string): never {
  throw new ApiError({
    code: "DEPENDENCY_UNAVAILABLE",
    message: `${what} is not available yet.`,
    traceId: "",
    retryable: false,
    status: 501,
  });
}
