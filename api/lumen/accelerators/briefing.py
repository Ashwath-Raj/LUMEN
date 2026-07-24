"""
SmartBrowz — Case Intelligence Briefing — LUMEN_MASTER_SPEC_V3 §26.1 row 16,
§29.1 (`POST /cases/{id}/briefing`), §4.3 rule 5.

§26.1 #16: "SmartBrowz — Case Intelligence Briefing PDF — dossier with
insights, network figure, timeline, evidence, watermarked per §4.3." §29.1:
"POST /cases/{id}/briefing — SmartBrowz PDF → Stratus URL (T2)."

This module: (1) assembles the dossier PAYLOAD from existing persisted data
(the case, its insights, a lifecycle timeline, evidence chips — consumed, not
recomputed), watermarked per §4.3 rule 5 ("watermarked with the requesting
user and timestamp"); (2) renders it to a PDF via a swappable
`BriefingRenderer` backend and stores it, returning a Stratus URL.

The renderer + storage are external (SmartBrowz headless browser + Stratus).
Locally there is neither, so `LocalBriefingRenderer` produces a deterministic
artifact — the dossier payload serialised, with a deterministic stub Stratus
key — so the briefing is demonstrable now (§33 row-23 "demonstrable"), never
half-wired. A `SmartBrowzRenderer` (real headless-browser PDF → Stratus
upload) slots in at deployment via `set_renderer`, no caller changing.

Cannot determine from the specification (recorded in the deliverables):
  * the PDF template / layout — §26.1 lists the dossier CONTENTS, not a format.
  * the "network figure" rendering — a graph image is a UI/render concern; the
    payload carries the case's network subject ids, not a rendered figure.
  * the Stratus key/URL scheme — a deterministic local stub is used.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Protocol

from sqlalchemy.orm import Session

from lumen.db.models import canonical as m
from lumen.db.models.intelligence import LumenInsight


# ── §4.3 rule 5 watermark ──────────────────────────────────────────────────

@dataclass(frozen=True)
class Watermark:
    """§4.3 rule 5: 'watermarked with the requesting user and timestamp.'"""
    requesting_user: str
    generated_at: str      # iso8601

    def as_text(self) -> str:
        return f"LUMEN briefing · {self.requesting_user} · {self.generated_at}"


# ── dossier payload (assembled from persisted data) ────────────────────────

@dataclass
class BriefingDossier:
    case_id: str
    crime_no: str | None
    registered: str | None
    brief_facts: str | None
    insights: list[dict] = field(default_factory=list)     # §8 insights on the case
    timeline: list[dict] = field(default_factory=list)     # lifecycle events, to scale
    evidence: list[dict] = field(default_factory=list)     # clickable chips
    network_subject_ids: list[str] = field(default_factory=list)
    watermark: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "case_id": self.case_id, "crime_no": self.crime_no,
            "registered": self.registered, "brief_facts": self.brief_facts,
            "insights": self.insights, "timeline": self.timeline,
            "evidence": self.evidence,
            "network_subject_ids": self.network_subject_ids,
            "watermark": self.watermark,
        }


def _timeline(session: Session, case: m.CaseMaster) -> list[dict]:
    """The case lifecycle events in date order (incident → info → registered →
    arrest → chargesheet). Reads canonical dates; no recomputation."""
    events: list[tuple] = []

    def add(kind: str, when):
        if when is not None:
            iso = when.isoformat() if hasattr(when, "isoformat") else str(when)
            events.append((iso, kind))

    add("incident", case.IncidentFromDate)
    add("info_received", case.InfoReceivedPSDate)
    add("registered", case.CrimeRegisteredDate)
    for ar in (session.query(m.ArrestSurrender)
               .filter(m.ArrestSurrender.CaseMasterID == case.CaseMasterID)):
        add("arrest", ar.ArrestSurrenderDate)
    for cs in (session.query(m.ChargesheetDetails)
               .filter(m.ChargesheetDetails.CaseMasterID == case.CaseMasterID)):
        add("chargesheet", cs.csdate)
    events.sort(key=lambda e: (e[0], e[1]))
    return [{"at": at, "event": kind} for at, kind in events]


def assemble_dossier(session: Session, case_id: int, *,
                     requesting_user: str,
                     now: datetime | None = None) -> BriefingDossier:
    """§26.1 #16 dossier: insights, timeline, evidence — for one case,
    watermarked per §4.3 rule 5."""
    now = now or datetime.now(timezone.utc)
    case = session.get(m.CaseMaster, case_id)
    if case is None:
        raise KeyError(f"case {case_id} not found")

    insights = (session.query(LumenInsight)
                .filter(LumenInsight.subject_type == "case",
                        LumenInsight.subject_id == str(case_id))
                .order_by(LumenInsight.insight_id).all())
    insight_dicts = [{"insight_id": i.insight_id, "kind": i.kind,
                      "headline": i.headline, "confidence": i.confidence}
                     for i in insights]
    # evidence chips = the case itself + its insight evidence
    evidence = [{"entity": "case", "id": str(case_id),
                 "url": f"/cases/{case_id}"}]
    # persons associated (accused) — network subjects for the "network figure"
    network_ids = [str(a.AccusedMasterID) for a in
                   session.query(m.Accused)
                   .filter(m.Accused.CaseMasterID == case_id)
                   .order_by(m.Accused.AccusedMasterID)]

    wm = Watermark(requesting_user=requesting_user, generated_at=now.isoformat())
    return BriefingDossier(
        case_id=str(case_id),
        crime_no=case.CrimeNo,
        registered=case.CrimeRegisteredDate.isoformat() if case.CrimeRegisteredDate else None,
        brief_facts=case.BriefFacts,
        insights=insight_dicts,
        timeline=_timeline(session, case),
        evidence=evidence,
        network_subject_ids=network_ids,
        watermark={"text": wm.as_text(), "requesting_user": wm.requesting_user,
                   "generated_at": wm.generated_at},
    )


# ── swappable renderer (SmartBrowz PDF → Stratus) ──────────────────────────

@dataclass(frozen=True)
class RenderedBriefing:
    stratus_url: str
    content_type: str
    byte_size: int


class BriefingRenderer(Protocol):
    name: str

    def render(self, dossier: BriefingDossier) -> RenderedBriefing: ...


class LocalBriefingRenderer:
    """The local deterministic backend. Serialises the dossier and produces a
    deterministic stub Stratus URL — demonstrable without SmartBrowz/Stratus.
    The stub key is a stable hash of (case_id, watermark) so re-rendering the
    same dossier yields the same URL."""

    name = "local"
    content_type = "application/json"      # PDF is the SmartBrowz backend's job

    def render(self, dossier: BriefingDossier) -> RenderedBriefing:
        import hashlib
        import json
        payload = json.dumps(dossier.as_dict(), sort_keys=True)
        key = hashlib.sha256(
            f"{dossier.case_id}:{dossier.watermark.get('generated_at','')}"
            .encode("utf-8")).hexdigest()[:16]
        return RenderedBriefing(
            stratus_url=f"stratus://briefings/{dossier.case_id}/{key}",
            content_type=self.content_type,
            byte_size=len(payload.encode("utf-8")))


_renderer: BriefingRenderer = LocalBriefingRenderer()


def set_renderer(renderer: BriefingRenderer) -> None:
    """Swap the renderer (the SmartBrowz+Stratus client at deploy; the test
    seam locally)."""
    global _renderer
    _renderer = renderer


def active_renderer() -> BriefingRenderer:
    return _renderer


def generate_briefing(session: Session, case_id: int, *, requesting_user: str,
                      now: datetime | None = None) -> dict:
    """§29.1 POST /cases/{id}/briefing: assemble the dossier, render via the
    active backend, return the Stratus URL + dossier summary."""
    dossier = assemble_dossier(session, case_id, requesting_user=requesting_user,
                               now=now)
    rendered = _renderer.render(dossier)
    return {
        "case_id": dossier.case_id,
        "stratus_url": rendered.stratus_url,
        "content_type": rendered.content_type,
        "byte_size": rendered.byte_size,
        "renderer": _renderer.name,
        "watermark": dossier.watermark,
        "dossier": dossier.as_dict(),
    }
