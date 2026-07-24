"""
Audit repository — LUMEN_MASTER_SPEC_V3 §21, §4.2.

`lumen_audit` is immutable (§4.2: "Immutable, readable only by Auditor"; §21:
who read/ran/exported/was-denied). This repository is the write + read seam,
enforcing append-only in the repository layer — the same discipline
`bus/repository.py` gives `lumen_event`. It exposes append and read only; no
update, no delete. `assert_append_only` guards a flush against mutation of a
persisted row, so immutability is testable in CI, not merely by omission.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from lumen.db.models.policy import LumenAudit


class AuditAppendOnlyViolation(Exception):
    """Raised on any attempt to mutate or delete a persisted lumen_audit row."""


def append(session: Session, row: LumenAudit) -> LumenAudit:
    if session.get(LumenAudit, row.audit_id) is not None:
        raise AuditAppendOnlyViolation(
            f"audit_id {row.audit_id!r} already exists; lumen_audit is "
            "append-only (§21/§4.2)."
        )
    session.add(row)
    session.flush()
    return row


def read(session: Session, *, user_id: str | None = None,
         decision: str | None = None, action: str | None = None,
         limit: int | None = None) -> list[LumenAudit]:
    """Replay/audit read. Ordered by occurred_at then audit_id — deterministic."""
    q = session.query(LumenAudit)
    if user_id is not None:
        q = q.filter(LumenAudit.user_id == user_id)
    if decision is not None:
        q = q.filter(LumenAudit.decision == decision)
    if action is not None:
        q = q.filter(LumenAudit.action == action)
    q = q.order_by(LumenAudit.occurred_at, LumenAudit.audit_id)
    if limit is not None:
        q = q.limit(limit)
    return q.all()


def assert_append_only(session: Session) -> None:
    for obj in session.dirty:
        if isinstance(obj, LumenAudit) and sa_inspect(obj).persistent:
            raise AuditAppendOnlyViolation(
                "lumen_audit rows are immutable (§4.2): a persisted audit row "
                "was modified in this session."
            )
    for obj in session.deleted:
        if isinstance(obj, LumenAudit):
            raise AuditAppendOnlyViolation("lumen_audit rows are never deleted (§21).")
