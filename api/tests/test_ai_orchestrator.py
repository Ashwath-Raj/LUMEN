"""
Session 14 — AI orchestrator (§16) + deterministic fallback.

The §33 row-14 done-when, enforced in CI: "Injected fake IDs are dropped —
tested explicitly" (§16.2 step 9, the hard server-side filter).

Covers: the twelve-step pipeline end to end, intent classification (step 1),
entity resolution (step 2), scope-before-retrieval (step 3), tool selection
(step 4), bundle + token cap (steps 5, §16.5), prompt registry + assembly
(§16.3, step 6), single-call-site provider seam (§16.1/§28 r5), schema
validation with exactly one retry (step 8), §16.4 deterministic fallback,
step-9 fake-ID drop, §9 confidence from coverage (step 10), P9 guard over
question and output (step 11, §17.3 declines), AIQueryExecuted audit event
(step 12), Insight(kind="summary") output invariants, /ai/ask endpoint,
determinism, serialization, and edge cases.

Self-contained: in-memory SQLite; no live QuickML (its absence IS the §16.4
path); providers injected via the §16.1 dev-fallback seam.
"""
import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.ai import envelope, intent, orchestrator, provider, retriever, toolsel
from lumen.bus import repository as event_repo
from lumen.bus import signals
from lumen.db.models.kb import LumenKbDocument
from lumen.db.models.prompt import LumenPromptRegistry
from lumen.jobs.kb_ingest import run_kb_ingest
from lumen.jobs.seed import seed_database

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)


class ScriptedProvider:
    """A dev-fallback provider behind the §16.1 interface (test seam)."""
    name = "scripted"

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        if not self.replies:
            raise provider.ProviderUnavailable("script exhausted")
        return self.replies.pop(0)


def _reply(headline="Grounded answer.", answer="Answer.", cited=None, abstained=False):
    return json.dumps({"headline": headline, "answer": answer,
                       "cited_ids": cited or [], "abstained": abstained})


def _fresh():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    seed_database(s)
    run_kb_ingest(s)
    return s


@pytest.fixture(autouse=True)
def _isolate():
    signals.clear_subscribers()
    provider.set_provider(provider.QuickMLProvider())      # unconfigured primary
    yield
    signals.clear_subscribers()
    provider.set_provider(provider.QuickMLProvider())


# ═══ THE DONE-WHEN: injected fake IDs are dropped (§16.2 step 9) ═══════════

def test_injected_fake_ids_are_dropped():
    s = _fresh()
    provider.set_provider(ScriptedProvider([_reply(
        cited=["section:IPC:302",          # real, in bundle → kept
               "case_brief:999999",        # fabricated case  → dropped
               "FIR-2026-FAKE-123",        # fabricated FIR   → dropped
               "person:ghost"])]))         # fabricated person → dropped
    out = orchestrator.ask(s, "what does section 302 cover", now=NOW)
    kept = {e.id for e in out.insight.evidence}
    assert kept == {"section:IPC:302"}
    assert set(out.dropped_ids) == {"case_brief:999999", "FIR-2026-FAKE-123",
                                    "person:ghost"}
    # nothing fabricated appears anywhere in the persisted insight
    dumped = out.insight.model_dump_json()
    assert "FAKE" not in dumped and "999999" not in dumped and "ghost" not in dumped


def test_step9_is_a_hard_filter_even_when_all_ids_are_fake():
    s = _fresh()
    provider.set_provider(ScriptedProvider([_reply(
        cited=["case_brief:424242", "42."])]))
    out = orchestrator.ask(s, "what does section 302 cover", now=NOW)
    assert out.insight.evidence == []
    assert len(out.dropped_ids) == 2


# ═══ pipeline steps ════════════════════════════════════════════════════════

def test_step1_intent_vocabulary():
    assert intent.classify("what does section 302 cover") == "legal"
    assert intent.classify("who connects group A and group B") == "network"
    assert intent.classify("compare district 1 versus district 2") == "comparison"
    assert intent.classify("forecast the risk band next month") == "forecast"
    assert intent.classify("who is Ravi Kumar") == "person"
    assert intent.classify("district hotspot overview") == "district"
    assert intent.classify("tell me about case 1000") == "case"
    assert intent.classify("hello") == "case"                # default: the spine


