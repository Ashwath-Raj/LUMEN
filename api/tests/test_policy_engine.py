"""
Session 16 — policy engine (§20 RBAC + §21 audit).

Covers: the §20.1 role→capability table (all five roles, verbatim), the single
`authorize(user, action, resource) -> Decision` (§20.2 / §28 rule 7),
jurisdiction scoping on every decision, the invariant that EVERY decision
(allow and deny) writes one immutable lumen_audit row (§21) and that a deny
also emits PolicyDenied on the §19 bus (§20.2), append-only audit enforcement,
lumen_user_role loading, determinism, serialization, and edge cases.

Self-contained: in-memory SQLite, no live PostgreSQL.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.db.models.policy import LumenAudit, LumenUserRole
from lumen.policy import audit_repo, roles
from lumen.policy.engine import (
    Decision, PolicyUser, Resource, authorize, load_user,
)
from lumen.bus import signals

NOW = datetime(2026, 7, 25, 0, 0, tzinfo=timezone.utc)


def _fresh():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


@pytest.fixture(autouse=True)
def _isolate():
    signals.clear_subscribers()
    yield
    signals.clear_subscribers()


# ── §20.1 role → capability table ──────────────────────────────────────────

def test_five_roles_exactly():
    assert set(roles.ROLES) == {"state_analyst", "district_sp",
                                "investigating_officer", "station_officer",
                                "auditor"}


def test_state_analyst_capabilities():
    for a in ("read_case_detail", "run_ai", "run_graph_query",
              "approve_insight", "export"):
        assert roles.can("state_analyst", a)


def test_district_sp_sees_unmasked_and_approves():
    assert roles.can("district_sp", "see_unmasked_identity")
    assert roles.can("district_sp", "approve_insight")
    assert roles.can("district_sp", "export")


def test_investigating_officer_no_export_no_approve():
    assert roles.can("investigating_officer", "read_case_detail")
    assert roles.can("investigating_officer", "write_case_note")
    assert roles.can("investigating_officer", "run_ai")
    assert not roles.can("investigating_officer", "export")
    assert not roles.can("investigating_officer", "approve_insight")


def test_station_officer_masked_no_export_no_unmasked():
    assert roles.can("station_officer", "read_case_detail")
    assert roles.can("station_officer", "read_aggregate")
    assert not roles.can("station_officer", "see_unmasked_identity")
    assert not roles.can("station_officer", "export")
    assert not roles.can("station_officer", "approve_insight")


def test_auditor_audit_and_quality_only_no_case_detail():
    assert roles.can("auditor", "read_audit")
    assert roles.can("auditor", "read_quality")
    assert not roles.can("auditor", "read_case_detail")
    assert not roles.can("auditor", "run_ai")
    assert not roles.can("auditor", "export")


def test_unknown_role_capabilities_raises():
    with pytest.raises(KeyError):
        roles.capabilities("king")


# ── §20.2 authorize: capability gate ───────────────────────────────────────

def test_authorize_allows_capable_role():
    s = _fresh()
    d = authorize(s, PolicyUser("u1", "state_analyst"), "export",
                  Resource("case", "1000", district_id=1), now=NOW)
    assert isinstance(d, Decision) and d.allowed


def test_authorize_denies_missing_capability():
    s = _fresh()
    d = authorize(s, PolicyUser("u2", "station_officer"), "export",
                  Resource("case", "1000", unit_id=11), now=NOW)
    assert not d.allowed and "capability" in d.reason


# ── §20.2 jurisdiction scoping ─────────────────────────────────────────────

def test_district_scope_enforced():
    s = _fresh()
    sp = PolicyUser("u3", "district_sp", district_scope=[1])
    assert authorize(s, sp, "read_case_detail",
                     Resource("case", "1", district_id=1), now=NOW).allowed
    denied = authorize(s, sp, "read_case_detail",
                       Resource("case", "2", district_id=2), now=NOW)
    assert not denied.allowed and "scope" in denied.reason


def test_unit_scope_enforced():
    s = _fresh()
    io = PolicyUser("u4", "investigating_officer", unit_scope=[11])
    assert authorize(s, io, "read_case_detail",
                     Resource("case", "1", unit_id=11), now=NOW).allowed
    assert not authorize(s, io, "read_case_detail",
                         Resource("case", "1", unit_id=99), now=NOW).allowed


def test_all_scope_roles_pass_any_jurisdiction():
    s = _fresh()
    for role in ("state_analyst", "auditor"):
        u = PolicyUser(f"u-{role}", role)
        action = "read_audit" if role == "auditor" else "read_case_detail"
        assert authorize(s, u, action,
                         Resource("case", "9", district_id=7, unit_id=88),
                         now=NOW).allowed


def test_resource_without_jurisdiction_is_not_scope_restricted():
    s = _fresh()
    sp = PolicyUser("u5", "district_sp", district_scope=[1])
    # an aggregate resource carries no district → scope does not restrict it
    assert authorize(s, sp, "read_aggregate", Resource("aggregate"), now=NOW).allowed


# ── §21 / §20.2: every decision audited; deny emits PolicyDenied ───────────

def test_every_decision_writes_one_audit_row():
    s = _fresh()
    authorize(s, PolicyUser("u6", "state_analyst"), "export",
              Resource("case", "1", district_id=1), now=NOW)      # allow
    authorize(s, PolicyUser("u6", "station_officer"), "export",
              Resource("case", "1", unit_id=11), now=NOW)          # deny (cap)
    s.commit()
    rows = audit_repo.read(s)
    assert len(rows) == 2
    assert {r.decision for r in rows} == {"allow", "deny"}
    allow_row = next(r for r in rows if r.decision == "allow")
    assert allow_row.action == "export" and allow_row.reason        # reason present
    assert allow_row.resource == "case:1"


def test_deny_emits_policy_denied_allow_does_not():
    s = _fresh()
    events = []
    signals.subscribe("PolicyDenied", lambda ev: events.append(ev))
    authorize(s, PolicyUser("u7", "state_analyst"), "read_case_detail",
              Resource("case", "1", district_id=1), now=NOW)        # allow
    assert events == []
    authorize(s, PolicyUser("u7", "auditor"), "read_case_detail",
              Resource("case", "1"), now=NOW)                        # deny
    assert len(events) == 1
    ev = events[0]
    assert ev.event_type == "PolicyDenied"
    assert ev.payload["action"] == "read_case_detail"
    assert ev.actor_id == "u7"


def test_scope_denial_is_audited_and_emits_event():
    s = _fresh()
    events = []
    signals.subscribe("PolicyDenied", lambda ev: events.append(ev))
    authorize(s, PolicyUser("u8", "district_sp", district_scope=[1]),
              "read_case_detail", Resource("case", "5", district_id=9), now=NOW)
    s.commit()
    denies = audit_repo.read(s, decision="deny")
    assert len(denies) == 1 and "scope" in denies[0].reason
    assert len(events) == 1


# ── audit store is append-only (§21 / §4.2) ────────────────────────────────

def test_audit_is_append_only_no_update():
    s = _fresh()
    authorize(s, PolicyUser("u9", "state_analyst"), "run_ai",
              Resource("case", "1"), now=NOW)
    s.commit()
    row = audit_repo.read(s)[0]
    row.reason = "tampered"
    with pytest.raises(audit_repo.AuditAppendOnlyViolation):
        audit_repo.assert_append_only(s)


def test_audit_is_append_only_no_delete():
    s = _fresh()
    authorize(s, PolicyUser("u10", "state_analyst"), "run_ai",
              Resource("case", "1"), now=NOW)
    s.commit()
    s.delete(audit_repo.read(s)[0])
    with pytest.raises(audit_repo.AuditAppendOnlyViolation):
        audit_repo.assert_append_only(s)


def test_duplicate_audit_id_rejected():
    s = _fresh()
    audit_repo.append(s, LumenAudit(audit_id="a1", user_id="u", action="x",
                                    resource="r", decision="allow", reason="ok",
                                    occurred_at=NOW))
    with pytest.raises(audit_repo.AuditAppendOnlyViolation):
        audit_repo.append(s, LumenAudit(audit_id="a1", user_id="u", action="y",
                                        resource="r2", decision="deny",
                                        reason="no", occurred_at=NOW))


# ── §20.2 lumen_user_role ──────────────────────────────────────────────────

def test_load_user_from_user_role_table():
    s = _fresh()
    s.add(LumenUserRole(user_id="officer-1", role="station_officer",
                        district_scope=[1], unit_scope=[11]))
    s.flush()
    user = load_user(s, "officer-1")
    assert user is not None
    assert user.role == "station_officer" and user.unit_scope == [11]
    assert load_user(s, "nobody") is None


def test_authorize_end_to_end_from_persisted_role():
    s = _fresh()
    s.add(LumenUserRole(user_id="sp-1", role="district_sp",
                        district_scope=[1], unit_scope=None))
    s.flush()
    user = load_user(s, "sp-1")
    assert authorize(s, user, "read_case_detail",
                     Resource("case", "1", district_id=1), now=NOW).allowed
    assert not authorize(s, user, "read_case_detail",
                         Resource("case", "2", district_id=2), now=NOW).allowed


# ── determinism + serialization ────────────────────────────────────────────

def test_authorize_is_deterministic():
    def run():
        s = _fresh()
        u = PolicyUser("d", "district_sp", district_scope=[1])
        return [
            authorize(s, u, "read_case_detail", Resource("case", "1", district_id=1), now=NOW).allowed,
            authorize(s, u, "export", Resource("case", "1", district_id=1), now=NOW).allowed,
            authorize(s, u, "read_case_detail", Resource("case", "2", district_id=2), now=NOW).allowed,
        ]
    assert run() == run()


def test_scope_kind_table_matches_roles():
    assert set(roles.ROLE_SCOPE_KIND) == set(roles.ROLES)
    assert roles.ROLE_SCOPE_KIND["state_analyst"] == "all"
    assert roles.ROLE_SCOPE_KIND["district_sp"] == "district"
    assert roles.ROLE_SCOPE_KIND["station_officer"] == "unit"
