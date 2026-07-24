"""
Identity masking rules — LUMEN_MASTER_SPEC_V3 §4.2 (masking column) and
§20.2 ("Build identity masking even though it is T2").

§20.1 gives five roles; masking thresholds in §4.2 are expressed as
"below District SP" / "below Investigating Officer", which only make
sense against a defined role ordering. The ordering used here is the
one implied by §20.1's own scope column (State Analyst: all districts;
District SP: own district; Investigating Officer: assigned cases + own
unit; Station Officer: own unit) — each row is a strict narrowing of the
one above it. `Auditor` is excluded from this ordering: §20.1 gives it
"Audit log and quality only; no case detail", so it never sees identity
fields (masked or not) in the first place — it is not a point on the
masking scale, it is out of scope for identity data entirely.

Masking rules implemented, verbatim from §4.2:
  - Victim:             name -> "V1", age banded,        below District SP
  - Accused:             name -> "A1",                     below Investigating Officer
  - ComplainantDetails:  name masked (same threshold as Victim/Accused's
                         District SP row groups it with — see note below);
                         caste/religion NEVER rendered outside a single
                         case-detail view for District SP and above, and
                         NEVER in any aggregate, regardless of role.
  - Employee:            EmployeeDOB, BloodGroupID, PhysicallyChallenged
                         never rendered in LUMEN at all, for any role.

Note on ComplainantDetails' name-masking threshold: §4.2's masking cell
for this row states only "Name masked; ..." without repeating an
explicit "below District SP" qualifier the way the Victim and Accused
rows do. Since ComplainantDetails shares Victim's owner role (District
SP) and RESTRICTED classification in the same table, and no other
threshold is given anywhere in the document, the Victim threshold
(below District SP) is applied here as the only value consistent with
the rest of the row — not a different, invented one.
"""
from __future__ import annotations

from typing import Literal

Role = Literal["state_analyst", "district_sp", "investigating_officer", "station_officer", "auditor"]

# Strict ordering, most privileged first — §20.1's scope column, narrowing
# at each row. Auditor is deliberately absent: it has no case-detail access
# at all (§20.1), so it is never compared against this scale.
_ROLE_RANK: dict[Role, int] = {
    "state_analyst": 3,
    "district_sp": 2,
    "investigating_officer": 1,
    "station_officer": 0,
}


def _rank(role: Role) -> int:
    if role not in _ROLE_RANK:
        raise ValueError(
            f"Role {role!r} has no position on the identity-masking scale "
            "(§20.1: Auditor has no case-detail access at all)."
        )
    return _ROLE_RANK[role]


def _at_least(role: Role, threshold: Role) -> bool:
    return _rank(role) >= _rank(threshold)


def mask_victim_name(name: str, viewer_role: Role) -> str:
    """"Name masked to V1, age banded, below District SP" (§4.2)."""
    if _at_least(viewer_role, "district_sp"):
        return name
    return "V1"


def mask_victim_age(age_year: int, viewer_role: Role) -> int | None:
    """"Age banded ... below District SP" (§4.2). The specification states
    that age is banded below District SP but does not specify a band
    width, boundary alignment, or output format anywhere in the document.
    Inventing one (e.g. "10-year bands") would be inventing behaviour the
    session's own instructions forbid. This function therefore returns
    the real age unmasked at/above the threshold, and `None` below it —
    i.e., it enforces that the raw age must not pass through unbanded,
    without fabricating what the band itself looks like. The banding
    representation itself is: Cannot determine from the specification."""
    if _at_least(viewer_role, "district_sp"):
        return age_year
    return None


def mask_accused_name(name: str, viewer_role: Role) -> str:
    """"Name masked to A1 below Investigating Officer" (§4.2)."""
    if _at_least(viewer_role, "investigating_officer"):
        return name
    return "A1"


def mask_complainant_name(name: str, viewer_role: Role) -> str:
    """Name masked below District SP — see module docstring note on why
    this threshold (not a different one) is used for ComplainantDetails."""
    if _at_least(viewer_role, "district_sp"):
        return name
    return "C1"


def complainant_caste_religion_visible(viewer_role: Role, *, is_single_case_detail_view: bool) -> bool:
    """"caste/religion never rendered outside a single case-detail view
    for District SP and above, never in any aggregate" (§4.2). Both
    conditions are required: role >= District SP AND the specific
    single-case-detail context — an aggregate view never passes
    regardless of role."""
    if not is_single_case_detail_view:
        return False
    return _at_least(viewer_role, "district_sp")


# "EmployeeDOB, BloodGroupID, PhysicallyChallenged never rendered in
# LUMEN at all" (§4.2) — no role check function exists for these because
# no role ever sees them; they are excluded at the point of read, not
# masked at the point of display.
EMPLOYEE_NEVER_RENDERED_FIELDS = ("EmployeeDOB", "BloodGroupID", "PhysicallyChallenged")

# §4.3 rule 3, verbatim: "Aggregates below k=5 are suppressed. A
# district-week count of 2 with a caste breakdown is re-identification.
# The UI shows 'fewer than 5 - suppressed.'" Placed here rather than in a
# separate file since §28 names only classification.py/masking.py/
# retention.py under governance/, and k-anonymity suppression is, like the
# rest of this module, a decision about what is safe to reveal to a
# viewer — not a classification declaration (classification.py) or a
# deletion timeline (retention.py).
K_ANONYMITY_THRESHOLD = 5
SUPPRESSED_AGGREGATE_LABEL = "fewer than 5 — suppressed"


def suppress_small_aggregate(count: int) -> int | str:
    """Returns the count unchanged at or above the k=5 threshold, and the
    exact spec-given label below it. §4.3 rule 3 gives this literal UI
    string; it is reproduced verbatim, not paraphrased."""
    if count >= K_ANONYMITY_THRESHOLD:
        return count
    return SUPPRESSED_AGGREGATE_LABEL
