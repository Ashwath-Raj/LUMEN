/**
 * Intelligence Workbench types .
 *
 * ── GENERATION NOTE (arch §G) ────────────────────────────────────────────
 * `AskRequest` is transcribed VERBATIM from the real `/ai/ask` router
 * (`api/lumen/api/routers/ai.py`: `{question, district_scope?}`); its response
 * is the frozen §8 `Insight` (`types/contracts.ts`) — nothing new to define.
 *
 * `IntelligenceLead` is the LeadCard's display shape over §18 decision support.
 * §18 states recommendations are `Insight(kind="recommendation")` derived from
 * existing insights — "no new model" — so `/recommendations` serves persisted
 * recommendation Insights and the list is empty until the intelligence engine
 * generates them. Nothing is fabricated.
 * ─────────────────────────────────────────────────────────────────────────
 */
import type { RiskBand } from "@/design/tokens";

/** POST /ai/ask request body (real router shape, verbatim). */
export interface AskRequest {
  question: string;
  district_scope?: number[];
}

/** One intelligence lead (display shape; endpoint 501 — see note above). */
export interface IntelligenceLead {
  lead_id: string;
  headline: string;
  priority: "critical" | "high" | "medium" | "low";
  confidence: number;
  risk_band: RiskBand | null;
  related_cases: string[];
  related_persons: string[];
  related_locations: string[];
  reasoning: string;
  suggested_actions: string[];
  generated_at: string;
}

/** Lead-panel sort orders (Session-5 brief). */
export type LeadSort = "confidence" | "priority" | "newest" | "relevance";

/** One workbench exchange: an analyst question + the AI's §8 Insight answer. */
import type { Insight } from "./contracts";
export interface Exchange {
  id: string;
  question: string;
  asked_at: string;
  /** Districts included as scope when asked (census codes, for display). */
  scope_districts: string[];
  status: "pending" | "answered" | "failed";
  insight?: Insight;
  error?: string;
}
