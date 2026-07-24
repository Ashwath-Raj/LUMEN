"""
`make eval` entry point — LUMEN_MASTER_SPEC_V3 §17.4.

"make eval runs the suite ... writes lumen_ai_eval, prints a scorecard."

Per the confirmed scope decision, the suite runs IN-PROCESS against the
Session-14 orchestrator over a freshly-seeded in-memory database (the §32
deterministic seed + §15 KB ingest), not over HTTP against a deployed API —
no deployment exists in this environment, and the QuickML-absent path is
§16.4's deterministic fallback, which is exactly what a network-free demo
runs on. The scorecard printed here is the §33 row-15 done-when.

Usage:  python -m scripts.eval        (from api/, inside the venv)
        make eval                      (from repo root)
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

_API_DIR = Path(__file__).resolve().parents[1]
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
# register every table on the metadata
from lumen.db.models import canonical, identity, quality, intelligence  # noqa: F401
from lumen.db.models import graph, prediction, event, kb, prompt, eval as _eval  # noqa: F401
from lumen.ai.eval.runner import format_scorecard, run_eval
from lumen.jobs.kb_ingest import run_kb_ingest
from lumen.jobs.seed import seed_database


def main() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)          # eval harness only — NOT app startup
    session = sessionmaker(bind=engine)()
    seed_database(session)
    run_kb_ingest(session)

    # run_id / timestamp are fixed here so a manual run is reproducible; a real
    # deployment would stamp wall-clock values.
    run_id = "eval-local"
    scorecard = run_eval(session, run_id=run_id,
                         now=datetime(2026, 7, 25, 0, 0, tzinfo=timezone.utc))
    print(format_scorecard(scorecard))


if __name__ == "__main__":
    main()
