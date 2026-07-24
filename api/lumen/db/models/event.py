"""
Event store table — LUMEN_MASTER_SPEC_V3 §3.6, §19.2, §21.

`lumen_event`, defined verbatim from §3.6's DDL:

    lumen_event(event_id UUID PK, event_type, event_version, actor_id,
                subject_type, subject_id, payload JSON, trace_id, occurred_at)

Nine columns. Note the intentional shape difference from §19.1's contract:
the table flattens the contract's nested `subject{type,id}` to
`subject_type`/`subject_id`, and has NO `classification` column (the contract
carries one; the table row is itself classified INTERNAL by §4.2). The
mapping is applied in bus/signals.py; both shapes are represented exactly as
the spec writes them.

§21 / §19.2: `lumen_event` is APPEND-ONLY — "no updates, no deletes, enforced
in the repository layer." The repository (`lumen/bus/repository.py`) is that
enforcement point; this model declares no UPDATE/DELETE behaviour of its own.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, JSON, String

from lumen.db.session import Base


class LumenEvent(Base):
    __tablename__ = "lumen_event"

    event_id = Column(String(36), primary_key=True)      # UUID (§3.6)
    event_type = Column(String(40))
    event_version = Column(String(10))
    actor_id = Column(String(60))
    subject_type = Column(String(20))
    subject_id = Column(String(60))
    payload = Column(JSON)
    trace_id = Column(String(36))
    occurred_at = Column(DateTime)
