"""
Session 17 — service registry (§22).

Covers: the §22 catalogue reproduced verbatim (9 services, capabilities,
dependencies), register/list/get/seed on lumen_service_registry, the read-only
catalogue over the existing lumen_model_registry and lumen_prompt_registry
(§22 "alongside"), the GET /system/registry endpoint returning all three,
determinism/idempotence, serialization, and edge cases.

Self-contained: in-memory SQLite, no live PostgreSQL.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.db.models.intelligence import LumenModelRegistry
from lumen.db.models.prompt import LumenPromptRegistry
from lumen.db.models.registry import LumenServiceRegistry
from lumen.registry import models as model_registry
from lumen.registry import prompts as prompt_registry
from lumen.registry import services as service_registry
from lumen.registry.services import CATALOGUE, ServiceSpec

NOW = datetime(2026, 7, 25, 0, 0, tzinfo=timezone.utc)


def _fresh():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


# ── §22 catalogue reproduced verbatim ──────────────────────────────────────

def test_catalogue_has_the_nine_services_verbatim():
    expected = {
        "identity": ("entity resolution", ("data store",)),
        "graph": ("projection + queries", ("data store", "identity")),
        "prediction": ("risk, anomaly, outcome", ("features", "data store")),
        "features": ("feature computation", ("data store", "graph")),
        "quality": ("rule evaluation", ("data store",)),
        "ai": ("orchestration", ("QuickML", "retrieval", "graph", "features", "KB")),
        "kb": ("corpus + retrieval", ("QuickML", "stratus")),
        "policy": ("authorisation", ("authentication",)),
        "bus": ("event publication", ("signals",)),
    }
    got = {s.name: (s.capability, s.depends_on) for s in CATALOGUE}
    assert got == expected
    assert len(CATALOGUE) == 9


# ── register / seed / lookup ────────────────────────────────────────────────

def test_seed_writes_the_catalogue():
    s = _fresh()
    n = service_registry.seed_service_registry(s)
    s.commit()
    assert n == 9
    rows = service_registry.list_services(s)
    assert [r.service_id for r in rows] == sorted(x.name for x in CATALOGUE)
    ai = service_registry.get_service(s, "ai")
    assert ai.capability == "orchestration"
    assert ai.depends_on == ["QuickML", "retrieval", "graph", "features", "KB"]
    assert ai.version == "v1"                          # disclosed default
    assert ai.health_state == "unknown"               # §24 probing deferred
    assert ai.last_check is None


def test_seed_is_idempotent_upsert():
    s = _fresh()
    service_registry.seed_service_registry(s)
    service_registry.seed_service_registry(s)
    s.commit()
    assert s.query(LumenServiceRegistry).count() == 9


def test_register_single_service_and_update():
    s = _fresh()
    spec = ServiceSpec("identity", "entity resolution", ("data store",), "lumen.identity")
    row = service_registry.register_service(s, spec, health_state="ok", last_check=NOW)
    assert row.health_state == "ok" and row.last_check == NOW
    # re-register updates in place, no duplicate
    service_registry.register_service(s, spec, health_state="degraded")
    assert s.query(LumenServiceRegistry).filter_by(service_id="identity").count() == 1
    assert service_registry.get_service(s, "identity").health_state == "degraded"


def test_get_unknown_service_returns_none():
    s = _fresh()
    assert service_registry.get_service(s, "nonesuch") is None


def test_list_is_ordered_deterministically():
    s = _fresh()
    service_registry.seed_service_registry(s)
    ids = [r.service_id for r in service_registry.list_services(s)]
    assert ids == sorted(ids)


# ── model / prompt registries: read-only catalogue of existing tables ──────

def test_model_registry_reads_existing_table():
    s = _fresh()
    s.add(LumenModelRegistry(model_id="graph_projection@v1", name="graph_projection",
                             kind="graph", version="v1", params={}, metrics={},
                             trained_at=NOW, active=True))
    s.flush()
    rows = model_registry.list_models(s)
    assert len(rows) == 1
    assert model_registry.get_model(s, "graph_projection@v1").name == "graph_projection"
    d = model_registry.as_dict(rows[0])
    assert d["model_id"] == "graph_projection@v1" and d["active"] is True


def test_prompt_registry_reads_existing_table():
    s = _fresh()
    s.add(LumenPromptRegistry(prompt_id="ask_summary@v1", name="ask_summary",
                              version="v1", template_hash="a" * 64,
                              created_at=NOW, active=True))
    s.flush()
    rows = prompt_registry.list_prompts(s)
    assert len(rows) == 1
    assert prompt_registry.get_prompt(s, "ask_summary@v1").version == "v1"
    assert prompt_registry.as_dict(rows[0])["template_hash"] == "a" * 64


def test_empty_model_and_prompt_registries():
    s = _fresh()
    assert model_registry.list_models(s) == []
    assert prompt_registry.list_prompts(s) == []


# ── serialization ───────────────────────────────────────────────────────────

def test_service_as_dict_shape():
    s = _fresh()
    service_registry.seed_service_registry(s)
    d = service_registry.as_dict(service_registry.get_service(s, "bus"))
    assert set(d) == {"service_id", "name", "capability", "version", "endpoint",
                      "depends_on", "health_state", "last_check"}
    assert d["depends_on"] == ["signals"]


# ── GET /system/registry (§22 · §29.1) ─────────────────────────────────────

def test_system_registry_endpoint():
    from fastapi.testclient import TestClient
    import main as app_main
    from lumen.db.session import get_db

    engine = create_engine("sqlite:///file:regmem?mode=memory&cache=shared&uri=true",
                           connect_args={"uri": True})
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    setup = TestingSession()
    service_registry.seed_service_registry(setup)
    setup.add(LumenModelRegistry(model_id="m@v1", name="m", kind="k", version="v1",
                                 params={}, metrics={}, trained_at=NOW, active=True))
    setup.add(LumenPromptRegistry(prompt_id="p@v1", name="p", version="v1",
                                  template_hash="b" * 64, created_at=NOW, active=True))
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
        resp = client.get("/api/system/registry")
        assert resp.status_code == 200
        body = resp.json()
        assert set(body) == {"services", "models", "prompts"}
        assert body["services"]["total"] == 9
        assert body["models"]["total"] == 1 and body["prompts"]["total"] == 1
        ai = next(x for x in body["services"]["items"] if x["service_id"] == "ai")
        assert ai["capability"] == "orchestration"
    finally:
        app_main.app.dependency_overrides.pop(get_db, None)


def test_endpoint_registered_in_app():
    import main as app_main
    assert "/api/system/registry" in app_main.app.openapi()["paths"]