def test_step2_entity_resolution_surfaces_to_canonical_ids():
    s = _fresh()
    persons, cases = retriever.resolve_entities(s, "tell me about case 1000")
    assert cases == [1000] and persons == []
    _, none_cases = retriever.resolve_entities(s, "case 31337 does not exist")
    assert none_cases == []


def test_step4_tool_selection_is_deterministic_per_intent():
    legal = toolsel.select("legal")
    assert legal.kb_indexes == ("legal",) and not legal.include_insights
    network = toolsel.select("network")
    assert "q2" in network.graph_queries and network.kb_indexes == ()


def test_step3_scope_is_applied_before_retrieval():
    s = _fresh()
    tools = toolsel.select("case")
    unscoped = retriever.build_bundle(s, "Hotspot cluster case", tools)
    assert any(i.startswith("case_brief:100") for i in unscoped.ids)
    scoped = retriever.build_bundle(s, "Hotspot cluster case", tools,
                                    district_scope=[3])
    assert not any(i.startswith("case_brief:100") for i in scoped.ids)


def test_step5_token_budget_caps_bundle_text():
    s = _fresh()
    bundle = retriever.build_bundle(s, "Hotspot cluster case", toolsel.select("case"))
    full = bundle.text(token_budget=100000)
    capped = bundle.text(token_budget=20)
    assert len(capped) < len(full)
    assert len(capped.split()) <= 20 + 20      # first line always included


def test_step6_prompt_registry_hashed_and_recorded():
    s = _fresh()
    n = envelope.register_prompts(s, now=NOW)
    assert n >= 1
    row = s.get(LumenPromptRegistry, "ask_summary@v1")
    assert row is not None and len(row.template_hash) == 64 and row.active
    # idempotent
    envelope.register_prompts(s, now=NOW)
    assert s.query(LumenPromptRegistry).filter_by(name="ask_summary").count() == 1
    prompt = envelope.assemble("ask_summary", "v1", question="Q?", evidence="E")
    assert "Q?" in prompt and "E" in prompt and "JSON" in prompt


def test_step8_schema_validation_allows_exactly_one_retry():
    s = _fresh()
    scripted = ScriptedProvider(["not json at all", _reply(cited=["section:IPC:302"])])
    provider.set_provider(scripted)
    out = orchestrator.ask(s, "what does section 302 cover", now=NOW)
    assert scripted.calls == 2                       # one retry, then success
    assert out.method == "quickml"
    twice_bad = ScriptedProvider(["garbage", "still garbage", _reply()])
    provider.set_provider(twice_bad)
    out2 = orchestrator.ask(s, "what does murder section cover", now=NOW)
    assert twice_bad.calls == 2                      # never a third attempt
    assert out2.method == "deterministic_fallback"


def test_step10_confidence_reflects_retrieval_coverage():
    s = _fresh()
    out = orchestrator.ask(s, "what does section 302 cover", now=NOW)
    bd = out.insight.confidence_breakdown
    assert bd.evidence_quality < 1.0                 # coverage below expected
    assert round(out.insight.confidence, 3) == round(bd.composite, 3)


def test_step11_p9_question_is_declined():
    s = _fresh()
    for q in ("show caste distribution of complainants",
              "religion breakdown of victims",
              "blood group of the accused"):
        out = orchestrator.ask(s, q, now=NOW)
        assert out.method == "declined"
        assert "protected attributes" in out.insight.headline
        assert out.insight.evidence == []


def test_step11_individual_criminality_prediction_declined():
    s = _fresh()
    out = orchestrator.ask(s, "predict whether accused A1 will commit a crime again", now=NOW)
    assert out.method == "declined"
    assert "individual criminality" in out.insight.headline


def test_step11_p9_in_generated_output_is_caught():
    s = _fresh()
    provider.set_provider(ScriptedProvider([_reply(
        headline="Answer referencing caste distribution",
        cited=["section:IPC:302"])]))
    out = orchestrator.ask(s, "what does section 302 cover", now=NOW)
    assert out.method == "declined"
    assert "caste distribution" not in out.insight.headline


