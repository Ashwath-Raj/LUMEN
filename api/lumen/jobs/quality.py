"""
Quality precompute batch job — LUMEN_MASTER_SPEC_V3 §5.2.

Runs the §5.1 rule engine, computes the §5.2 six-dimension scores, and
writes both to the `lumen_` platform tables (§3.6):
`lumen_quality_finding` (one row per finding) and `lumen_quality_score`
(one row per scope+dimension). §5.2: "Written to lumen_quality_score on
every precompute run."

The job is re-runnable: each run clears the two quality tables first, so a
second run reflects the current data rather than appending duplicates. It
does not touch any canonical (§3.5) table — quality is an analytical
overlay (§4.3 rule 1: "LUMEN never deletes canonical records").
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from lumen.db.models.quality import LumenQualityFinding, LumenQualityScore
from lumen.quality.engine import evaluate
from lumen.quality.scoring import compute_scores

logger = logging.getLogger("lumen")

# §5.3 item 2 frames findings as an administrative product; a fresh finding
# starts in an "open" state (its lifecycle beyond that is not defined by §5).
INITIAL_FINDING_STATE = "open"


def run_quality_precompute(session: Session, *, now: datetime | None = None) -> dict:
    """Evaluate rules + scores and persist them. Returns a small summary
    (counts) for logging / the batch caller."""
    now = now or datetime.now(timezone.utc)

    # Clear prior run (quality tables only — never canonical).
    session.query(LumenQualityFinding).delete()
    session.query(LumenQualityScore).delete()
    session.flush()

    result = evaluate(session)
    for f in result.findings:
        session.add(
            LumenQualityFinding(
                rule_id=f.rule_id,
                severity=f.severity,
                entity_type=f.entity_type,
                entity_id=f.entity_id,
                detail=f.detail,
                detected_at=now,
                state=INITIAL_FINDING_STATE,
            )
        )

    scores = compute_scores(result)
    for s in scores:
        session.add(
            LumenQualityScore(
                scope_type=s.scope_type,
                scope_id=s.scope_id,
                dimension=s.dimension,
                score=s.score,
                computed_at=now,
            )
        )

    session.commit()
    summary = {"findings": len(result.findings), "scores": len(scores)}
    logger.info("§5 quality precompute complete: %s", summary)
    return summary
