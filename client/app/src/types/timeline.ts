/**
 * Case timeline + activity types (Case Workspace E.4 Timeline + Activity tabs).
 *
 * ── GENERATION NOTE (arch §G) ────────────────────────────────────────────
 * TIMELINE is derived from the FROZEN `ProcessEvent` semantic entity
 * (`entities.py`, §2.1) — the five lifecycle event kinds (incident, info
 * received, registered, arrest, chargesheet) with their §2.3 render form. The
 * `GET /cases/{id}/timeline` endpoint (§29.1) returns "derived lifecycle with
 * gaps and district benchmarks"; the district-median reference is a spec field
 * of the timeline surface (§30.4), transcribed here.
 *
 * ACTIVITY is the §21 `lumen_audit` access log ("who read which case, who ran
 * which AI query, … who was denied") — read-only (§21). It is NOT the domain
 * event bus; those are `EventContract` (§19.1, frozen). The audit shape (actor,
 * action, target, when, reason) is §21 verbatim; `GET /audit` scopes to the
 * case. Both are transcribed for generation once field-level contracts land.
 * ─────────────────────────────────────────────────────────────────────────
 */

/** §2.1 ProcessEvent kinds — the five lifecycle stages (§30.4 order). */
export type TimelineEventKind =
  | "incident"
  | "info_received"
  | "registered"
  | "arrest"
  | "chargesheet";

/** One §2.1 ProcessEvent on the case timeline (§30.4). */
export interface TimelineEvent {
  event_id: string;
  kind: TimelineEventKind;
  occurred_at: string | null;
  /** §2.3 render form, e.g. "Arrest · 12 Mar 2026 · Whitefield PS · IO PSI Ramesh". */
  label: string;
  station_name: string | null;
  io_display_name: string | null;
  /** Chargesheet type 'A'/'B'/'C' (§3.2 fact 6) when kind = chargesheet. */
  chargesheet_type: string | null;
  /** Any entity references this event links to (§8 Evidence-style). */
  entity_url: string | null;
}

/** `GET /cases/{id}/timeline` payload (§29.1, §30.4). */
export interface CaseTimeline {
  events: TimelineEvent[];
  /** Gap-to-scale reference: district median days between stages (§30.4). */
  district_median_days: number | null;
}

/** §21 audit access-log entry — read-only ("no editing", Activity tab). */
export interface ActivityEntry {
  audit_id: string;
  /** ISO timestamp — the "when". */
  occurred_at: string;
  /** The actor: a user id/name or "system". */
  actor: string;
  /** The action, e.g. "case.read", "ai.query", "export", "policy.denied". */
  action: string;
  /** The target entity of the action. */
  target: string;
  /** Reason recorded with every decision (§20.2) — present on denials esp. */
  reason: string | null;
}

/** `GET /audit` (case-scoped) paged list (§29.2). */
export interface ActivityLog {
  items: ActivityEntry[];
  total: number;
  limit: number;
  offset: number;
}
