"""
Policy / access tables — LUMEN_MASTER_SPEC_V3 §3.6, §20.2, §21.

Two `lumen_` tables, defined verbatim from §3.6's DDL block:

    lumen_audit(audit_id UUID PK, user_id, action, resource, decision,
                reason, ip, occurred_at)
    lumen_user_role(user_id PK, role, district_scope JSON, unit_scope JSON)

`lumen_audit` (§21): "covers *access* ... who read which case, who ran which
AI query, who exported what, who was denied." Immutable, Auditor-readable
(§4.2). The append-only discipline is enforced in the repository layer
(`policy/audit_repo.py`) — no updates, no deletes — the same treatment §21
gives `lumen_event`.

`lumen_user_role` (§20.2 T1): "roles in lumen_user_role" — the user's role and
jurisdiction scope (`district_scope` / `unit_scope` JSON arrays of ids).

NOTE — `lumen_policy` is referenced by §20.2's prose ("Policies live in
lumen_policy") but §3.6's schema block defines NO DDL for it. Its columns
cannot be determined from the specification, so no `lumen_policy` table is
created here; the §20.1 role→capability policy is code-defined in
`policy/roles.py` (which §20.1 fully specifies). This is recorded in the
Session deliverables.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, JSON, String

from lumen.db.session import Base


class LumenAudit(Base):
    __tablename__ = "lumen_audit"

    audit_id = Column(String(36), primary_key=True)      # UUID (§3.6)
    user_id = Column(String(60))
    action = Column(String(60))
    resource = Column(String(120))
    decision = Column(String(20))                        # "allow" | "deny"
    reason = Column(String(300))
    ip = Column(String(60))
    occurred_at = Column(DateTime)


class LumenUserRole(Base):
    __tablename__ = "lumen_user_role"

    user_id = Column(String(60), primary_key=True)
    role = Column(String(40))                            # §20.1 role
    district_scope = Column(JSON)                        # [DistrictID, ...] | null (all)
    unit_scope = Column(JSON)                            # [UnitID, ...] | null (all)
