"""
Policy engine — LUMEN_MASTER_SPEC_V3 §20.2, §28 rule 7.

§28 rule 7: "`policy/engine.py` is the only authoriser." §20.2: "Policies live
in lumen_policy, evaluated by a single `authorize(user, action, resource) ->
Decision`. Every decision — allow **and** deny — writes to lumen_audit with a
reason and emits `PolicyDenied` on denial."

`authorize` is that single function. Evaluation is deterministic RBAC (T1):

  1. Capability — does the user's §20.1 role hold the requested action?
  2. Scope — is the resource within the user's jurisdiction scope
     (`lumen_user_role.district_scope` / `unit_scope`; §20.2 "jurisdiction
     scoping on every case query")?

Both must hold to allow. Every call — allow and deny — appends one immutable
`lumen_audit` row (§21); a deny also publishes `PolicyDenied` on the §19 bus
(§20.2). No ABAC/T2 attribute rules (juvenile records, masking thresholds,
export permissions, k-anonymity) — those are explicitly T2 and not built.

The user is a `PolicyUser` built from a `lumen_user_role` row. A resource is a
`Resource(kind, id, district_id?, unit_id?)` — the caller supplies the
resource's jurisdiction so scope can be checked without this module reaching
into repositories it must not duplicate.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from lumen.bus import signals
from lumen.contracts.event import EventContract, Subject
from lumen.db.models.policy import LumenAudit, LumenUserRole
from lumen.governance.masking import Role
from lumen.policy import audit_repo, roles


@dataclass(frozen=True)
class PolicyUser:
    user_id: str
    role: Role
    district_scope: list[int] | None = None   # None = all districts (§20.1)
    unit_scope: list[int] | None = None        # None = all units

    @classmethod
    def from_row(cls, row: LumenUserRole) -> "PolicyUser":
        return cls(user_id=row.user_id, role=row.role,
                   district_scope=row.district_scope, unit_scope=row.unit_scope)


@dataclass(frozen=True)
class Resource:
    kind: str                       # "case" | "aggregate" | "audit" | "quality" | ...
    id: str = ""
    district_id: int | None = None  # the resource's jurisdiction, for scope check
    unit_id: int | None = None


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


def load_user(session: Session, user_id: str) -> PolicyUser | None:
    row = session.get(LumenUserRole, user_id)
    return PolicyUser.from_row(row) if row is not None else None


def _scope_ok(user: PolicyUser, resource: Resource) -> tuple[bool, str]:
    """§20.2 jurisdiction scoping. A resource with no jurisdiction (e.g. an
    aggregate, audit, or quality resource) is not scope-restricted. `all`
    scope roles pass everything."""
    kind = roles.ROLE_SCOPE_KIND.get(user.role, "unit")
    if kind == "all":
        return True, "unrestricted scope"
    if kind == "district":
        if resource.district_id is None:
            return True, "resource carries no district scope"
        if user.district_scope is None or resource.district_id in user.district_scope:
            return True, "within district scope"
        return False, (f"resource district {resource.district_id} outside "
                       f"user district scope {user.district_scope}")
    # unit scope (investigating officer, station officer)
    if resource.unit_id is None:
        return True, "resource carries no unit scope"
    if user.unit_scope is None or resource.unit_id in user.unit_scope:
        return True, "within unit scope"
    return False, (f"resource unit {resource.unit_id} outside user unit scope "
                   f"{user.unit_scope}")


def authorize(session: Session, user: PolicyUser, action: str, resource: Resource,
              *, ip: str | None = None, now: datetime | None = None) -> Decision:
    """The single authoriser (§28 rule 7). Returns a Decision; audits every
    call; publishes PolicyDenied on denial (§20.2)."""
    now = now or datetime.now(timezone.utc)

    if not roles.can(user.role, action):
        decision = Decision(False, f"role {user.role!r} lacks capability {action!r}")
    else:
        ok, why = _scope_ok(user, resource)
        decision = Decision(ok, why if ok else f"scope denied: {why}")

    _audit(session, user, action, resource, decision, ip, now)
    if not decision.allowed:
        _emit_policy_denied(session, user, action, resource, decision, now)
    return decision


def _audit(session, user, action, resource, decision, ip, now) -> None:
    audit_repo.append(session, LumenAudit(
        audit_id=str(uuid.uuid4()),
        user_id=user.user_id,
        action=action,
        resource=f"{resource.kind}:{resource.id}" if resource.id else resource.kind,
        decision="allow" if decision.allowed else "deny",
        reason=decision.reason[:300],
        ip=ip,
        occurred_at=now,
    ))


def _emit_policy_denied(session, user, action, resource, decision, now) -> None:
    signals.publish(session, EventContract(
        event_id=str(uuid.uuid4()),
        event_type="PolicyDenied",                    # §19.2 catalogue
        occurred_at=now,
        actor_id=user.user_id,
        subject=Subject(type=resource.kind, id=resource.id or resource.kind),
        payload={"action": action, "role": user.role, "reason": decision.reason},
        trace_id=str(uuid.uuid4()),
        classification="INTERNAL",
    ))
