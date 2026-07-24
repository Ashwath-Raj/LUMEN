"""
Session 23 — Catalyst T2 accelerators (§26.1 rows 14, 15, 16, 24, 25).

§33 row-23 done-when: "Each demonstrable or dropped — no half-wired services."
Every accelerator is a swappable backend with a local deterministic default
(demonstrable now) and a Catalyst client that slots in at deploy. This suite
proves: the SmartBrowz briefing dossier (insights, timeline, evidence,
§4.3-rule-5 watermark) + swappable renderer + POST /cases/{id}/briefing;
Mail + Push local outboxes + backend swap; Zia OCR/voice HONEST stubs
(available=False — never fabricated, §26.3 honesty rule) + backend swap;
determinism; and edge cases.

Consumes existing data (case/insights/timeline); duplicates no business logic.
Self-contained: in-memory SQLite, no live Catalyst services.
"""
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.db.models import canonical as m
from lumen.db.models import intelligence  # noqa: F401 — register lumen_insight
from lumen.db.models.intelligence import LumenInsight
from lumen.accelerators import briefing, notify, zia
from lumen.jobs.seed import seed_database

NOW = datetime(2026, 7, 25, 0, 0, tzinfo=timezone.utc)


def _fresh():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


@pytest.fixture(autouse=True)
def _reset_backends():
    """Each test starts with the local backends; swaps are undone after."""
    briefing.set_renderer(briefing.LocalBriefingRenderer())
    notify.set_mail_backend(notify.LocalMailBackend())
    notify.set_push_backend(notify.LocalPushBackend())
    zia.set_ocr_backend(zia.LocalOcrBackend())
    zia.set_voice_backend(zia.LocalVoiceBackend())
    yield
    briefing.set_renderer(briefing.LocalBriefingRenderer())
    notify.set_mail_backend(notify.LocalMailBackend())
    notify.set_push_backend(notify.LocalPushBackend())
    zia.set_ocr_backend(zia.LocalOcrBackend())
    zia.set_voice_backend(zia.LocalVoiceBackend())


# ── SmartBrowz briefing (#16) ──────────────────────────────────────────────

def test_briefing_dossier_contents():
    s = _fresh()
    seed_database(s)
    dossier = briefing.assemble_dossier(s, 5000, requesting_user="officer-1", now=NOW)
    assert dossier.case_id == "5000"
    assert dossier.crime_no is not None
    # §32 g5 lifecycle case 5000: incident → info → registered → arrest → chargesheet
    events = [t["event"] for t in dossier.timeline]
    assert {"incident", "info_received", "registered", "arrest", "chargesheet"} <= set(events)
    # timeline is date-ordered
    ats = [t["at"] for t in dossier.timeline]
    assert ats == sorted(ats)
    assert dossier.evidence and dossier.evidence[0]["entity"] == "case"


def test_briefing_watermark_per_section_4_3():
    s = _fresh()
    seed_database(s)
    dossier = briefing.assemble_dossier(s, 5000, requesting_user="sp-rao", now=NOW)
    wm = dossier.watermark
    assert wm["requesting_user"] == "sp-rao"                  # §4.3 rule 5
    assert wm["generated_at"] == NOW.isoformat()
    assert "sp-rao" in wm["text"] and NOW.isoformat() in wm["text"]


def test_briefing_includes_case_insights():
    s = _fresh()
    seed_database(s)
    s.add(LumenInsight(insight_id="ins-1", kind="risk", subject_type="case",
                       subject_id="5000", headline="Elevated risk.", confidence=0.7,
                       lifecycle_state="generated"))
    s.flush()
    dossier = briefing.assemble_dossier(s, 5000, requesting_user="o", now=NOW)
    assert any(i["insight_id"] == "ins-1" for i in dossier.insights)


def test_briefing_render_deterministic_stratus_url():
    s = _fresh()
    seed_database(s)
    a = briefing.generate_briefing(s, 5000, requesting_user="o", now=NOW)
    b = briefing.generate_briefing(s, 5000, requesting_user="o", now=NOW)
    assert a["stratus_url"] == b["stratus_url"]               # deterministic
    assert a["stratus_url"].startswith("stratus://briefings/5000/")
    assert a["renderer"] == "local"


def test_briefing_renderer_is_swappable():
    """The SmartBrowz+Stratus client slots in behind the same interface."""
    s = _fresh()
    seed_database(s)

    class SmartBrowzStub:
        name = "smartbrowz"
        def render(self, dossier):
            return briefing.RenderedBriefing(
                stratus_url=f"stratus://real/{dossier.case_id}.pdf",
                content_type="application/pdf", byte_size=4096)

    briefing.set_renderer(SmartBrowzStub())
    out = briefing.generate_briefing(s, 5000, requesting_user="o", now=NOW)
    assert out["renderer"] == "smartbrowz"
    assert out["content_type"] == "application/pdf"
    assert out["stratus_url"] == "stratus://real/5000.pdf"


def test_briefing_missing_case_raises():
    s = _fresh()
    seed_database(s)
    with pytest.raises(KeyError):
        briefing.assemble_dossier(s, 999999, requesting_user="o", now=NOW)


