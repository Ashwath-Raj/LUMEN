"""
System metrics — LUMEN_MASTER_SPEC_V3 §25.

§25 lists ten metrics for `/system/metrics`:

  1. latency percentiles per route
  2. cache hit rate
  3. precompute duration and last run
  4. graph query timings
  5. LLM latency and token counts
  6. insight counts by kind and lifecycle state
  7. fallback invocations
  8. policy denials
  9. quality score trend
  10. AI evaluation scorecard

Six are computable DETERMINISTICALLY from persisted tables (no runtime
instrumentation): insight counts (lumen_insight), policy denials (lumen_audit),
the AI eval scorecard (lumen_ai_eval), the quality trend (lumen_quality_score),
fallback invocations + AI latency (AIQueryExecuted events in lumen_event).

Four require RUNTIME instrumentation that this platform does not persist —
per-route latency percentiles, cache hit rate, precompute/graph-query timings,
and LLM token counts. §25 itself says "Catalyst monitoring and logs cover
platform health": those live counters are the Catalyst runtime's, a later
session. This module does NOT fabricate them (§24.3 rule 5) — it reports them
as the "not available" marker, keeping every §25 field key present and honest.
Each is recorded in the Session deliverables as "Cannot determine from the
specification".

Reads only; no business logic is duplicated (insight/quality/eval/audit
subsystems own their computation — this aggregates their persisted output).
Deterministic and local: pure functions of the database, no wall-clock, no
external calls.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from lumen.db.models.eval import LumenAiEval
from lumen.db.models.event import LumenEvent
from lumen.db.models.intelligence import LumenInsight
from lumen.db.models.policy import LumenAudit
from lumen.db.models.quality import LumenQualityScore
from lumen.resilience.degradation import NOT_AVAILABLE

# §25 metrics with no persisted backing (runtime instrumentation is Catalyst's;
# a later session). Reported as NOT_AVAILABLE — never fabricated.
UNINSTRUMENTED = {
    "latency_percentiles_per_route": NOT_AVAILABLE,
    "cache_hit_rate": NOT_AVAILABLE,
    "precompute_duration_and_last_run": NOT_AVAILABLE,
    "graph_query_timings": NOT_AVAILABLE,
    "llm_token_counts": NOT_AVAILABLE,
}


# ── 6. insight counts by kind and lifecycle state ──────────────────────────

def insight_counts(session: Session) -> dict:
    by_kind: dict[str, int] = {}
    by_state: dict[str, int] = {}
    for row in session.query(LumenInsight).all():
        by_kind[row.kind] = by_kind.get(row.kind, 0) + 1
        by_state[row.lifecycle_state] = by_state.get(row.lifecycle_state, 0) + 1
    return {"total": sum(by_kind.values()),
            "by_kind": dict(sorted(by_kind.items())),
            "by_lifecycle_state": dict(sorted(by_state.items()))}


# ── 8. policy denials ───────────────────────────────────────────────────────

def policy_denials(session: Session) -> dict:
    denials = session.query(LumenAudit).filter(LumenAudit.decision == "deny").all()
    by_action: dict[str, int] = {}
    for row in denials:
        by_action[row.action] = by_action.get(row.action, 0) + 1
    return {"total": len(denials), "by_action": dict(sorted(by_action.items()))}


# ── 7 + partial 5. fallback invocations + AI latency (AIQueryExecuted) ─────

def ai_query_metrics(session: Session) -> dict:
    """From the AIQueryExecuted event store: total queries, fallback
    invocations, and end-to-end latency stats. §25's 'LLM latency' is served
    as the AI end-to-end latency recorded per query; the LLM-only split and
    token counts are not instrumented (NOT_AVAILABLE)."""
    events = (session.query(LumenEvent)
              .filter(LumenEvent.event_type == "AIQueryExecuted").all())
    total = len(events)
    fallbacks = 0
    latencies: list[float] = []
    for e in events:
        payload = e.payload or {}
        if payload.get("method") == "deterministic_fallback":
            fallbacks += 1
        lat = payload.get("latency_ms")
        if isinstance(lat, (int, float)):
            latencies.append(float(lat))
    latency_stats = {"count": len(latencies)}
    if latencies:
        ordered = sorted(latencies)
        latency_stats.update({
            "min_ms": ordered[0],
            "max_ms": ordered[-1],
            "mean_ms": round(sum(ordered) / len(ordered), 2),
            "p95_ms": ordered[min(len(ordered) - 1,
                                  int(round(0.95 * (len(ordered) - 1))))],
        })
    return {
        "ai_queries_total": total,
        "fallback_invocations": fallbacks,
        "fallback_rate": (fallbacks / total) if total else 0.0,
        "ai_latency_ms": latency_stats,
        "llm_token_counts": NOT_AVAILABLE,          # §25 — not instrumented
    }


# ── 9. quality score trend ──────────────────────────────────────────────────

def quality_trend(session: Session) -> dict:
    """Per-dimension mean score over time (computed_at buckets). Deterministic
    aggregation of lumen_quality_score."""
    rows = session.query(LumenQualityScore).all()
    by_dim: dict[str, list[tuple]] = {}
    for r in rows:
        if r.score is None or r.computed_at is None:
            continue
        by_dim.setdefault(r.dimension, []).append((r.computed_at.isoformat(), r.score))
    trend: dict[str, list] = {}
    for dim, points in sorted(by_dim.items()):
        # aggregate to one mean per computed_at timestamp, ordered in time
        buckets: dict[str, list[float]] = {}
        for ts, score in points:
            buckets.setdefault(ts, []).append(score)
        trend[dim] = [{"computed_at": ts,
                       "mean_score": round(sum(v) / len(v), 4)}
                      for ts, v in sorted(buckets.items())]
    return trend


# ── 10. AI evaluation scorecard ─────────────────────────────────────────────

def eval_scorecard(session: Session, *, run_id: str | None = None) -> dict:
    """Aggregate lumen_ai_eval for the given run (or the latest run present).
    Deterministic means over the run's per-question rows."""
    q = session.query(LumenAiEval)
    if run_id is None:
        latest = (session.query(LumenAiEval)
                  .order_by(LumenAiEval.evaluated_at.desc()).first())
        if latest is None:
            return {"run_id": None, "question_count": 0}
        run_id = latest.run_id
    rows = q.filter(LumenAiEval.run_id == run_id).all()
    if not rows:
        return {"run_id": run_id, "question_count": 0}
    n = len(rows)
    return {
        "run_id": run_id,
        "question_count": n,
        "groundedness": round(sum(r.groundedness or 0.0 for r in rows) / n, 4),
        "correctness": round(sum(r.correctness or 0.0 for r in rows) / n, 4),
        "hallucinated_ids_total": sum(r.hallucinated_ids or 0 for r in rows),
        "prompt_version": rows[0].prompt_version,
    }


# ── the /system/metrics payload (all ten §25 fields) ───────────────────────

def system_metrics(session: Session) -> dict:
    """The §25 metrics surface: six computed, four (+ token counts) as
    'not available'. Every §25 field key is present."""
    return {
        # computable from persisted tables
        "insight_counts": insight_counts(session),
        "policy_denials": policy_denials(session),
        "ai": ai_query_metrics(session),
        "quality_score_trend": quality_trend(session),
        "ai_eval_scorecard": eval_scorecard(session),
        # not instrumented in this platform (Catalyst runtime — later session)
        **UNINSTRUMENTED,
    }
