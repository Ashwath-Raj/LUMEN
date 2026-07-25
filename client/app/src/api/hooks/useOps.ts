/**
 * Ops + quality hooks  — the REAL, DB-backed judge-facing
 * surfaces: §5.3 quality scores/findings, §24.2 health, §25 metrics, §22
 * registries, §17.4 eval. Shapes transcribed from the live responses of the
 * implemented routers (quality.py, system.py). One endpoint → one hook.
 */
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { queryKeys } from "@/api/queryKeys";

// ── Quality (§5.2/§5.3) ────────────────────────────────────────────────

export interface QualityScoreRow {
  scope_type: string;
  scope_id: string;
  dimension: string;
  score: number;
  computed_at: string | null;
}

export interface QualityFindingRow {
  finding_id: number;
  rule_id: string;
  severity: string;
  entity_type: string;
  entity_id: string;
  detail: string | null;
  detected_at: string | null;
  state: string | null;
}

export function useQualityScores(scopeType?: string) {
  return useQuery({
    queryKey: [...queryKeys.qualityScores(), scopeType ?? "all"],
    queryFn: async ({ signal }) => {
      const query = new URLSearchParams();
      if (scopeType) query.set("scope_type", scopeType);
      const { data } = await apiFetch<{ total: number; scores: QualityScoreRow[] }>(
        ENDPOINTS.qualityScores,
        { signal, query },
      );
      return data;
    },
  });
}

export function useQualityFindings(ruleId?: string, limit = 100, offset = 0) {
  return useQuery({
    queryKey: [...queryKeys.qualityFindings(), ruleId ?? "all", limit, offset],
    queryFn: async ({ signal }) => {
      const query = new URLSearchParams({ limit: String(limit), offset: String(offset) });
      if (ruleId) query.set("rule_id", ruleId);
      const { data } = await apiFetch<{ total: number; findings: QualityFindingRow[] }>(
        ENDPOINTS.qualityFindings,
        { signal, query },
      );
      return data;
    },
  });
}

// ── System (§22/§24/§25/§17.4) ─────────────────────────────────────────

export interface HealthDependency {
  dependency: string;
  state: string;
  response: unknown;
  user_sees: string | null;
}

export interface SystemHealth {
  degradation_level: number;
  degradation_label: string;
  dependencies: HealthDependency[];
}

export function useSystemHealth() {
  return useQuery({
    queryKey: queryKeys.systemHealth(),
    queryFn: async ({ signal }) => {
      const { data } = await apiFetch<SystemHealth>(ENDPOINTS.systemHealth, { signal });
      return data;
    },
  });
}

export interface SystemMetrics {
  insight_counts: { total: number; by_kind: Record<string, number>; by_lifecycle_state: Record<string, number> };
  policy_denials: { total: number; by_action: Record<string, number> };
  ai: {
    ai_queries_total: number;
    fallback_invocations: number;
    fallback_rate: number;
    ai_latency_ms: Record<string, number>;
    llm_token_counts: unknown;
  };
  [key: string]: unknown;
}

export function useSystemMetrics() {
  return useQuery({
    queryKey: queryKeys.systemMetrics(),
    queryFn: async ({ signal }) => {
      const { data } = await apiFetch<SystemMetrics>(ENDPOINTS.systemMetrics, { signal });
      return data;
    },
  });
}

export interface RegistryItem {
  model_id?: string;
  name: string;
  kind?: string;
  version?: string;
  active?: boolean;
  trained_at?: string;
  [key: string]: unknown;
}

export interface SystemRegistry {
  services: { total: number; items: RegistryItem[] };
  models: { total: number; items: RegistryItem[] };
  prompts?: { total: number; items: RegistryItem[] };
  [key: string]: unknown;
}

export function useSystemRegistry() {
  return useQuery({
    queryKey: queryKeys.systemRegistry(),
    queryFn: async ({ signal }) => {
      const { data } = await apiFetch<SystemRegistry>(ENDPOINTS.systemRegistry, { signal });
      return data;
    },
  });
}

export interface SystemEval {
  run_id: string | null;
  question_count: number;
  /** §17.2 metrics, present once a run has been persisted. */
  groundedness?: number;
  correctness?: number;
  hallucinated_ids_total?: number;
  prompt_version?: string;
  [key: string]: unknown;
}

export function useSystemEval() {
  return useQuery({
    queryKey: queryKeys.systemEval(),
    queryFn: async ({ signal }) => {
      const { data } = await apiFetch<SystemEval>(ENDPOINTS.systemEval, { signal });
      return data;
    },
  });
}
