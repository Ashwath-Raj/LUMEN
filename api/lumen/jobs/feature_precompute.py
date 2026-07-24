"""
Feature precompute job — LUMEN_MASTER_SPEC_V3 §12.

"One table, one loader, versioned." This job is the batch step that computes
every §12 feature (`intelligence/features.compute_all`) and writes them to
`lumen_feature` (`persist_features`). Models and prompts then READ the table —
they never recompute (§12).

Idempotent per version: a re-run clears the version's rows and rewrites them
(§12's versioning is the invalidation mechanism — a fresh run replaces the
prior computation for that version). Consumes upstream that must already be
built: resolution (§6, lumen_person_link), graph metrics (§14,
lumen_person_metrics / lumen_community), quality (§5, lumen_quality_score),
and the canonical tables. It computes nothing those subsystems own — it reads
their outputs (§12: "never recompute").

Scheduling: §23 / §26.1 stage the precompute on Catalyst Cron; that runtime is
a later concern. This job is a plain callable — the full staggered cron
orchestrator (jobs/precompute.py) remains a placeholder for that session.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from lumen.intelligence.features import (
    FEATURE_VERSION, compute_all, persist_features,
)

logger = logging.getLogger("lumen")


def run_feature_precompute(session: Session, *, version: str = FEATURE_VERSION,
                           now: datetime | None = None) -> dict:
    """Compute + persist all §12 features. Returns a small summary."""
    now = now or datetime.now(timezone.utc)
    features = compute_all(session)
    written = persist_features(session, features, version=version, now=now)
    session.commit()

    by_type: dict[str, int] = {}
    by_name: dict[str, int] = {}
    for f in features:
        by_type[f.entity_type] = by_type.get(f.entity_type, 0) + 1
        by_name[f.feature_name] = by_name.get(f.feature_name, 0) + 1
    summary = {"written": written, "version": version,
               "by_type": by_type, "feature_kinds": len(by_name)}
    logger.info("§12 feature precompute complete: %s", summary)
    return summary