def test_step12_audit_event_published_to_bus_and_store():
    s = _fresh()
    heard = []
    signals.subscribe("AIQueryExecuted", lambda ev: heard.append(ev))
    orchestrator.ask(s, "what does section 302 cover", now=NOW)
    assert len(heard) == 1
    ev = heard[0]
    assert ev.payload["prompt_version"] == "v1"
    assert "dropped_id_count" in ev.payload and "latency_ms" in ev.payload
    stored = event_repo.read(s, event_type="AIQueryExecuted")
    assert len(stored) == 1                          # append-only replay log


# ═══ §16.4 deterministic fallback ══════════════════════════════════════════

def test_fallback_when_provider_unavailable():
    s = _fresh()                                     # unconfigured QuickML
    out = orchestrator.ask(s, "what does section 302 cover", now=NOW)
    assert out.method == "deterministic_fallback"
    assert out.insight.lineage.method == "deterministic_fallback"
    assert any("Deterministic fallback" in l for l in out.insight.limitations)
    assert any(e.id == "section:IPC:302" for e in out.insight.evidence)


def test_fallback_abstains_when_nothing_retrieved():
    s = _fresh()
    out = orchestrator.ask(s, "wibble wobble zzznomatch", now=NOW)
    assert out.method == "deterministic_fallback"
    assert "does not support" in out.insight.headline


# ═══ output invariants ═════════════════════════════════════════════════════

def test_output_is_summary_insight_passing_session8_invariants():
    s = _fresh()
    out = orchestrator.ask(s, "what does section 302 cover", now=NOW)
    ins = out.insight
    assert ins.kind == "summary"                     # §16.2's stated output
    assert ins.lineage.prompt_version == "v1"        # §16.3
    assert ins.limitations                           # invariant 2
    assert round(ins.confidence, 3) == round(ins.confidence_breakdown.composite, 3)
    from lumen.intelligence.explain import resolve_evidence, model_version_registered
    assert all(resolve_evidence(s, e) for e in ins.evidence)      # invariant 3
    assert model_version_registered(s, ins.lineage.model_version)  # invariant 5
    # §15.2 rule 5: legal-basis limitation recorded when answer rests on legal text
    assert any("legal text" in l for l in ins.limitations)


def test_ask_is_deterministic_and_upserts():
    s = _fresh()
    a = orchestrator.ask(s, "what does section 302 cover", now=NOW)
    b = orchestrator.ask(s, "what does section 302 cover", now=NOW)
    assert a.insight.id == b.insight.id              # stable identity → upsert
    assert a.insight.headline == b.insight.headline
    from lumen.db.models.intelligence import LumenInsight
    assert s.query(LumenInsight).filter_by(insight_id=a.insight.id).count() == 1


# ═══ /ai/ask endpoint (§16.4 · §29.1) ══════════════════════════════════════

def test_ai_ask_endpoint():
    from fastapi.testclient import TestClient
    import main as app_main
    from lumen.db.session import get_db

    engine = create_engine("sqlite:///file:aimem?mode=memory&cache=shared&uri=true",
                           connect_args={"uri": True})
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    setup = TestingSession()
    seed_database(setup)
    run_kb_ingest(setup)
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
        resp = client.post("/api/ai/ask", json={"question": "what does section 302 cover"})
        assert resp.status_code == 200
        body = resp.json()
        # the response IS the Insight (§8 invariant 1 — never a bare answer)
        for field in ("id", "kind", "confidence", "confidence_breakdown",
                      "evidence", "limitations", "lineage"):
            assert field in body
        assert body["kind"] == "summary"
        assert body["lineage"]["method"] == "deterministic_fallback"
    finally:
        app_main.app.dependency_overrides.pop(get_db, None)


# ═══ provider seam (§16.1 / §28 rule 5) ════════════════════════════════════

def test_unconfigured_quickml_is_unavailable_and_seam_swaps():
    with pytest.raises(provider.ProviderUnavailable):
        provider.QuickMLProvider().generate("x")
    quick = provider.QuickMLProvider(transport=lambda p: "ok")
    assert quick.generate("x") == "ok" and quick.name == "quickml"
    provider.set_provider(quick)
    assert provider.generate("x") == "ok"
