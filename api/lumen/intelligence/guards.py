"""
P9 deny-list enforcement — LUMEN_MASTER_SPEC_V3 §4.3 rule 6, P9 (§0),
§28 structural rule 10.

P9, verbatim (§0): "Protected attributes are never analytical inputs.
Caste, religion, blood group, disability status are stored because the
canonical schema defines them, and excluded from every feature, filter,
chart, prompt and map layer. Enforced by a deny-list, tested in CI."

§4.3 rule 6, verbatim: "P9 enforcement is structural, not a convention:
`intelligence/guards.py` holds the deny-list, every feature/prompt/chart
builder passes through it, and a CI test fails the build if a denied
column reaches a model input."

§28 structural rule 10, verbatim: "Nothing reads a P9 column outside the
governed display path in `governance/masking.py`."

The four denied columns are exactly the ones the canonical schema (§3.5)
marks `-- P9` in its own DDL comments, matching P9's textual list
(caste, religion, blood group, disability status):

    Employee.BloodGroupID
    Employee.PhysicallyChallenged
    ComplainantDetails.ReligionID
    ComplainantDetails.CasteID

`GenderID` appears adjacent to `BloodGroupID`/`PhysicallyChallenged` in
the same DDL line but is NOT marked `-- P9` and is not named in P9's
text — it is deliberately excluded from the deny-list; including it would
be inventing a restriction the specification does not state.

This module holds the deny-list and the one function
(`assert_no_denied_columns`) that every feature/prompt/chart builder must
call. No feature, prompt, or chart builder exists yet in this codebase
(intelligence/features.py, ai/prompts/*, the chart layer — all later
sessions), so there is nothing for this guard to be wired into beyond the
CI test itself. The CI test (`api/tests/test_p9_guards.py`) is what makes
enforcement "structural, not a convention" per rule 6 in the meantime: it
fails the build the moment a denied column reaches a model input, exactly
as the "Done when" criterion for this session states.
"""
from __future__ import annotations

P9_DENIED_COLUMNS: frozenset[tuple[str, str]] = frozenset(
    {
        ("Employee", "BloodGroupID"),
        ("Employee", "PhysicallyChallenged"),
        ("ComplainantDetails", "ReligionID"),
        ("ComplainantDetails", "CasteID"),
    }
)


class P9ViolationError(Exception):
    """Raised when a denied column reaches a model/feature/prompt/chart input."""


def is_denied(table: str, column: str) -> bool:
    """True if `(table, column)` is a P9-protected attribute per the
    canonical schema's own `-- P9` markers (§3.5)."""
    return (table, column) in P9_DENIED_COLUMNS


def assert_no_denied_columns(table: str, columns: list[str]) -> None:
    """The single call every feature/prompt/chart builder must pass
    through (§4.3 rule 6). Raises `P9ViolationError` naming the first
    denied column found, rather than silently dropping it — a silent drop
    would hide the defect instead of failing the build."""
    for column in columns:
        if is_denied(table, column):
            raise P9ViolationError(
                f"{table}.{column} is a P9-protected attribute (caste, religion, "
                "blood group, or disability status) and may not reach a model, "
                "feature, filter, chart, prompt, or map layer input. "
                "See LUMEN_MASTER_SPEC_V3 §0 (P9) and §4.3 rule 6."
            )
