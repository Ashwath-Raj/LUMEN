/**
 * Which parameter slots each §14.4 named query needs — mirrors the router's
 * `need(...)` guards, so the form marks exactly the params the backend requires
 * (a missing one is a 422, never a silent empty graph).
 */
import type { NetworkQueryParams } from "@/api";

export const QUERY_PARAMS: Record<string, Array<keyof NetworkQueryParams>> = {
  q1: ["person_a", "person_b"],
  q2: ["group_a", "group_b"],
  q3: [],
  q4: ["district_id"],
  q5: ["top_n"],
  q6: [],
  q7: ["case_id"],
  q8: [],
  q9: ["as_of"],
  q10: ["case_id"],
};
