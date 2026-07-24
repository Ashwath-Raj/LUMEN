"""
CI enforcement of the P9 deny-list — LUMEN_MASTER_SPEC_V3 §4.3 rule 6:
"P9 enforcement is structural, not a convention: `intelligence/guards.py`
holds the deny-list, every feature/prompt/chart builder passes through
it, and a CI test fails the build if a denied column reaches a model
input."

This is that CI test. It needs no database, no HTTP client, and no
running app — the guard is pure Python logic, so these tests exercise it
directly, matching Session 4's scope (governance/masking/P9 guards only;
no feature store, prompt builder, or chart layer exists yet to integrate
against — those are later sessions).
"""
import pytest

from lumen.intelligence.guards import (
    P9_DENIED_COLUMNS,
    P9ViolationError,
    assert_no_denied_columns,
    is_denied,
)
from lumen.db.models import canonical


def _p9_marked_columns_from_schema_source() -> set[tuple[str, str]]:
    """Independently re-derives the P9-marked columns straight from
    `canonical.py`'s own source text (its `# P9` inline comments), rather
    than importing `guards.py`'s constant — so this test can catch the
    deny-list drifting out of sync with the schema itself, not just
    re-assert the same constant against itself.
    """
    import inspect

    source = inspect.getsource(canonical)
    found: set[tuple[str, str]] = set()
    current_class: str | None = None
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("class ") and "(Base)" in stripped:
            current_class = stripped.split("class ")[1].split("(")[0].strip()
            continue
        if "# P9" in line and current_class:
            # e.g. "    BloodGroupID = Column(Integer)                # P9 ..."
            column_name = stripped.split("=")[0].strip()
            found.add((current_class, column_name))
    return found


def test_deny_list_matches_schema_p9_markers():
    """The deny-list in guards.py must exactly match every column the
    canonical schema itself marks `# P9` — no more, no fewer. A schema
    change that adds/removes a `# P9` marker without updating guards.py
    fails this test, keeping enforcement structural rather than something
    that silently drifts."""
    schema_marked = _p9_marked_columns_from_schema_source()
    assert schema_marked == set(P9_DENIED_COLUMNS), (
        f"guards.py's P9_DENIED_COLUMNS has drifted from canonical.py's own "
        f"# P9 markers. In schema but not in guard: {schema_marked - set(P9_DENIED_COLUMNS)}. "
        f"In guard but not in schema: {set(P9_DENIED_COLUMNS) - schema_marked}."
    )


@pytest.mark.parametrize(
    "table,column",
    [
        ("Employee", "BloodGroupID"),
        ("Employee", "PhysicallyChallenged"),
        ("ComplainantDetails", "ReligionID"),
        ("ComplainantDetails", "CasteID"),
    ],
)
def test_each_denied_column_is_flagged(table, column):
    assert is_denied(table, column) is True


@pytest.mark.parametrize(
    "table,column",
    [
        ("Employee", "GenderID"),  # adjacent to P9 columns in the DDL but not itself marked
        ("Employee", "FirstName"),
        ("ComplainantDetails", "GenderID"),
        ("ComplainantDetails", "ComplainantName"),
        ("CaseMaster", "BriefFacts"),
        ("Victim", "VictimName"),
    ],
)
def test_non_denied_columns_are_not_flagged(table, column):
    assert is_denied(table, column) is False


def test_model_input_containing_a_denied_column_fails_the_build():
    """The literal "Done when" criterion for this session: a denied
    column reaching a model input must fail (raise), not pass silently."""
    with pytest.raises(P9ViolationError, match="BloodGroupID"):
        assert_no_denied_columns("Employee", ["FirstName", "KGID", "BloodGroupID"])


def test_model_input_without_denied_columns_passes():
    """A feature/prompt/chart input built only from non-P9 columns must
    pass through the guard untouched."""
    assert_no_denied_columns("Employee", ["FirstName", "KGID", "AppointmentDate"]) is None


def test_first_denied_column_named_in_error_not_swallowed():
    """The guard must name which column violated P9, not just that
    something did — so the CI failure is actionable."""
    with pytest.raises(P9ViolationError) as excinfo:
        assert_no_denied_columns("ComplainantDetails", ["CasteID", "ReligionID"])
    assert "ComplainantDetails.CasteID" in str(excinfo.value)