# ── POST /cases/{id}/briefing endpoint (§29.1) ─────────────────────────────

def test_briefing_endpoint():
    from fastapi.testclient import TestClient
    import main as app_main
    from lumen.db.session import get_db

    engine = create_engine("sqlite:///file:brief?mode=memory&cache=shared&uri=true",
                           connect_args={"uri": True})
    Base.metadata.create_all(engine)
    keepalive = engine.connect()
    TS = sessionmaker(bind=engine)
    setup = TS(); seed_database(setup); setup.commit(); setup.close()

    def override():
        db = TS()
        try:
            yield db
        finally:
            db.close()

    app_main.app.dependency_overrides[get_db] = override
    try:
        client = TestClient(app_main.app)
        resp = client.post("/api/cases/5000/briefing",
                           json={"requesting_user": "officer-1"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["case_id"] == "5000"
        assert body["stratus_url"].startswith("stratus://")
        assert body["watermark"]["requesting_user"] == "officer-1"
        assert "timeline" in body["dossier"]
        # unknown case → 404
        assert client.post("/api/cases/999999/briefing",
                           json={"requesting_user": "o"}).status_code == 404
    finally:
        app_main.app.dependency_overrides.pop(get_db, None)
        keepalive.close()


# ── Mail (#24) + Push (#25) ────────────────────────────────────────────────

def test_mail_records_to_outbox():
    msg = notify.send_mail(recipient="sp@district1", subject="Anomaly alert",
                           body="District-week spike detected.", now=NOW)
    assert msg.channel == "mail" and msg.recipient == "sp@district1"
    assert msg.sent_at == NOW.isoformat()
    assert notify.active_mail_backend().outbox[-1] == msg


def test_push_records_to_outbox():
    msg = notify.send_push(recipient="device-token-9", subject="High-risk alert",
                           body="Immediate attention.", now=NOW)
    assert msg.channel == "push"
    assert notify.active_push_backend().outbox[-1] == msg


def test_mail_backend_swappable():
    class CatalystMail:
        name = "catalyst-mail"
        def __init__(self): self.calls = []
        def send(self, *, recipient, subject, body, sent_at):
            self.calls.append(recipient)
            return notify.Message("mail", recipient, subject, body, sent_at)
    cm = CatalystMail()
    notify.set_mail_backend(cm)
    notify.send_mail(recipient="x@y", subject="s", body="b", now=NOW)
    assert cm.calls == ["x@y"]
    assert notify.active_mail_backend().name == "catalyst-mail"


def test_push_backend_swappable():
    class CatalystPush:
        name = "catalyst-push"
        def __init__(self): self.calls = []
        def send(self, *, recipient, subject, body, sent_at):
            self.calls.append(recipient)
            return notify.Message("push", recipient, subject, body, sent_at)
    cp = CatalystPush()
    notify.set_push_backend(cp)
    notify.send_push(recipient="dev-1", subject="s", body="b", now=NOW)
    assert cp.calls == ["dev-1"]


# ── Zia OCR (#14) + voice (#15): honest stubs, never fabricated ────────────

def test_ocr_local_is_honest_unavailable():
    """§26.3 honesty rule: the local stub does not fabricate OCR text."""
    result = zia.ocr_extract("scan://fir-123.pdf")
    assert result.available is False
    assert result.text is None
    assert result.engine == "local_stub"


def test_voice_stt_and_translation_local_unavailable():
    stt = zia.speech_to_text("audio://clip.wav")
    assert stt.available is False and stt.text is None
    tr = zia.translate_kn_en("ಕನ್ನಡ ಪಠ್ಯ")
    assert tr.available is False and tr.text is None
    assert tr.source_language == "kn" and tr.target_language == "en"


def test_ocr_backend_swappable_returns_available():
    class ZiaOcr:
        name = "zia"
        def extract_text(self, document_ref):
            return zia.OcrResult(text="FIR No 123 ...", engine="zia", available=True)
    zia.set_ocr_backend(ZiaOcr())
    result = zia.ocr_extract("scan://fir-123.pdf")
    assert result.available is True and result.text == "FIR No 123 ..."


def test_voice_backend_swappable():
    class ZiaVoice:
        name = "zia"
        def speech_to_text(self, audio_ref):
            return zia.VoiceResult(text="transcribed", engine="zia", available=True)
        def translate(self, text, *, source, target):
            return zia.VoiceResult(text="translated", engine="zia", available=True,
                                   source_language=source, target_language=target)
    zia.set_voice_backend(ZiaVoice())
    assert zia.speech_to_text("a").text == "transcribed"
    assert zia.translate_kn_en("x").text == "translated"


# ── determinism ─────────────────────────────────────────────────────────────

def test_accelerators_are_deterministic():
    s = _fresh()
    seed_database(s)
    def snap():
        d = briefing.assemble_dossier(s, 5000, requesting_user="o", now=NOW)
        return (d.as_dict(), zia.ocr_extract("x").available,
                zia.translate_kn_en("y").target_language)
    assert snap() == snap()
