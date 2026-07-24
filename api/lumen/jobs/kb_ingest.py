"""
Knowledge base ingestion job — LUMEN_MASTER_SPEC_V3 §15.2 rule 4.

"Ingestion is a job: chunk → embed via QuickML → store refs in
lumen_kb_chunk. Re-ingest on Act/Section change."

Runs the §15.1 corpus collection (kb/ingest.py) over the canonical tables and
persists documents + chunks. Checksums make it re-entrant: an unchanged
document is skipped; a changed Act/Section (or brief) is re-chunked — the
rule-4 re-ingest trigger, exercised simply by re-running this job after the
change. The QuickML embedding step is deferred at the Session 13/14 boundary
(embedding_ref stays NULL).
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from lumen.kb.ingest import DEFAULT_MAX_CHARS, collect_corpus, ingest_document

logger = logging.getLogger("lumen")


def run_kb_ingest(session: Session, *, max_chars: int = DEFAULT_MAX_CHARS) -> dict:
    """Ingest the full canonical corpus. Returns counts for the caller/logs."""
    written = 0
    unchanged = 0
    by_kind: dict[str, int] = {}
    for doc in collect_corpus(session):
        if ingest_document(session, doc, max_chars=max_chars):
            written += 1
        else:
            unchanged += 1
        by_kind[doc.kind] = by_kind.get(doc.kind, 0) + 1
    session.commit()
    summary = {"written": written, "unchanged": unchanged, **by_kind}
    logger.info("§15 KB ingest complete: %s", summary)
    return summary
