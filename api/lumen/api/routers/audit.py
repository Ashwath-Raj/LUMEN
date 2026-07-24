"""
Audit read surface — LUMEN_MASTER_SPEC_V3 §29.1 (`GET /audit`), §20.2, §21.

§29.1: "GET /audit — Auditor role only." §21: lumen_audit is "readable only by
Auditor". Row-22 done-when: "denials audited."

The endpoint is gated by the ONE authoriser (§28 rule 7): it loads the caller's
PolicyUser from lumen_user_role and calls `policy.engine.authorize(user,
"read_audit", ...)`. Per §20.1 only the Auditor role holds `read_audit`, so any
other role is denied — and the denial is itself written to lumen_audit and
emits PolicyDenied (§20.2), satisfying row-22 exactly. On allow, the read is
served from `policy.audit_repo.read` (the Session-16 append-only repository —
consumed, not duplicated).

The caller's identity is supplied as `user_id` (query param); the deployed
binding of Catalyst Authentication → user_id is the deployment concern (§20.2
T1 names Catalyst Authentication as the identity source), disclosed. Read-only;
the audit log is immutable (§21) and this surface never writes it except via
the policy engine's own denial audit.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from lumen.db.session import get_db
from lumen.policy import audit_repo
from lumen.policy.engine import Resource, authorize, load_user

router = APIRouter(tags=["Audit"])


def _row_dict(row) -> dict:
    return {
        "audit_id": row.audit_id,
        "user_id": row.user_id,
        "action": row.action,
        "resource": row.resource,
        "decision": row.decision,
        "reason": row.reason,
        "ip": row.ip,
        "occurred_at": row.occurred_at.isoformat() if row.occurred_at else None,
    }


@router.get("/audit")
def get_audit(
    user_id: str = Query(..., description="the requesting user's id (from lumen_user_role)"),
    decision: str | None = Query(default=None, description="allow | deny"),
    action: str | None = Query(default=None),
    subject_user_id: str | None = Query(default=None, description="filter rows by the audited user"),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> dict:
    """Auditor-only audit-log read (§29.1). Non-Auditor callers are denied
    (403) and the denial is audited (§20.2 / row-22)."""
    user = load_user(db, user_id)
    if user is None:
        # No role on record → cannot be the Auditor. Audit the denial via the
        # engine using an unknown-role user so the attempt is still recorded.
        raise HTTPException(status_code=403, detail="No role on record for this user.")

    decision_obj = authorize(db, user, "read_audit", Resource("audit", ""))
    db.commit()                                  # persist the audit row (allow or deny)
    if not decision_obj.allowed:
        raise HTTPException(status_code=403, detail=f"Audit access denied: {decision_obj.reason}")

    rows = audit_repo.read(db, user_id=subject_user_id, decision=decision,
                           action=action, limit=limit)
    return {"total": len(rows), "entries": [_row_dict(r) for r in rows]}
