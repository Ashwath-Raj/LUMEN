"""
Precompute orchestrator — LUMEN_MASTER_SPEC_V3 §26.1 row 20, §23.

§26.1 row 20 (Cron / Job Scheduling, T1): "jobs/precompute.py: resolution,
projection, metrics, hotspots, anomalies, quality." This is the batch pipeline
the scheduler runs off the request path (§23: "Batch jobs never run in the
request path").

§23 batch-queue rule: "Precompute stages are idempotent and checkpointed, so a
partial run resumes rather than restarts." Each stage delegates to an existing
job (consumed, never duplicated) and each of those is already idempotent
(clear-and-rewrite). This orchestrator adds the CHECKPOINT layer: a
`PrecomputeCheckpoint` records which stages completed; a resumed run skips
completed stages and continues from the first incomplete one.

Stage ORDER follows data dependency (§26.1 lists the stages but not an order;
disclosed): resolution (§6) → projection+metrics (§14) → quality (§5) →
predictions = hotspots+anomalies+risk+outcome (§13) → features (§12). Each
later stage reads the persisted output of earlier ones.

Scheduling itself is Catalyst Cron config (catalyst.json / deploy), not code;
§23: "heavy jobs staggered, never concurrent with the demo window." This
module is a plain deterministic callable — the local, testable pipeline; the
Cron trigger is wired at deployment (a later concern, disclosed). No external
scheduler, queue, or distributed execution.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from lumen.graph.projection import run_projection
from lumen.intelligence.engine import run_predictions
from lumen.jobs.feature_precompute import run_feature_precompute
from lumen.jobs.quality import run_quality_precompute
from lumen.jobs.resolve import run_resolution

logger = logging.getLogger("lumen")

# §26.1 row-20 stages, in data-dependency order (disclosed). Each name maps to
# one existing idempotent job.
STAGES: tuple[str, ...] = (
    "resolution",     # §6  — lumen_person / links
    "projection",     # §14 — graph edges + metrics ("projection, metrics")
    "quality",        # §5  — quality findings + scores
    "predictions",    # §13 — hotspots, anomalies, risk, outcome
    "features",       # §12 — feature store
)


@dataclass
class PrecomputeCheckpoint:
    """§23 checkpoint: which stages have completed. Passed into a run so a
    partial run resumes. §3.6 defines no checkpoint table, so the checkpoint is
    an in-memory/caller-held record (disclosed) — not a fabricated table."""
    completed: set[str] = field(default_factory=set)
    stage_summaries: dict[str, dict] = field(default_factory=dict)

    def is_done(self, stage: str) -> bool:
        return stage in self.completed

    def mark(self, stage: str, summary: dict) -> None:
        self.completed.add(stage)
        self.stage_summaries[stage] = summary

    @property
    def is_complete(self) -> bool:
        return set(STAGES).issubset(self.completed)


def _run_stage(session: Session, stage: str, now: datetime) -> dict:
    if stage == "resolution":
        return run_resolution(session, now=now)
    if stage == "projection":
        return run_projection(session, now=now)
    if stage == "quality":
        return run_quality_precompute(session, now=now)
    if stage == "predictions":
        return run_predictions(session, now=now)
    if stage == "features":
        return run_feature_precompute(session, now=now)
    raise ValueError(f"unknown precompute stage {stage!r}")


def run_precompute(session: Session, *, now: datetime | None = None,
                   checkpoint: PrecomputeCheckpoint | None = None,
                   stop_after: str | None = None) -> PrecomputeCheckpoint:
    """Run the §26.1-row-20 pipeline, staggered stage by stage. Idempotent and
    checkpointed (§23): a supplied `checkpoint` resumes — completed stages are
    skipped. `stop_after` runs up to and including a stage (used to simulate a
    partial run / a staggered window). Returns the updated checkpoint."""
    now = now or datetime.now(timezone.utc)
    checkpoint = checkpoint or PrecomputeCheckpoint()

    for stage in STAGES:
        if checkpoint.is_done(stage):
            logger.info("§26.1 precompute: skipping completed stage %s", stage)
            continue
        summary = _run_stage(session, stage, now)
        checkpoint.mark(stage, summary)
        logger.info("§26.1 precompute stage %s complete: %s", stage, summary)
        if stop_after is not None and stage == stop_after:
            break

    if checkpoint.is_complete:
        logger.info("§26.1 precompute complete: %s", checkpoint.stage_summaries)
    return checkpoint
