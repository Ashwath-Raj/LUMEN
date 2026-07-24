"""
Quality surface router — LUMEN_MASTER_SPEC_V3 §5.3 item 2 and §29.1
(`GET /quality/scores` · `/quality/findings`).

Reads the precomputed `lumen_quality_score` / `lumen_quality_finding` rows
(written by `jobs/quality.py`, §5.2 "on every precompute run") and returns
them. No detection happens in the request path — §5.2/§14.5 keep analytics
out of request handlers; the surface reads precomputed tables.

Response shape matches the plain-dict style of the only other live router
(`health.py`); this session introduces two NEW endpoints and changes no
existing contract (§29.2: contracts are additive only).

Note: the two OTHER §5.3 surfacing paths — `Insight(kind="data_quality")`
(§5.3 item 1) and quality-scores-feeding-confidence (§5.3 item 3) — depend
on the Insight engine (§8) and confidence model (§9), which are Session 8,
and are deliberately NOT implemented here.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from lumen.db.session import get_db
from lumen.db.models.quality import LumenQualityFinding, LumenQualityScore

router = APIRouter(prefix="/quality", tags=["Quality"])


@router.get("/scores")
def get_quality_scores(
    scope_type: str | None = Query(default=None, description="state | district | unit"),
    db: Session = Depends(get_db),
) -> dict:
    q = db.query(LumenQualityScore)
    if scope_type is not None:
        q = q.filter(LumenQualityScore.scope_type == scope_type)
    rows = q.all()
    return {
        "total": len(rows),
        "scores": [
            {
                "scope_type": r.scope_type,
                "scope_id": r.scope_id,
                "dimension": r.dimension,
                "score": r.score,
                "computed_at": r.computed_at.isoformat() if r.computed_at else None,
            }
            for r in rows
        ],
    }


@router.get("/findings")
def get_quality_findings(
    rule_id: str | None = Query(default=None, description="Q01..Q18"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    q = db.query(LumenQualityFinding)
    if rule_id is not None:
        q = q.filter(LumenQualityFinding.rule_id == rule_id)
    total = q.count()
    rows = q.order_by(LumenQualityFinding.finding_id).offset(offset).limit(limit).all()
    return {
        "total": total,
        "findings": [
            {
                "finding_id": r.finding_id,
                "rule_id": r.rule_id,
                "severity": r.severity,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "detail": r.detail,
                "detected_at": r.detected_at.isoformat() if r.detected_at else None,
                "state": r.state,
            }
            for r in rows
        ],
    }
