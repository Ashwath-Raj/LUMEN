/**
 * Session/client state types — arch §G ("one small session context: user, role,
 * scope, degradation level from the last envelope"). No global store.
 */
import type { DegradationLevel } from "./envelope";

/** §20.1 roles. */
export type Role =
  | "state_analyst"
  | "district_sp"
  | "investigating_officer"
  | "station_officer"
  | "auditor";

/** The authenticated operator (Catalyst Authentication, §26.1 row 17). */
export interface Operator {
  id: string;
  name: string;
  email: string;
}

/** The session context value (arch §G). */
export interface Session {
  operator: Operator | null;
  role: Role | null;
  /** Human-readable scope, e.g. "District SP · Mysuru" (shell scope indicator). */
  scopeLabel: string | null;
  /** Latest degradation level seen on an envelope's meta (drives the pill). */
  degradationLevel: DegradationLevel;
}
