"""
Session 22 — platform integration: the remaining §29.1 /system/* + /audit
APIs (§33 row 22: "/system/* live; denials audited").

Covers: GET /system/eval (the AI evaluation scorecard read); GET /audit
(Auditor-role-only via the §20 policy engine, with every denial written to
lumen_audit and emitting PolicyDenied — row-22's "denials audited"); the
audit read filters; that the k=5 aggregate suppression (§4.3 rule 3, the one
concrete ABAC rule) already exists and is reused, not duplicated; determinism;
and edge cases.

Integrations are consumed, never duplicated: observability.eval_scorecard
(Session 20), policy.engine.authorize + audit_repo (Session 16), the §19 bus.

Self-contained: in-memory SQLite, no live PostgreSQL / Catalyst auth.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.db.models import (  # noqa: F401 — register tables
    canonical, eval as _eval, event, policy,
)
from lumen.db.models.eval import LumenAiEval
from lumen.db.models.policy import LumenUserRole
from lumen.governance import masking
from lumen.policy import audit_repo
from lumen.policy.engine import PolicyUser, Resource, authorize
from lumen.bus import signals

NOW = datetime(2026, 7, 25, 0, 0, tzinfo=timezone.utc)


_DB_COUNTER = [0]


def _client_with_db():
    """A TestClient bound to a FRESH per-test shared in-memory DB; returns
    (client, Session factory, cleanup)."""
    from fastapi.testclient import TestClient
    import main as app_main
    from lumen.db.session import get_db

    _DB_COUNTER[0] += 1
    name = f"pi22_{_DB_COUNTER[0]}"
    engine = create_engine(
        f"sqlite:///file:{name}?mode=memory&cache=shared&uri=true",
        connect_args={"uri": True})
    # keep one connection open for the DB's lifetime so the shared in-memory
    # database is not discarded between sessions
    keepalive = engine.connect()
    Base.metadata.create_all(engine)
    TS = sessionmaker(bind=engine)

    def override():
        db = TS()
        try:
            yield db
        finally:
            db.close()

    app_main.app.dependency_overrides[get_db] = override
    client = TestClient(app_main.app)

    def cleanup():
        app_main.app.dependency_overrides.pop(get_db, None)
        keepalive.close()

    return client, TS, cleanup


@pytest.fixture(autouse=True)
def _isolate():
    signals.clear_subscribers()
    yield
    signals.clear_subscribers()


# ── GET /system/eval ────────────────────────────────────────────────────────

def test_system_eval_returns_scorecard():
    client, TS, cleanup = _client_with_db()
    try:
        s = TS()
        s.add(LumenAiEval(eval_id="r1:q1", run_id="r1", question_id="q1",
                          groundedness=1.0, correctness=0.9, hallucinated_ids=0,
                          latency_ms=5.0, prompt_version="v1", evaluated_at=NOW))
        s.add(LumenAiEval(eval_id="r1:q2", run_id="r1", question_id="q2",
                          groundedness=1.0, correctness=0.8, hallucinated_ids=0,
                          latency_ms=6.0, prompt_version="v1", evaluated_at=NOW))
        s.commit(); s.close()

        resp = client.get("/api/system/eval")
        assert resp.status_code == 200
        body = resp.json()
        assert body["run_id"] == "r1" and body["question_count"] == 2
        assert body["groundedness"] == 1.0
        # explicit run_id
        assert client.get("/api/system/eval?run_id=r1").json()["run_id"] == "r1"
    finally:
        cleanup()


def test_system_eval_empty_is_graceful():
    client, TS, cleanup = _client_with_db()
    try:
        resp = client.get("/api/system/eval")
        assert resp.status_code == 200
        assert resp.json()["question_count"] == 0
    finally:
        cleanup()


# ── GET /audit — Auditor only (§29.1 · §21) ────────────────────────────────

def _seed_roles(TS):
    s = TS()
    s.add(LumenUserRole(user_id="aud-1", role="auditor"))
    s.add(LumenUserRole(user_id="so-1", role="station_officer", unit_scope=[11]))
    s.add(LumenUserRole(user_id="sa-1", role="state_analyst"))
    # generate an audit row through the real engine (an allow)
    authorize(s, PolicyUser("so-1", "station_officer", unit_scope=[11]),
              "read_case_detail", Resource("case", "1", unit_id=11), now=NOW)
    s.commit(); s.close()


def test_auditor_can_read_audit_log():
    client, TS, cleanup = _client_with_db()
    try:
        _seed_roles(TS)
        resp = client.get("/api/audit?user_id=aud-1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1 and "entries" in body
        # the entry shape
        for e in body["entries"]:
            assert set(e) == {"audit_id", "user_id", "action", "resource",
                              "decision", "reason", "ip", "occurred_at"}
    finally:
        cleanup()


def test_non_auditor_is_denied_403():
    client, TS, cleanup = _client_with_db()
    try:
        _seed_roles(TS)
        for uid, role in (("so-1", "station_officer"), ("sa-1", "state_analyst")):
            resp = client.get(f"/api/audit?user_id={uid}")
            assert resp.status_code == 403
            assert "denied" in resp.json()["detail"].lower()
    finally:
        cleanup()


def test_denial_is_audited_and_emits_policy_denied():
    """Row-22 done-when: 'denials audited'."""
    client, TS, cleanup = _client_with_db()
    try:
        _seed_roles(TS)
        events = []
        signals.subscribe("PolicyDenied", lambda ev: events.append(ev))
        client.get("/api/audit?user_id=so-1")             # denied
        # the denial is persisted to lumen_audit …
        s = TS()
        denies = audit_repo.read(s, decision="deny", action="read_audit")
        assert len(denies) == 1
        assert denies[0].user_id == "so-1"
        s.close()
        # … and emitted on the bus
        assert len(events) == 1 and events[0].event_type == "PolicyDenied"
    finally:
        cleanup()


def test_unknown_user_denied():
    client, TS, cleanup = _client_with_db()
    try:
        _seed_roles(TS)
        resp = client.get("/api/audit?user_id=ghost")
        assert resp.status_code == 403
    finally:
        cleanup()


def test_audit_read_filters():
    client, TS, cleanup = _client_with_db()
    try:
        _seed_roles(TS)
        # a denial exists after a non-auditor probe
        client.get("/api/audit?user_id=so-1")
        allow = client.get("/api/audit?user_id=aud-1&decision=allow").json()
        deny = client.get("/api/audit?user_id=aud-1&decision=deny").json()
        assert all(e["decision"] == "allow" for e in allow["entries"])
        assert all(e["decision"] == "deny" for e in deny["entries"])
        # subject filter
        by_subject = client.get("/api/audit?user_id=aud-1&subject_user_id=so-1").json()
        assert all(e["user_id"] == "so-1" for e in by_subject["entries"])
    finally:
        cleanup()


def test_audit_requires_user_id():
    client, TS, cleanup = _client_with_db()
    try:
        resp = client.get("/api/audit")                   # missing required user_id
        assert resp.status_code == 422
    finally:
        cleanup()


# ── ABAC: k=5 suppression already exists (§4.3 r3) — reused, not rebuilt ────

def test_k_anonymity_suppression_is_reused():
    assert masking.K_ANONYMITY_THRESHOLD == 5
    assert masking.suppress_small_aggregate(5) == 5
    assert masking.suppress_small_aggregate(10) == 10
    assert masking.suppress_small_aggregate(4) == masking.SUPPRESSED_AGGREGATE_LABEL
    assert masking.suppress_small_aggregate(0) == "fewer than 5 — suppressed"


# ── endpoints registered / determinism ─────────────────────────────────────

def test_system_family_endpoints_registered():
    import main as app_main
    paths = app_main.app.openapi()["paths"]
    for p in ("/api/system/health", "/api/system/metrics",
              "/api/system/registry", "/api/system/eval", "/api/audit"):
        assert p in paths, f"{p} not registered"


def test_audit_read_is_deterministic():
    """The read is deterministically ordered over a fixed DB state. Note each
    call itself audits the auditor's allowed read (§21: every access audited),
    so read the store directly twice for a state-frozen comparison."""
    client, TS, cleanup = _client_with_db()
    try:
        _seed_roles(TS)
        client.get("/api/audit?user_id=aud-1")            # populate + freeze
        s = TS()
        rows_a = audit_repo.read(s)
        rows_b = audit_repo.read(s)
        s.close()
        # identical, stably-ordered sequence over the frozen state
        assert [r.audit_id for r in rows_a] == [r.audit_id for r in rows_b]
        # ordered by (occurred_at, audit_id) — the repository's contract
        ordered = sorted(rows_a, key=lambda r: (r.occurred_at, r.audit_id))
        assert [r.audit_id for r in rows_a] == [r.audit_id for r in ordered]
    finally:
        cleanup()
