"""
Session 25 — demo hardening (§32, §34).

The §33 row-25 done-when: "Full script runs twice with no reload, and once with
QuickML disabled." This suite is the durable CI artifact for that: it verifies
the deterministic seed and every recorded DEMO_SCRIPT.md id, that each §34 demo
step has backing data/API, that the degraded path (QuickML disabled) yields the
deterministic fallback + L3, and that error/empty states are graceful.

This is a HARDENING/VERIFICATION session — it introduces no new APIs, tables,
or subsystems; it exercises the ones already built. Self-contained: in-memory
SQLite, no live PostgreSQL / QuickML.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base, get_db
from lumen.db.models import (  # noqa: F401 — register every table
    canonical as m, event, eval as _eval, feature, graph, identity,
    intelligence, kb, policy, prediction, prompt, quality, registry,
)
from lumen.db.models.graph import LumenGraphEdge
from lumen.db.models.identity import LumenPerson
from lumen.db.models.intelligence import LumenInsight
from lumen.db.models.policy import LumenUserRole
from lumen.db.models.prediction import LumenDistrictRisk, LumenHotspot
from lumen.db.models.quality import LumenQualityFinding, LumenQualityScore
from lumen.ai import orchestrator, provider
from lumen.bus import signals
from lumen.governance.masking import mask_accused_name
from lumen.jobs.kb_ingest import run_kb_ingest
from lumen.jobs.precompute import run_precompute
from lumen.jobs.seed import seed_database
from lumen.resilience import breaker, degradation

NOW = datetime(2026, 7, 25, 0, 0, tzinfo=timezone.utc)


def _fresh():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


@pytest.fixture(autouse=True)
def _isolate():
    signals.clear_subscribers()
    provider.set_provider(provider.QuickMLProvider())      # QuickML absent
    yield
    signals.clear_subscribers()
    provider.set_provider(provider.QuickMLProvider())


# ── §32 seed: determinism + every recorded DEMO_SCRIPT.md id exists ─────────

def test_seed_is_deterministic():
    def manifest():
        s = _fresh()
        return seed_database(s).as_dict()
    assert manifest() == manifest()


def test_demo_script_recorded_ids_all_exist():
    """Every entity id recorded in docs/DEMO_SCRIPT.md exists in a fresh seed."""
    s = _fresh()
    man = seed_database(s)
    # g1 hotspot cases 1000-1009, district 1
    assert all(s.get(m.CaseMaster, c) for c in range(1000, 1010))
    assert man.hotspot_district_id == 1
    # g2 community accused ids + broker
    assert all(s.get(m.Accused, a) for a in
               [2001, 2002, 2003, 2004, 2101, 2102, 2103, 2104,
                2201, 2202, 2211, 2212])
    assert man.community_broker_label == "P-BROKER"
    # g3 name-variant accused
    assert all(s.get(m.Accused, a) for a in range(3000, 3009))
    # g4 signature pair
    assert s.get(m.CaseMaster, 4000) and s.get(m.CaseMaster, 4001)
    # g5 lifecycle case 5000 + 278d delay + arrest + chargesheet
    assert s.get(m.CaseMaster, 5000) and man.lifecycle_charge_delay_days == 278
    assert s.get(m.ArrestSurrender, 5000) and s.get(m.ChargesheetDetails, 5000)
    # g6 spike district 2, week 2026-06-01
    assert man.spike_district_id == 2 and man.spike_week_start == "2026-06-01"
    # g8 crimeno/unit mismatch case 8000
    c8 = s.get(m.CaseMaster, 8000)
    assert man.crimeno_unit_mismatch_case_id == 8000
    assert c8.CrimeNo == "100010012202600800" and c8.PoliceStationID == 11
    # g9 missing coords 9000 + impossible timestamp 9001
    c9 = s.get(m.CaseMaster, 9000)
    assert c9.latitude is None and c9.longitude is None
    assert man.impossible_timestamp_case_id == 9001
    # g11 low-conf candidate 11001/11002, intended 0.70
    assert s.get(m.Accused, 11001) and s.get(m.Accused, 11002)
    assert man.low_confidence_candidate.get("intended_confidence") == 0.70
    # g12 masking-divergent cases 12000-12004
    assert all(s.get(m.CaseMaster, c) for c in range(12000, 12005))


# ── §34 demo path: every step has backing data/API after full precompute ──

@pytest.fixture()
def demo():
    s = _fresh()
    seed_database(s)
    run_kb_ingest(s)
    run_precompute(s, now=NOW)      # resolution, projection, quality, predictions, features
    return s


def test_demo_step1_command_center_backing(demo):
    assert demo.query(LumenDistrictRisk).count() > 0            # risk bands
    assert demo.query(LumenQualityScore).count() > 0            # statewide quality


def test_demo_step2_geo_hotspots(demo):
    assert demo.query(LumenHotspot).count() > 0                 # DBSCAN clusters


def test_demo_step3_case_workspace(demo):
    assert demo.get(m.CaseMaster, 1000) is not None            # hotspot case aggregate


def test_demo_step4_crimeno_mismatch_flagged(demo):
    q04 = demo.query(LumenQualityFinding).filter_by(rule_id="Q04").count()
    assert q04 >= 1                                             # the seeded Q04 catch


def test_demo_step5_resolution_ran(demo):
    assert demo.query(LumenPerson).count() > 0                  # name-variant persons


def test_demo_step6_risk_insight_explainable(demo):
    ins = demo.query(LumenInsight).filter_by(kind="risk").first()
    assert ins is not None
    assert ins.factors and ins.confidence_components            # factors + confidence breakdown


def test_demo_step7_network_q2_intermediary(demo):
    from lumen.graph.queries import q2_hidden_intermediary
    r = q2_hidden_intermediary(demo, ["accused:2001"], ["accused:2101"], now=NOW)
    assert r.insight is not None and r.insight.limitations      # insight + limitations line
    assert r.graph is not None                                 # never a bare graph


def test_demo_step8_intelligence_console_ask(demo):
    out = orchestrator.ask(demo, "what does section 302 cover", now=NOW)
    assert out.insight.kind == "summary"
    assert out.insight.lineage.prompt_version == "v1"           # versioned prompt (§16.3)
    # step 9 hard filter: nothing cited outside the bundle
    assert all(c in out.bundle_ids for c in out.cited_ids)


def test_demo_step9_role_masking(demo):
    assert mask_accused_name("Real Name", "station_officer") != "Real Name"
    assert mask_accused_name("Real Name", "district_sp") == "Real Name"


def test_demo_step10_live_insert_event(demo):
    from lumen.contracts.event import EventContract, Subject
    from lumen.bus.repository import read as event_read
    signals.publish(demo, EventContract(
        event_id="ev-demo", event_type="CaseRegistered", occurred_at=NOW,
        actor_id="system", subject=Subject(type="case", id="99999"),
        payload={}, trace_id="t", classification="CONFIDENTIAL"))
    assert len(event_read(demo, event_type="CaseRegistered")) >= 1


def test_demo_step12_catalyst_registry(demo):
    from lumen.registry.services import list_services, seed_service_registry
    seed_service_registry(demo)
    assert len(list_services(demo)) == 9


# ── §34 step 11 / §24.2: degraded-path rehearsal (QuickML disabled) ────────

def test_degraded_ai_ask_is_deterministic_fallback(demo):
    provider.set_provider(provider.QuickMLProvider())          # unconfigured → unavailable
    out = orchestrator.ask(demo, "what does section 302 cover", now=NOW)
    assert out.method == "deterministic_fallback"
    assert out.insight.lineage.method == "deterministic_fallback"
    assert any("Deterministic fallback" in l for l in out.insight.limitations)
    assert out.insight.kind == "summary"                       # still returns an insight


def test_degraded_level_is_l3_with_banner():
    level = degradation.resolve_level({"quickml_llm"})
    assert level == degradation.Level.L3
    assert degradation.level_label(level) == "L3 — DETERMINISTIC"
    rep = degradation.health_report({"quickml_llm": lambda: False})
    assert rep["degradation_level"] == 3
    q = next(d for d in rep["dependencies"] if d["dependency"] == "quickml_llm")
    assert "evidence-based summary" in q["user_sees"]           # §24.1 banner text


def test_degraded_breaker_opens_at_three_failures():
    c = breaker.CircuitBreaker("quickml", lambda: 0.0)
    for _ in range(3):
        c.record_failure()
    assert c.state() is breaker.BreakerState.OPEN               # §24.3 rule 2


def test_rest_of_platform_functions_with_quickml_down(demo):
    """Graph, predictions, quality all answer with the LLM disabled."""
    from lumen.graph.queries import q2_hidden_intermediary
    r = q2_hidden_intermediary(demo, ["accused:2001"], ["accused:2101"], now=NOW)
    assert r.insight is not None
    assert demo.query(LumenDistrictRisk).count() > 0
    assert demo.query(LumenQualityScore).count() > 0


# ── error / empty states: graceful, never a bare 500 (§29.3) ───────────────

def _client():
    """A TestClient over one shared in-memory SQLite connection (StaticPool),
    which the TestClient's worker thread reuses — avoiding SQLite's
    cross-thread close error on teardown."""
    import main as app_main
    from sqlalchemy.pool import StaticPool

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TS = sessionmaker(bind=engine)
    setup = TS()
    seed_database(setup)
    run_kb_ingest(setup)
    setup.add(LumenUserRole(user_id="so-1", role="station_officer", unit_scope=[11]))
    setup.commit()
    setup.close()

    def override():
        db = TS()
        try:
            yield db
        finally:
            db.close()

    from fastapi.testclient import TestClient
    app_main.app.dependency_overrides[get_db] = override
    client = TestClient(app_main.app, raise_server_exceptions=False)

    def cleanup():
        app_main.app.dependency_overrides.pop(get_db, None)
        engine.dispose()

    return client, cleanup


def test_error_states_are_graceful():
    client, cleanup = _client()
    try:
        # unknown entities → 404, never 500
        assert client.post("/api/cases/999999/briefing",
                           json={"requesting_user": "o"}).status_code == 404
        assert client.get("/api/persons/does-not-exist").status_code == 404
        # denied audit access → 403, denial recorded, not a crash
        assert client.get("/api/audit?user_id=so-1").status_code == 403
        assert client.get("/api/audit?user_id=ghost").status_code == 403
        # malformed input → 422 validation, not 500
        assert client.get("/api/audit").status_code == 422
        assert client.post("/api/ai/ask", json={}).status_code == 422
        assert client.post("/api/cases/5000/briefing", json={}).status_code == 422
    finally:
        cleanup()


def test_empty_states_are_graceful():
    client, cleanup = _client()
    try:
        # empty/quiet surfaces → 200 with an empty-but-valid body, never a crash
        for path in ("/api/quality/scores", "/api/quality/findings?rule_id=Q99",
                     "/api/system/health", "/api/system/metrics",
                     "/api/system/eval", "/api/system/registry"):
            resp = client.get(path)
            assert resp.status_code == 200, f"{path} -> {resp.status_code}"
            body = str(resp.json())
            assert "Traceback" not in body and "at 0x" not in body
        # a no-match AI question returns a graceful abstaining insight, not 500
        r = client.post("/api/ai/ask", json={"question": "zzznomatch wibble"})
        assert r.status_code == 200
    finally:
        cleanup()


# ── the done-when: the demo path is repeatable (twice, no reload) ──────────

def test_demo_path_repeatable_twice():
    """§33 row-25 done-when — 'runs twice with no reload': the full precompute +
    demo-critical reads produce identical results on a second run over the same
    session (idempotent), the deterministic analogue of a no-reload re-run."""
    s = _fresh()
    seed_database(s)
    run_kb_ingest(s)

    def snapshot():
        run_precompute(s, now=NOW)
        return (s.query(LumenGraphEdge).count(),
                s.query(LumenDistrictRisk).count(),
                s.query(LumenHotspot).count(),
                s.query(LumenPerson).count())
    first = snapshot()
    second = snapshot()                                        # "no reload" re-run
    assert first == second and all(v > 0 for v in first)
