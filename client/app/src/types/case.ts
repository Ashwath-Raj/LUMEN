/**
 * Case contract types — the investigation surface (Case Registry E.3, Case
 * Workspace E.4).
 *
 * ── GENERATION NOTE (arch §G) ────────────────────────────────────────────
 * These are transcribed from the backend's OWN authoritative shapes, not
 * invented: the `Case` / `CaseParticipant` / `Officer` / `Charge` / `Station` /
 * `ProcessEvent` semantic dataclasses (`lumen/semantics/entities.py`, §2.1), the
 * §2.3 canonical display forms (`lumen/semantics/render.py`), and the §3.5
 * schema. The spec deliberately leaves the case aggregate as an open `dict`
 * (`EntityContract.data`, §7) — so, exactly as Sessions 0/1 did for `/overview`,
 * this file transcribes what §29.1 (`GET /cases`, `/cases/{id}`) must return to
 * render §2.3 and marks it for generation once a field-level contract lands.
 *
 * The semantic entities carry lookup IDs (crime head, gravity, status, station,
 * officer); §2.3 renders their NAMES via repository joins. The API's job is to
 * return the resolved semantic form, so the types below carry the resolved
 * display fields the UI reads — never table/column names (§2 rule), never P9
 * fields (caste/religion/DOB are stored, never rendered — §4.2).
 *
 * `Insight` and `ProcessEvent`-derived events reuse the FROZEN contracts
 * (`contracts.ts` §8, `event.ts` §19.1); only the case-aggregate fields the spec
 * leaves open are transcribed here.
 * ─────────────────────────────────────────────────────────────────────────
 */
import type { RiskBand } from "@/design/tokens";
import type { Classification } from "./contracts";

/** §2.3 gravity is a named lookup (`GravityOffence`); the risk band is derived. */
export interface CaseGravity {
  id: string;
  name: string;
}

/** §3.5 case status (`CaseStatusMaster`), e.g. "Under Investigation". */
export interface CaseStatus {
  id: string;
  name: string;
}

/** §2.1 CrimeType — two-level (`CrimeHead` + `CrimeSubHead`). */
export interface CrimeType {
  head_id: string;
  head_name: string;
  sub_head_id: string | null;
  sub_head_name: string | null;
}

/** §2.1 Officer, resolved for display (§2.3 "PSI Ramesh …, Whitefield PS"). */
export interface CaseOfficer {
  employee_id: string;
  display_name: string;
  rank_short_name: string | null;
  station_name: string | null;
  /** Registering officer vs investigating officer (both are Officer, §2.1). */
  role: "registering" | "investigating";
}

/** §2.1 Station (`Unit` where type = police station). */
export interface CaseStation {
  unit_id: string;
  unit_name: string;
  district_id: string;
  district_name: string;
}

/**
 * One §29.1 `GET /cases` row — the Registry grid columns (E.3):
 * CrimeNo · title · district · station · status · priority(gravity) · officer
 * · created · updated · risk · confidence · quality.
 *
 * Risk/confidence/quality come from the case's derived insights (§5.2, §9); a
 * case with none yet leaves them null (rendered as "—", never fabricated).
 */
export interface CaseListItem {
  case_master_id: string;
  crime_no: string;
  /** §2.3 short title, e.g. crime-type name; the row's human label. */
  title: string;
  crime_type: CrimeType;
  gravity: CaseGravity;
  status: CaseStatus;
  district_name: string;
  station_name: string;
  /** Investigating officer display name (may be unassigned). */
  officer_name: string | null;
  crime_registered_date: string | null;
  updated_at: string | null;
  /** Derived (§5.2/§9) — null when the case has no insight yet. */
  risk_band: RiskBand | null;
  risk_score: number | null;
  confidence: number | null;
  quality_score: number | null;
  /** Count of insights attached (E.3 "insight count" column affordance). */
  insight_count: number;
  classification: Classification;
}

/** §29.2 paged list envelope for `GET /cases`. */
export interface CaseList {
  items: CaseListItem[];
  total: number;
  limit: number;
  offset: number;
}

/** A case participant (§2.1 CaseParticipant) — role in one case, not a human. */
export interface CaseParticipant {
  role: "accused" | "victim" | "complainant";
  /** Ordering label (A1, A2, V1…) — NOT identity (§3.2 fact 2). */
  label: string;
  /** Display name; masked per role below threshold (§4.2) → e.g. "A2 (masked)". */
  display_name: string;
  /** True when the name is masked for the current viewer (§4.2). */
  masked: boolean;
  /** Resolved person link when entity resolution attached one (§6); else null. */
  person_id: string | null;
}

/** §2.1 Charge, rendered "IPC 302 — Punishment for murder" (§2.3). */
export interface CaseCharge {
  act_short_name: string;
  section_id: string;
  section_description: string | null;
}

/** §3.5 court (`Court`). */
export interface CaseCourt {
  court_id: string;
  court_name: string;
}

/**
 * `GET /cases/{id}` aggregate (§29.1 "one aggregate call renders header +
 * entities"). Header fields + the entity columns the Overview tab shows. Graph /
 * geo payloads are separate endpoints and NOT included (Session 4/3).
 */
export interface CaseDetail {
  case_master_id: string;
  crime_no: string;
  title: string;
  crime_type: CrimeType;
  gravity: CaseGravity;
  status: CaseStatus;
  classification: Classification;

  station: CaseStation;
  court: CaseCourt | null;
  officers: CaseOfficer[];
  participants: CaseParticipant[];
  charges: CaseCharge[];

  crime_registered_date: string | null;
  incident_from_date: string | null;
  incident_to_date: string | null;
  info_received_ps_date: string | null;
  updated_at: string | null;

  /** Brief facts (CONFIDENTIAL — truncated below District SP, §4.2). */
  brief_facts: string | null;
  latitude: number | null;
  longitude: number | null;

  /** Derived summary (§5.2/§9) — null when no insight exists yet. */
  risk_band: RiskBand | null;
  risk_score: number | null;
  confidence: number | null;
  quality_score: number | null;
}
