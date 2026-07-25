/**
 * Cross-boundary contract types — master spec §7, §8, §2.1.
 *
 * ── GENERATION NOTE (arch §G) ────────────────────────────────────────────
 * The architecture mandates these types be GENERATED from the backend's
 * Pydantic contracts (spec §7 rule 5: "Frontend types are generated from these
 * models — never hand-written"), so that a contract drift fails the typecheck.
 * The generator is not wired yet (no generation step exists); the
 * shapes below are a faithful hand-transcription of the spec's own models,
 * marked here so a generation step can replace this file wholesale. They are
 * the minimum the shell + `InsightCard` scaffold reference; feature sessions
 * extend from the generated set, never by hand-editing this file.
 * ─────────────────────────────────────────────────────────────────────────
 */

/** §2.1 closed semantic-entity vocabulary. */
export type EntityKind =
  | "case"
  | "person"
  | "case_participant"
  | "officer"
  | "station"
  | "jurisdiction"
  | "court"
  | "charge"
  | "crime_type"
  | "process_event"
  | "insight";

/** §8 Factor. */
export interface Factor {
  label: string;
  weight: number;
  detail: string | null;
}

/** §8 Evidence — always rendered as a clickable chip (D3). */
export interface Evidence {
  entity:
    | "case"
    | "person"
    | "participant"
    | "officer"
    | "station"
    | "jurisdiction"
    | "court"
    | "charge"
    | "process_event"
    | "kb_document";
  id: string;
  label: string;
  url: string;
}

/** §8 Lineage. */
export interface Lineage {
  method: string;
  model_version: string;
  prompt_version: string | null;
  features_used: string[];
  query_ids: string[];
  source_row_count: number;
  quality_score: number;
  computed_at: string;
}

/** §8 / §9 ConfidenceBreakdown — the five multiplicative components. */
export interface ConfidenceBreakdown {
  evidence_quality: number;
  model_confidence: number;
  data_completeness: number;
  identity_confidence: number;
  graph_confidence: number;
  composite: number;
}

export type InsightKind =
  | "risk"
  | "anomaly"
  | "linkage"
  | "network"
  | "forecast"
  | "summary"
  | "recommendation"
  | "data_quality";

export type LifecycleState =
  | "generated"
  | "verified"
  | "approved"
  | "operational"
  | "expired"
  | "archived"
  | "deleted";

export type Classification =
  | "PUBLIC"
  | "INTERNAL"
  | "CONFIDENTIAL"
  | "RESTRICTED";

/** §8 Insight — the platform's output currency; the whole `InsightCard`. */
export interface Insight {
  id: string;
  contract_version: string;
  kind: InsightKind;
  subject_type: "case" | "person" | "district" | "unit" | "state";
  subject_id: string;
  headline: string;
  score: number | null;
  confidence: number;
  confidence_breakdown: ConfidenceBreakdown;
  factors: Factor[];
  counterfactuals: string[];
  evidence: Evidence[];
  /** Never empty (§8 invariant 2). */
  limitations: string[];
  lineage: Lineage;
  lifecycle_state: LifecycleState;
  classification: Classification;
  generated_at: string;
  expires_at: string | null;
}
