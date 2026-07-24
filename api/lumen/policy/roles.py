"""
Role → capability policy — LUMEN_MASTER_SPEC_V3 §20.1.

§20.1's role table reproduced as data — the code-defined policy (§20.2
references `lumen_policy`, but §3.6 defines no DDL for that table, so the
policy that §20.1 fully specifies lives here rather than in an invented
table; recorded in the Session deliverables).

The five roles reuse the `Role` enum already defined in
`governance/masking.py` (Session 4) — not redefined here (§28: one vocabulary).

| Role                  | Scope              | May do                                    |
|-----------------------|--------------------|-------------------------------------------|
| State Analyst         | All districts      | Read all, run AI, run graph queries,      |
|                       |                    | approve insights, export                  |
| District SP           | Own district       | Everything in scope, approve insights,    |
|                       |                    | see unmasked identities                   |
| Investigating Officer | Assigned cases +   | Case detail, notes, AI on own cases       |
|                       | own unit           |                                           |
| Station Officer       | Own unit           | Unit cases, aggregate views, masked ids   |
| Auditor               | All, read-only     | Audit log and quality only; no case detail|

Actions are the capability verbs §20.1 states, verbatim as an enum. The
role→action mapping below is a direct transcription of the "May do" column;
nothing is added. "Everything in scope" (District SP) expands to the full
action set within scope. Scope enforcement (district/unit) is applied by the
engine against `lumen_user_role`, separately from the capability check.
"""
from __future__ import annotations

from typing import Literal

from lumen.governance.masking import Role   # the §20.1 role vocabulary (Session 4)

# The capability verbs named across §20.1's "May do" column.
Action = Literal[
    "read_case_detail",     # "Read all" / "Case detail" / "Unit cases"
    "read_aggregate",       # "aggregate views"
    "run_ai",               # "run AI" / "AI on own cases"
    "run_graph_query",      # "run graph queries"
    "approve_insight",      # "approve insights"
    "export",               # "export"
    "write_case_note",      # "notes"
    "read_audit",           # "Audit log"
    "read_quality",         # "quality"
    "see_unmasked_identity",  # "see unmasked identities"
]

ROLES: tuple[Role, ...] = (
    "state_analyst", "district_sp", "investigating_officer",
    "station_officer", "auditor",
)

# §20.1 "May do", transcribed. `read_quality` is available to every role that
# may read anything (quality is PUBLIC/INTERNAL, §4.2) — the Auditor row names
# it explicitly; the operational roles get it as part of their read scope.
_CAPABILITIES: dict[Role, frozenset[str]] = {
    # Read all, run AI, run graph queries, approve insights, export
    "state_analyst": frozenset({
        "read_case_detail", "read_aggregate", "run_ai", "run_graph_query",
        "approve_insight", "export", "write_case_note", "read_quality",
    }),
    # Everything in scope, approve insights, see unmasked identities
    "district_sp": frozenset({
        "read_case_detail", "read_aggregate", "run_ai", "run_graph_query",
        "approve_insight", "export", "write_case_note", "read_quality",
        "see_unmasked_identity",
    }),
    # Case detail, notes, AI on own cases
    "investigating_officer": frozenset({
        "read_case_detail", "read_aggregate", "run_ai", "write_case_note",
        "read_quality",
    }),
    # Unit cases, aggregate views, masked identities (no unmasked, no export,
    # no approve)
    "station_officer": frozenset({
        "read_case_detail", "read_aggregate", "read_quality",
    }),
    # Audit log and quality only; no case detail
    "auditor": frozenset({
        "read_audit", "read_quality",
    }),
}


def capabilities(role: Role) -> frozenset[str]:
    if role not in _CAPABILITIES:
        raise KeyError(f"Unknown role {role!r}; not one of §20.1's five roles.")
    return _CAPABILITIES[role]


def can(role: Role, action: str) -> bool:
    """Whether `role` holds `action` per §20.1 (capability check only; scope
    is enforced separately by the engine)."""
    return action in _CAPABILITIES.get(role, frozenset())


# §20.1 scope column, as data. None = unrestricted ("All districts" /
# "All, read-only"); the other roles narrow to district/unit/case scope,
# enforced by the engine against lumen_user_role.
ROLE_SCOPE_KIND: dict[Role, str] = {
    "state_analyst": "all",
    "district_sp": "district",
    "investigating_officer": "unit",      # assigned cases + own unit
    "station_officer": "unit",
    "auditor": "all",                     # read-only, audit/quality only
}
