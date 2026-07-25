"""
Insight surface — LUMEN_MASTER_SPEC_V3 §29.1, §8, §10, §17.5.

  GET  /insights                    — the §8 Insight feed (filterable, §29.2 paged)
  GET  /insights/{id}/lineage       — the §8 Lineage panel payload
  POST /insights/{id}/approve       — §10 lifecycle approval (District SP /
                                      State Analyst); records approver +
                                      timestamp and emits `InsightApproved`
  POST /insights/{id}/feedback      — §17.5 officer feedback: thumbs up/down
                                      plus optional reason, written to
                                      `lumen_event` as `InsightFeedbackGiven`

§28 rule 1 keeps the router thin — lifecycle transitions go through
`intelligence.lifecycle` (the one owner of §10), and events are appended through
the §19 bus repository. Nothing is computed here.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from lumen.bus import repository as bus_repo
from lumen.db.models.event import LumenEvent
from lumen.db.models.intelligence import LumenInsight
from lumen.db.session import get_db
from lumen.intelligence import lifecycle
from lumen.intelligence.lifecycle import VerificationFailedError
from lumen.policy import roles as policy_roles

router = APIRouter(prefix="/insights", tags=["Insights"])

# §10: "A District SP or State Analyst approves (T2)."
_APPROVER_ROLES = {"district_sp", "state_analyst"}


def serialize(r: LumenInsight) -> dict:
    """A `lumen_insight` row as the §8 Insight JSON — the same shape
    `/ai/ask` returns and the UI's frozen contract type expects."""
    return {
        "id": r.insight_id,
        "contract_version": r.contract_version or "v1",
        "kind": r.kind,
        "subject_type": r.subject_type,
        "subject_id": r.subject_id,
        "headline": r.headline,
        "score": r.score,
        "confidence": r.confidence if r.confidence is not None else 0.0,
        "confidence_breakdown": r.confidence_components or {
            "evidence_quality": 1.0, "model_confidence": 1.0, "data_completeness": 1.0,
            "identity_confidence": 1.0, "graph_confidence": 1.0,
            "composite": r.confidence if r.confidence is not None else 0.0,
        },
        "factors": r.factors or [],
        "counterfactuals": r.counterfactuals or [],
        "evidence": r.evidence or [],
        "limitations": r.limitations or ["Limitations were not recorded for this insight."],
        "lineage": r.lineage or {
            "method": "unknown", "model_version": "unknown", "prompt_version": None,
            "features_used": [], "query_ids": [], "source_row_count": 0,
            "quality_score": 0.0,
            "computed_at": r.generated_at.isoformat() if r.generated_at else "",
        },
        "lifecycle_state": r.lifecycle_state or "generated",
        "classification": "CONFIDENTIAL",
        "generated_at": r.generated_at.isoformat() if r.generated_at else "",
        "expires_at": r.expires_at.isoformat() if r.expires_at else None,
        "approved_by": r.approved_by,
        "approved_at": r.approved_at.isoformat() if r.approved_at else None,
    }


@router.get("")
def list_insights(
    kind: str | None = Query(default=None),
    subject_type: str | None = None,
    subject_id: str | None = None,
    lifecycle_state: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    q = db.query(LumenInsight)
    if kind:
        q = q.filter(LumenInsight.kind == kind)
    if subject_type:
        q = q.filter(LumenInsight.subject_type == subject_type)
    if subject_id:
        q = q.filter(LumenInsight.subject_id == subject_id)
    if lifecycle_state:
        q = q.filter(LumenInsight.lifecycle_state == lifecycle_state)
    total = q.count()
    rows = q.order_by(LumenInsight.generated_at.desc()).offset(offset).limit(limit).all()
    return {"insights": [serialize(r) for r in rows], "total": total,
            "limit": limit, "offset": offset}


@router.get("/{insight_id}/lineage")
def get_lineage(insight_id: str, db: Session = Depends(get_db)) -> dict:
    """§29.1 lineage panel — the §8 Lineage of one insight."""
    row = db.get(LumenInsight, insight_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Insight not found")
    return {
        "insight_id": row.insight_id,
        "lineage": row.lineage or {},
        "lifecycle_state": row.lifecycle_state,
        "approved_by": row.approved_by,
        "approved_at": row.approved_at.isoformat() if row.approved_at else None,
    }


class ApproveRequest(BaseModel):
    """§10: approval is recorded with approver and timestamp."""
    approver: str
    role: str


@router.post("/{insight_id}/approve")
def approve_insight(insight_id: str, body: ApproveRequest,
                    db: Session = Depends(get_db)) -> dict:
    """§10 lifecycle approval. Only a District SP or State Analyst may approve;
    any other role is refused with SCOPE_DENIED semantics (403). The transition
    itself is owned by `intelligence.lifecycle` (§10 never skips `verified`)."""
    row = db.get(LumenInsight, insight_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Insight not found")
    if body.role not in _APPROVER_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Outside your role scope: §10 approval requires District SP "
                   "or State Analyst. Access is logged.",
        )

    # §3.6 carries no classification column; §4.2's register says a
    # `lumen_insight` "inherits the classification of its subject", and §8
    # invariant 6 re-validates it against the evidence — so it is supplied here.
    try:
        insight = lifecycle.load_insight(db, insight_id, classification="CONFIDENTIAL")
    except KeyError:
        raise HTTPException(status_code=404, detail="Insight not found")
    # §10: an insight never skips `verified`, and `verify_insight` enforces the
    # entry checks — including the confidence floor. A refusal here is the
    # specification working, not a fault, so it is reported as a 409 with the
    # reason rather than surfacing as an internal error.
    try:
        if insight.lifecycle_state == "generated":
            insight = lifecycle.to_verified(db, insight)
        approved = lifecycle.to_approved(db, insight, approver=body.approver)
    except VerificationFailedError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:                       # illegal §10 transition
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    db.commit()
    return {"insight_id": approved.id, "lifecycle_state": approved.lifecycle_state,
            "approved_by": body.approver}


class FeedbackRequest(BaseModel):
    """§17.5: "Thumbs up/down plus optional reason on every AI insight." """
    rating: Literal["up", "down"]
    reason: str | None = None
    actor_id: str = "user"


@router.post("/{insight_id}/feedback")
def submit_feedback(insight_id: str, body: FeedbackRequest,
                    db: Session = Depends(get_db)) -> dict:
    """§17.5 officer feedback — written to `lumen_event` as
    `InsightFeedbackGiven` (the §19.2 catalogue's own event type)."""
    row = db.get(LumenInsight, insight_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Insight not found")

    now = datetime.now(timezone.utc)
    event = LumenEvent(
        event_id=str(uuid.uuid4()),
        event_type="InsightFeedbackGiven",
        event_version="v1",
        actor_id=body.actor_id,
        subject_type="insight",
        subject_id=insight_id,
        payload={"rating": body.rating, "reason": body.reason},
        trace_id=str(uuid.uuid4()),
        occurred_at=now,
    )
    bus_repo.append(db, event)
    db.commit()
    return {"event_id": event.event_id, "insight_id": insight_id,
            "rating": body.rating, "recorded_at": now.isoformat()}


# Re-exported so other §29.1 routers serialise insights identically.
__all__ = ["router", "serialize", "policy_roles"]
