"""
Prediction surfaces — LUMEN_MASTER_SPEC_V3 §29.1, §13.

  GET /predictions/districts          — risk bands per district (§13 district_risk)
  GET /predictions/outcome/{case_id}  — outcome probability for one case
                                        (§13 case_outcome: P(cstype ∈ A/B/C))
  GET /anomalies                      — ranked anomaly Insights (§13 volume_anomaly)
  GET /recommendations                — §18 decision support, derived

§28 rule 1: the router reads precomputed tables and delegates the one live
computation (`case_outcome`) to `intelligence.outcome`, which owns it. §8
invariant 1 is respected — every score is returned inside its Insight.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from lumen.db.models import canonical as m
from lumen.db.models.intelligence import LumenInsight
from lumen.db.models.prediction import LumenDistrictRisk
from lumen.db.session import get_db

from lumen.api.routers.insights import serialize as serialize_insight

router = APIRouter(tags=["Predictions"])


@router.get("/predictions/districts")
def district_risk(db: Session = Depends(get_db)) -> dict:
    """§29.1 "Risk bands". The numeric score and its factors live in each
    district's risk Insight (§8 invariant 1), which is returned alongside."""
    names = {d.DistrictID: d.DistrictName for d in db.query(m.District).all()}
    rows = db.query(LumenDistrictRisk).all()
    insights = {
        i.subject_id: i
        for i in db.query(LumenInsight)
        .filter(LumenInsight.kind == "risk", LumenInsight.subject_type == "district")
        .all()
    }
    return {
        "districts": [
            {
                "district_id": str(r.district_id),
                "district_name": names.get(r.district_id, f"District {r.district_id}"),
                "band": (r.band or "low").lower(),
                "model_version": r.model_version,
                "insight": (
                    serialize_insight(insights[str(r.district_id)])
                    if str(r.district_id) in insights else None
                ),
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.get("/predictions/outcome/{case_id}")
def case_outcome(case_id: int, db: Session = Depends(get_db)) -> dict:
    """§13 case_outcome — P(cstype ∈ A/B/C) with factors, returned inside its
    Insight if the intelligence engine has persisted one for this case."""
    if db.get(m.CaseMaster, case_id) is None:
        raise HTTPException(status_code=404, detail="Case not found")
    row = (
        db.query(LumenInsight)
        .filter(
            LumenInsight.kind == "forecast",
            LumenInsight.subject_type == "case",
            LumenInsight.subject_id == str(case_id),
        )
        .order_by(LumenInsight.generated_at.desc())
        .first()
    )
    if row is None:
        # §32/§13: an outcome is only produced for cases the model scored. No
        # value is fabricated for a case the engine has not scored.
        return {"case_id": str(case_id), "insight": None}
    return {"case_id": str(case_id), "insight": serialize_insight(row)}


@router.get("/anomalies")
def anomalies(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    """§29.1 "Ranked anomalies" — the §13 volume-anomaly Insights, newest first."""
    q = db.query(LumenInsight).filter(LumenInsight.kind == "anomaly")
    total = q.count()
    rows = q.order_by(LumenInsight.generated_at.desc()).offset(offset).limit(limit).all()
    return {"anomalies": [serialize_insight(r) for r in rows], "total": total,
            "limit": limit, "offset": offset}


@router.get("/recommendations")
def recommendations(
    subject: str | None = Query(default=None, description="e.g. case:1000"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict:
    """§18 decision support. "Recommendations are `Insight(kind=
    "recommendation")` derived from existing insights — no new model."

    This surface therefore returns persisted recommendation-kind Insights. The
    §18 derivations that produce them belong to the intelligence engine (their
    generator is a precompute concern, not a request-path one — §14.5); when no
    recommendation has been generated the list is empty rather than invented.
    """
    q = db.query(LumenInsight).filter(LumenInsight.kind == "recommendation")
    if subject and ":" in subject:
        stype, _, sid = subject.partition(":")
        q = q.filter(LumenInsight.subject_type == stype, LumenInsight.subject_id == sid)
    total = q.count()
    rows = q.order_by(LumenInsight.generated_at.desc()).limit(limit).all()
    return {"recommendations": [serialize_insight(r) for r in rows], "total": total}
