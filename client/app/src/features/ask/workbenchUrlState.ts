/**
 * Investigation-memory ⇄ URL (Part 5; arch §C "URL is state"). The workbench's
 * persistent context — session id, selected case, selected persons, selected
 * district scope — serializes to query params so a shared/refreshed URL restores
 * the same investigation context. The CONVERSATION content itself is
 * session-local by design (spec: the console history rail is session-local; no
 * user-facing history store exists to persist to — nothing is invented).
 */
import { readParam, writeParams } from "@/utils/urlState";

export interface WorkbenchContext {
  /** Client-generated session id (keys the leads endpoint + exports). */
  session: string;
  /** Selected case id (arrives via ?case= from the workspace), or null. */
  caseId: string | null;
  /** Selected person ids (resolved identities from GET /persons). */
  persons: string[];
  /** Selected district census codes (from the authentic boundary set). */
  districts: string[];
}

function readList(params: URLSearchParams, key: string): string[] {
  const raw = readParam(params, key);
  return raw ? raw.split(",").filter(Boolean) : [];
}

export function readWorkbenchContext(params: URLSearchParams): WorkbenchContext {
  return {
    session: readParam(params, "session"),
    caseId: readParam(params, "case") || null,
    persons: readList(params, "persons"),
    districts: readList(params, "districts"),
  };
}

export function writeWorkbenchContext(
  current: URLSearchParams,
  patch: Partial<WorkbenchContext>,
): URLSearchParams {
  const flat: Record<string, string | null | undefined> = {};
  if (patch.session !== undefined) flat.session = patch.session || null;
  if (patch.caseId !== undefined) flat.case = patch.caseId ?? null;
  if (patch.persons !== undefined)
    flat.persons = patch.persons.length ? patch.persons.join(",") : null;
  if (patch.districts !== undefined)
    flat.districts = patch.districts.length ? patch.districts.join(",") : null;
  return writeParams(current, flat);
}

/** Toggle one id in a selection list. */
export function toggleId(list: string[], id: string): string[] {
  return list.includes(id) ? list.filter((x) => x !== id) : [...list, id];
}

/** A collision-safe client session id (no backend session registry exists). */
export function newSessionId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID().slice(0, 8)
    : Math.random().toString(36).slice(2, 10);
}
