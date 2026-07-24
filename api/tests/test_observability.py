"""
Session 20 — observability (§25).

Covers: the §25 /system/metrics surface — all ten field keys present; the six
metrics computable from persisted tables aggregated deterministically (insight
counts by kind + lifecycle, policy denials, AI fallback/latency, quality score
trend, AI eval scorecard); the four uninstrumented metrics (+ LLM token
counts) reported "not available" and never fabricated (§24.3 rule 5); the
/system/metrics + /system/health endpoints; determinism; and empty-data edges.

Reads only — no business logic duplicated (each subsystem owns its
computation; observability aggregates the persisted output).

Self-contained: in-memory SQLite; QuickML absent → §16.4 fallback path.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.ai import orchestrator, provider
from lumen.ai.eval.runner import run_eval
from lumen.bus import signals
from lumen.jobs.quality import run_quality_precompute
from lumen.jobs.resolve import run_resolution
from lumen.jobs.seed import seed_database
from lumen.graph.projection import run_projection
from lumen.observability import health as obs_health
from lumen.observability import metrics as M
from lumen.policy.engine import PolicyUser, Resource, authorize
from lumen.resilience.degradation import NOT_AVAILABLE

NOW = datetime(2026, 7, 25, 0, 0, tzinfo=timezone.utc)

# §25's ten metric fields, in the response.
SPEC_KEYS = {
    "insight_counts", "policy_denials", "ai", "quality_score_trend",
    "ai_eval_scorecard", "latency_percentiles_per_route", "cache_hit_rate",
    "precompute_duration_and_last_run", "graph_query_timings", "llm_token_counts",
}


def _fresh():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


@pytest.fixture(autouse=True)
def _isolate():
    signals.clear_subscribers()
    provider.set_provider(provider.QuickMLProvider())
    yield
    signals.clear_subscribers()
    provider.set_provider(provider.QuickMLProvider())


@pytest.fixture()
def populated():
    s = _fresh()
    seed_database(s)
    run_resolution(s)
    run_projection(s, now=NOW)
    run_quality_precompute(s, now=NOW)
    orchestrator.ask(s, "what does section 302 cover", now=NOW)     # fallback
    orchestrator.ask(s, "tell me about case 1000", now=NOW)
    run_eval(s, run_id="run-a", now=NOW)
    authorize(s, PolicyUser("u", "auditor"), "read_case_detail",
              Resource("case", "1"), now=NOW)                        # a denial
    s.commit()
    return s


# ── §25 surface shape ───────────────────────────────────────────────────────

def test_metrics_has_all_ten_spec_fields(populated):
    met = M.system_metrics(populated)
    assert set(met) == SPEC_KEYS


def test_four_uninstrumented_metrics_are_not_available(populated):
    met = M.system_metrics(populated)
    for field in ("latency_percentiles_per_route", "cache_hit_rate",
                  "precompute_duration_and_last_run", "graph_query_timings",
                  "llm_token_counts"):
        assert met[field] == NOT_AVAILABLE
    # LLM token counts also surfaced not-available inside the ai block
    assert met["ai"]["llm_token_counts"] == NOT_AVAILABLE


# ── insight counts by kind + lifecycle ─────────────────────────────────────

def test_insight_counts_by_kind_and_lifecycle(populated):
    ic = M.insight_counts(populated)
    assert ic["total"] >= 2                          # the AI summaries
    assert "summary" in ic["by_kind"]                # AI orchestrator insights
    assert "generated" in ic["by_lifecycle_state"]
    assert ic["total"] == sum(ic["by_kind"].values())
    assert ic["total"] == sum(ic["by_lifecycle_state"].values())


# ── policy denials ──────────────────────────────────────────────────────────

def test_policy_denials_counted(populated):
    pd = M.policy_denials(populated)
    assert pd["total"] == 1
    assert pd["by_action"].get("read_case_detail") == 1


def test_policy_denials_only_counts_denies():
    s = _fresh()
    seed_database(s)
    authorize(s, PolicyUser("u", "state_analyst"), "read_case_detail",
              Resource("case", "1", district_id=1), now=NOW)         # allow
    s.commit()
    assert M.policy_denials(s)["total"] == 0


# ── AI query metrics (fallback + latency) ──────────────────────────────────

def test_ai_metrics_fallback_and_latency(populated):
    ai = M.ai_query_metrics(populated)
    # every AIQueryExecuted event counts — the 2 explicit asks plus the eval
    # run's golden + adversarial questions (each is a real orchestrator.ask).
    # QuickML is absent, so answered queries take the §16.4 fallback path; the
    # adversarial P9/individual-prediction cases are 'declined' (not fallback),
    # so fallback_invocations is a strict majority but not all.
    assert ai["ai_queries_total"] >= 2
    assert 0.0 < ai["fallback_rate"] <= 1.0
    assert ai["fallback_invocations"] <= ai["ai_queries_total"]
    lat = ai["ai_latency_ms"]
    assert lat["count"] == ai["ai_queries_total"]
    assert "p95_ms" in lat and lat["max_ms"] >= lat["min_ms"]


# ── quality score trend ─────────────────────────────────────────────────────

def test_quality_trend_per_dimension(populated):
    trend = M.quality_trend(populated)
    # the six §5.2 dimensions
    assert set(trend) == {"completeness", "consistency", "integrity",
                          "timeliness", "uniqueness", "validity"}
    for dim, points in trend.items():
        assert points
        for p in points:
            assert 0.0 <= p["mean_score"] <= 1.0
            assert "computed_at" in p


# ── AI eval scorecard ───────────────────────────────────────────────────────

def test_eval_scorecard_aggregates_run(populated):
    sc = M.eval_scorecard(populated, run_id="run-a")
    assert sc["run_id"] == "run-a"
    assert sc["question_count"] == 41
    assert sc["groundedness"] == 1.0                 # §17.2 invariant
    assert sc["hallucinated_ids_total"] == 0
    assert sc["prompt_version"] == "v1"


def test_eval_scorecard_defaults_to_latest_run(populated):
    sc = M.eval_scorecard(populated)                 # no run_id → latest
    assert sc["run_id"] == "run-a"


# ── endpoints ───────────────────────────────────────────────────────────────

def test_system_metrics_endpoint():
    from fastapi.testclient import TestClient
    import main as app_main
    from lumen.db.session import get_db

    engine = create_engine("sqlite:///file:obsmem?mode=memory&cache=shared&uri=true",
                           connect_args={"uri": True})
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    setup = TestingSession()
    seed_database(setup)
    run_quality_precompute(setup, now=NOW)
    run_eval(setup, run_id="ep", now=NOW)
    setup.commit()
    setup.close()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app_main.app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app_main.app)
        resp = client.get("/api/system/metrics")
        assert resp.status_code == 200
        body = resp.json()
        assert set(body) == SPEC_KEYS
        assert body["cache_hit_rate"] == "not available"
        assert body["ai_eval_scorecard"]["run_id"] == "ep"
    finally:
        app_main.app.dependency_overrides.pop(get_db, None)


def test_metrics_endpoint_registered():
    import main as app_main
    assert "/api/system/metrics" in app_main.app.openapi()["paths"]


def test_health_delegates_to_resilience():
    """§25 /system/health delegates to the Session-18 computation — same
    payload, single source of truth."""
    rep = obs_health.system_health({})
    assert rep["degradation_level"] == 0
    assert "dependencies" in rep and len(rep["dependencies"]) == 9


# ── determinism + empty-data edges ─────────────────────────────────────────

def test_metrics_are_deterministic(populated):
    assert M.system_metrics(populated) == M.system_metrics(populated)


def test_empty_database_metrics():
    s = _fresh()                                     # no data at all
    met = M.system_metrics(s)
    assert set(met) == SPEC_KEYS                      # full shape still present
    assert met["insight_counts"]["total"] == 0
    assert met["policy_denials"]["total"] == 0
    assert met["ai"]["ai_queries_total"] == 0
    assert met["ai"]["fallback_rate"] == 0.0
    assert met["quality_score_trend"] == {}
    assert met["ai_eval_scorecard"]["question_count"] == 0
