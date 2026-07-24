"""
Session 18 — resilience / failure strategy (§24).

The §33 row-11 done-when, enforced in CI: "Killing QuickML degrades to L3"
(the visible banner is the frontend pill, a later session; the level
computation and its "user sees" text are here).

Covers: §24.3 rule-2 circuit breaker (3 failures/60 s → open 120 s →
half-open → close; rolling window; half-open probe failure re-opens), §24.1
per-dependency timeouts + rule-1 timeout guard, §24.3 rule-3 retry (2 attempts,
idempotent reads only, never retry generation), §24.2 L0-L4 ladder + level
resolution from health, the §24.1 response matrix verbatim, §24.3 rule-5
never-fabricate marker, §24.3 rule-6 audit half (lumen_audit), the §24.2
/system/health endpoint, determinism, and edge cases.

Self-contained: in-memory SQLite; deterministic injected clock — no wall-clock,
no sleeps, no live external services.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.resilience import breaker, degradation, timeouts
from lumen.resilience.breaker import BreakerState, CircuitOpen
from lumen.resilience.degradation import Level
from lumen.resilience.timeouts import DependencyTimeout

NOW = datetime(2026, 7, 25, 0, 0, tzinfo=timezone.utc)


class Clock:
    """Deterministic monotonic clock (seconds)."""
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, s):
        self.t += s


def _fresh():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


# ── §24.3 rule 2: circuit breaker ──────────────────────────────────────────

def test_breaker_constants_match_spec():
    assert breaker.FAILURE_THRESHOLD == 3
    assert breaker.FAILURE_WINDOW_S == 60.0
    assert breaker.OPEN_DURATION_S == 120.0


def test_three_failures_in_window_opens():
    c = Clock()
    b = breaker.CircuitBreaker("quickml", c)
    b.record_failure(); b.record_failure()
    assert b.state() is BreakerState.CLOSED and b.allows()
    b.record_failure()
    assert b.state() is BreakerState.OPEN and not b.allows()


def test_open_transitions_to_half_open_after_120s():
    c = Clock()
    b = breaker.CircuitBreaker("quickml", c)
    for _ in range(3):
        b.record_failure()
    c.advance(119.9)
    assert b.state() is BreakerState.OPEN
    c.advance(0.2)                                # 120.1 s
    assert b.state() is BreakerState.HALF_OPEN and b.allows()


def test_half_open_success_closes():
    c = Clock()
    b = breaker.CircuitBreaker("quickml", c)
    for _ in range(3):
        b.record_failure()
    c.advance(121)
    assert b.state() is BreakerState.HALF_OPEN
    b.record_success()
    assert b.state() is BreakerState.CLOSED


def test_half_open_failure_reopens_for_another_120s():
    c = Clock()
    b = breaker.CircuitBreaker("quickml", c)
    for _ in range(3):
        b.record_failure()
    c.advance(121)
    assert b.state() is BreakerState.HALF_OPEN
    b.record_failure()                            # probe fails
    assert b.state() is BreakerState.OPEN
    c.advance(119)
    assert b.state() is BreakerState.OPEN         # fresh 120 s window


def test_failures_outside_window_do_not_accumulate():
    c = Clock()
    b = breaker.CircuitBreaker("g", c)
    b.record_failure(); b.record_failure()
    c.advance(61)                                 # first two age out
    b.record_failure()
    assert b.state() is BreakerState.CLOSED       # only 1 in-window failure


def test_breaker_call_rejects_when_open():
    c = Clock()
    b = breaker.CircuitBreaker("quickml", c)
    for _ in range(3):
        b.record_failure()
    with pytest.raises(CircuitOpen):
        b.call(lambda: "never runs")


def test_breaker_call_records_outcome():
    c = Clock()
    b = breaker.CircuitBreaker("quickml", c)
    assert b.call(lambda: 42) == 42               # success
    def boom():
        raise RuntimeError("x")
    for _ in range(3):
        with pytest.raises(RuntimeError):
            b.call(boom)
    assert b.state() is BreakerState.OPEN


def test_registry_preregisters_quickml_and_graph():
    reg = breaker.BreakerRegistry(Clock())
    assert set(reg.states()) == {"quickml", "graph_backend"}
    assert reg.get("quickml").name == "quickml"


# ── §24.1 timeouts + §24.3 rule 1 ──────────────────────────────────────────

def test_spec_fixed_timeouts():
    assert timeouts.timeout_for("data_store") == 3.0
    assert timeouts.timeout_for("cache") == 0.2       # 200 ms
    assert timeouts.timeout_for("quickml_llm") == 15.0


def test_call_over_budget_raises_timeout():
    c = Clock()
    def slow():
        c.advance(4.0)                                # exceeds 3 s store budget
        return "done"
    with pytest.raises(DependencyTimeout):
        timeouts.call_with_timeout("data_store", slow, clock=c)


def test_call_within_budget_returns_result():
    c = Clock()
    def fast():
        c.advance(0.05)
        return "ok"
    r = timeouts.call_with_timeout("cache", fast, clock=c)
    assert r.value == "ok" and r.elapsed_s == pytest.approx(0.05)


# ── §24.3 rule 3: retry (idempotent reads only) ────────────────────────────

def test_idempotent_read_retries_twice():
    calls = {"n": 0}
    def flaky():
        calls["n"] += 1
        raise RuntimeError("boom")
    with pytest.raises(RuntimeError):
        timeouts.retry_read(flaky, idempotent=True)
    assert calls["n"] == timeouts.RETRY_ATTEMPTS == 2


def test_non_idempotent_never_retried():
    calls = {"n": 0}
    def gen():
        calls["n"] += 1
        raise RuntimeError("generation failed")
    with pytest.raises(RuntimeError):
        timeouts.retry_read(gen, idempotent=False)
    assert calls["n"] == 1                            # never retry generation


def test_retry_returns_on_eventual_success():
    calls = {"n": 0}
    def eventually():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("first fails")
        return "recovered"
    assert timeouts.retry_read(eventually, idempotent=True) == "recovered"


def test_backoff_is_exponential_and_deterministic():
    assert timeouts.backoff_delay(1) == pytest.approx(0.1)
    assert timeouts.backoff_delay(2) == pytest.approx(0.2)
    # jitter is injected, not random → reproducible
    assert timeouts.backoff_delay(1, jitter=1.0) == pytest.approx(0.15)
    assert timeouts.backoff_delay(1, jitter=-1.0) == pytest.approx(0.05)


# ── §24.2 degradation ladder ───────────────────────────────────────────────

def test_ladder_levels_named():
    assert degradation.LEVEL_NAMES[Level.L0] == "FULL"
    assert degradation.LEVEL_NAMES[Level.L3] == "DETERMINISTIC"
    assert degradation.LEVEL_NAMES[Level.L4] == "READ-ONLY"


def test_all_healthy_is_l0():
    assert degradation.resolve_level(set()) == Level.L0


def test_killing_quickml_degrades_to_l3():
    """§33 row-11 done-when: 'Killing QuickML degrades to L3'."""
    level = degradation.resolve_level({"quickml_llm"})
    assert level == Level.L3
    assert degradation.level_label(level) == "L3 — DETERMINISTIC"
    # the §24.1 "user sees" banner text for the QuickML row
    assert "evidence-based summary" in degradation.RESPONSES["quickml_llm"].user_sees


def test_store_loss_is_l4_and_dominates():
    assert degradation.resolve_level({"data_store"}) == Level.L4
    # worst level wins when several apply
    assert degradation.resolve_level({"cache", "quickml_llm", "data_store"}) == Level.L4


def test_response_matrix_is_verbatim():
    assert len(degradation.RESPONSES) == 9
    ds = degradation.RESPONSES["data_store"]
    assert ds.detection == "Health probe, timeout 3 s"
    assert ds.response == "Serve cached payloads; read-only mode"
    llm = degradation.RESPONSES["quickml_llm"]
    assert llm.detection == "Timeout 15 s, circuit breaker at 3 failures/60 s"


# ── §24.3 rule 5: never fabricate ──────────────────────────────────────────

def test_not_available_never_fabricates():
    assert degradation.not_available(None) == "not available"
    assert degradation.not_available(0) == 0          # a real zero is preserved
    assert degradation.not_available("") == ""
    assert degradation.not_available(42) == 42


# ── §24.1 health evaluation → level ────────────────────────────────────────

def test_evaluate_health_states():
    probes = {"quickml_llm": lambda: False, "data_store": lambda: True,
              "cache": lambda: (_ for _ in ()).throw(RuntimeError())}
    states = degradation.evaluate_health(probes)
    assert states["quickml_llm"] == "unhealthy"
    assert states["data_store"] == "healthy"
    assert states["cache"] == "unhealthy"            # a throwing probe is unhealthy
    assert states["stratus"] == "unknown"            # no probe → unknown


def test_health_report_computes_level():
    rep = degradation.health_report({"quickml_llm": lambda: False})
    assert rep["degradation_level"] == 3
    assert rep["degradation_label"] == "L3 — DETERMINISTIC"
    q = next(d for d in rep["dependencies"] if d["dependency"] == "quickml_llm")
    assert q["state"] == "unhealthy" and "evidence-based summary" in q["user_sees"]


def test_health_report_all_unknown_is_l0():
    rep = degradation.health_report({})
    assert rep["degradation_level"] == 0             # no probe ≠ failure (rule 5)
    assert all(d["state"] == "unknown" for d in rep["dependencies"])


# ── §24.3 rule 6: audit half ───────────────────────────────────────────────

def test_degradation_transition_is_audited():
    from lumen.policy import audit_repo
    s = _fresh()
    degradation.audit_degradation(s, from_level=Level.L0, to_level=Level.L3,
                                  reason="QuickML circuit opened", now=NOW)
    s.commit()
    rows = audit_repo.read(s, action="degradation")
    assert len(rows) == 1
    assert rows[0].decision == "L3 — DETERMINISTIC"
    assert "QuickML circuit opened" in rows[0].reason


# ── §24.2 /system/health endpoint ──────────────────────────────────────────

def test_system_health_endpoint():
    from fastapi.testclient import TestClient
    import main as app_main

    client = TestClient(app_main.app)
    resp = client.get("/api/system/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "degradation_level" in body and "dependencies" in body
    assert body["degradation_level"] == 0            # no live probes here → L0
    assert len(body["dependencies"]) == 9


def test_top_level_health_endpoint_unchanged():
    """Sessions 1-17 /health must still answer identically."""
    from fastapi.testclient import TestClient
    import main as app_main
    resp = TestClient(app_main.app).get("/health")
    assert resp.status_code == 200 and resp.json()["status"] == "ok"


# ── determinism ─────────────────────────────────────────────────────────────

def test_breaker_behaviour_is_deterministic():
    def run():
        c = Clock()
        b = breaker.CircuitBreaker("x", c)
        seq = []
        for _ in range(3):
            b.record_failure()
        seq.append(b.state().value)
        c.advance(121)
        seq.append(b.state().value)
        b.record_success()
        seq.append(b.state().value)
        return seq
    assert run() == run() == ["open", "half_open", "closed"]
