"""
Person (identity) surface router — LUMEN_MASTER_SPEC_V3 §6.4, §29.1.

§29.1 lists three person routes; the two owned by Session 7 (entity
resolution, §6) are implemented here:

  GET  /persons/{id}          — "Dossier with resolution evidence" (§29.1)
  POST /persons/{id}/dispute  — "Report an incorrect identity match" (§29.1)

The third, `GET /persons/{id}/network` (ego graph), is the §14 graph
subsystem (Session 9) and is deliberately NOT implemented here — building it
would require the graph module Session 7 must not touch.

A `GET /persons` list is added so resolved identities are enumerable; §29.2
requires every list endpoint to return `total` and accept `limit`/`offset`,
which it does. These are NEW endpoints; no existing contract changes (§29.2
additive-only).

§6.4 presentation rules honoured by these responses:
  - Confidence and a "see why" disclosure (the `match_features` per link) on
    every resolved identity.
  - Links below 0.85 render as *candidate matches*, returned under a separate
    `candidates` key, never mixed into `linked`.
  - Language is "person associated with N case records" — never "criminal",
    "offender", or "guilty".
  - A "report incorrect match" control → POST /dispute writes
    `lumen_person_dispute`. §6.4 also requires emitting `PersonMatchDisputed`;
    that event is emitted once the intelligence bus (§19) lands in Session 12
    — the bus module is a placeholder now, so the dispute is durably recorded
    here and the emission is wired in that later session. Human-in-the-loop is
    already visible: the dispute is persisted and surfaced.

Reads the precomputed `lumen_person` / `lumen_person_link` tables (written by
`jobs/resolve.py`); no resolution happens in the request path (§14.5 keeps
analytics out of request handlers).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from lumen.db.session import get_db
from lumen.db.models.identity import LumenPerson, LumenPersonLink, LumenPersonDispute
from lumen.identity.pipeline import LINK_STATE_CANDIDATE, LINK_STATE_LINKED

router = APIRouter(prefix="/persons", tags=["Persons"])


def _associated_phrase(case_count: int | None) -> str:
    """§6.4 language rule — never 'criminal'/'offender'/'guilty'."""
    n = case_count or 0
    return f"person associated with {n} case record{'s' if n != 1 else ''}"


def _link_dict(link: LumenPersonLink) -> dict:
    return {
        "accused_master_id": link.accused_master_id,
        "confidence": link.confidence,
        "match_features": link.match_features,   # §6.4 "see why"
        "state": link.state,
    }


@router.get("")
def list_persons(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    q = db.query(LumenPerson).order_by(LumenPerson.person_id)
    total = q.count()
    rows = q.offset(offset).limit(limit).all()
    return {
        "total": total,
        "persons": [
            {
                "person_id": p.person_id,
                "canonical_name": p.canonical_name,
                "description": _associated_phrase(p.case_count),
                "case_count": p.case_count,
                "district_count": p.district_count,
                "resolution_confidence": p.resolution_confidence,  # always present (P10)
                "method_version": p.method_version,
            }
            for p in rows
        ],
    }


@router.get("/{person_id}")
def get_person(person_id: str, db: Session = Depends(get_db)) -> dict:
    """Dossier with resolution evidence (§29.1 / §6.4)."""
    person = db.get(LumenPerson, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    links = db.query(LumenPersonLink).filter(LumenPersonLink.person_id == person_id).all()
    linked = [_link_dict(l) for l in links if l.state == LINK_STATE_LINKED]
    candidates = [_link_dict(l) for l in links if l.state == LINK_STATE_CANDIDATE]

    return {
        "person_id": person.person_id,
        "canonical_name": person.canonical_name,
        "description": _associated_phrase(person.case_count),  # §6.4 language rule
        "case_count": person.case_count,
        "district_count": person.district_count,
        "resolution_confidence": person.resolution_confidence,  # P10 — always shown
        "method_version": person.method_version,
        "first_seen": person.first_seen.isoformat() if person.first_seen else None,
        "last_seen": person.last_seen.isoformat() if person.last_seen else None,
        # §6.4: auto-linked members carry their "see why" match features …
        "linked": linked,
        # … and candidate (0.65–0.85) matches are returned separately, never
        # mixed in, so the UI can visually separate and exclude from centrality.
        "candidates": candidates,
    }


class DisputeRequest(BaseModel):
    accused_master_id: int
    raised_by: str
    reason: str | None = None


@router.post("/{person_id}/dispute")
def dispute_person_match(
    person_id: str,
    body: DisputeRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Report an incorrect identity match (§29.1 / §6.4). Writes
    `lumen_person_dispute`; `PersonMatchDisputed` is emitted when the §19 bus
    lands (Session 12)."""
    person = db.get(LumenPerson, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    dispute = LumenPersonDispute(
        person_id=person_id,
        accused_master_id=body.accused_master_id,
        raised_by=body.raised_by,
        reason=body.reason,
        raised_at=datetime.now(timezone.utc),
        resolution=None,   # open until adjudicated (§6.4 human-in-the-loop)
    )
    db.add(dispute)
    db.commit()
    db.refresh(dispute)

    return {
        "dispute_id": dispute.dispute_id,
        "person_id": dispute.person_id,
        "accused_master_id": dispute.accused_master_id,
        "raised_by": dispute.raised_by,
        "reason": dispute.reason,
        "raised_at": dispute.raised_at.isoformat() if dispute.raised_at else None,
        "resolution": dispute.resolution,
        "state": "open",
    }
