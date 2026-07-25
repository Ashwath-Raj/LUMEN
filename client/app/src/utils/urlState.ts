/**
 * URL-as-state serializers — arch §C ("URL is state") and §G (unit-tested).
 *
 * Every filter, viewport, time range, selected tab and selected entity
 * serializes to query params so that: (1) browser back works mid-drill;
 * (2) any view is shareable as a link; (3) refresh reproduces the view. No
 * filter state lives only in memory (§C rules).
 *
 * These are pure functions over `URLSearchParams` — framework-agnostic and
 * directly testable (arch §G testing scope). React Router hooks consume them;
 * the serialization logic lives here, once.
 */

/** Read a single param, or a fallback if absent. */
export function readParam(
  params: URLSearchParams,
  key: string,
  fallback = "",
): string {
  return params.get(key) ?? fallback;
}

/** Read a repeated param as a string list (e.g. `?head=a&head=b`). */
export function readList(params: URLSearchParams, key: string): string[] {
  return params.getAll(key).filter((v) => v.length > 0);
}

/** Read a numeric param, or a fallback. */
export function readNumber(
  params: URLSearchParams,
  key: string,
  fallback: number,
): number {
  const raw = params.get(key);
  if (raw === null || raw.trim() === "") return fallback;
  const n = Number(raw);
  return Number.isFinite(n) ? n : fallback;
}

/**
 * Merge a patch of values into existing params, returning a NEW
 * URLSearchParams (never mutates the input). An `undefined`/`null`/`""` value
 * removes the key; an array sets it as a repeated param. Deterministic key
 * order (sorted) so shared links are stable.
 */
export function writeParams(
  current: URLSearchParams,
  patch: Record<string, string | number | string[] | null | undefined>,
): URLSearchParams {
  const next = new URLSearchParams(current);
  for (const [key, value] of Object.entries(patch)) {
    next.delete(key);
    if (value === null || value === undefined || value === "") continue;
    if (Array.isArray(value)) {
      for (const item of value) if (item !== "") next.append(key, item);
    } else {
      next.set(key, String(value));
    }
  }
  next.sort();
  return next;
}

/** §29.2 list pagination params, read with sane defaults. */
export interface Pagination {
  limit: number;
  offset: number;
}

export function readPagination(
  params: URLSearchParams,
  defaults: Pagination = { limit: 50, offset: 0 },
): Pagination {
  return {
    limit: readNumber(params, "limit", defaults.limit),
    offset: readNumber(params, "offset", defaults.offset),
  };
}
