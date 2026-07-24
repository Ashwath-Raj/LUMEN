"""
Event store repository — LUMEN_MASTER_SPEC_V3 §21, §19.2.

§21: "`lumen_event` is append-only — no updates, no deletes, enforced in the
repository layer." This module is that enforcement point. It exposes exactly
three operations: append, get, and read (replay log queries). It offers NO
update or delete — the enforcement is structural (the methods do not exist),
and `assert_append_only` additionally guards against a caller mutating a
previously-persisted row within a session.

§19.2: "Every event lands in `lumen_event` (append-only) ... The store is the
replay log." Read helpers support "the source of the case lifecycle timeline
and the substrate for 'what changed since yesterday'" (§21) without
implementing those later surfaces.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from lumen.db.models.event import LumenEvent


class AppendOnlyViolation(Exception):
    """Raised on any attempt to mutate or delete a persisted lumen_event row."""


def append(session: Session, event_row: LumenEvent) -> LumenEvent:
    """Append one event. The only write path into the store."""
    if session.get(LumenEvent, event_row.event_id) is not None:
        raise AppendOnlyViolation(
            f"event_id {event_row.event_id!r} already exists; lumen_event is "
            "append-only (§21) — events are never rewritten."
        )
    session.add(event_row)
    session.flush()
    return event_row


def get(session: Session, event_id: str) -> LumenEvent | None:
    return session.get(LumenEvent, event_id)


def read(session: Session, *, event_type: str | None = None,
         subject_type: str | None = None, subject_id: str | None = None,
         since: datetime | None = None, limit: int | None = None) -> list[LumenEvent]:
    """Replay-log read (§21). Ordered by occurred_at then event_id for a
    stable, deterministic sequence."""
    q = session.query(LumenEvent)
    if event_type is not None:
        q = q.filter(LumenEvent.event_type == event_type)
    if subject_type is not None:
        q = q.filter(LumenEvent.subject_type == subject_type)
    if subject_id is not None:
        q = q.filter(LumenEvent.subject_id == subject_id)
    if since is not None:
        q = q.filter(LumenEvent.occurred_at >= since)
    q = q.order_by(LumenEvent.occurred_at, LumenEvent.event_id)
    if limit is not None:
        q = q.limit(limit)
    return q.all()


def assert_append_only(session: Session) -> None:
    """Guard callable in the flush path: raise if any already-persisted
    lumen_event row has pending modifications or deletions in this session.
    Makes the append-only rule enforceable in tests/CI, not just by omission
    of update/delete methods."""
    for obj in session.dirty:
        if isinstance(obj, LumenEvent) and sa_inspect(obj).persistent:
            raise AppendOnlyViolation(
                "lumen_event rows are immutable (§21): a persisted event was "
                "modified in this session."
            )
    for obj in session.deleted:
        if isinstance(obj, LumenEvent):
            raise AppendOnlyViolation(
                "lumen_event rows are never deleted (§21)."
            )
