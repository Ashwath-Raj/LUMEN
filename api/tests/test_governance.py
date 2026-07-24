"""
Governance register + masking + retention — LUMEN_MASTER_SPEC_V3 §4.

Covers `governance/classification.py`, `governance/masking.py`, and
`governance/retention.py`. Pure Python logic, no database or HTTP client
needed, matching Session 4's scope.
"""
import pytest

from lumen.governance.classification import (
    ASSET_REGISTER,
    classification_of,
    highest_classification,
)
from lumen.governance.masking import (
    EMPLOYEE_NEVER_RENDERED_FIELDS,
    K_ANONYMITY_THRESHOLD,
    complainant_caste_religion_visible,
    mask_accused_name,
    mask_complainant_name,
    mask_victim_age,
    mask_victim_name,
    suppress_small_aggregate,
)
from lumen.governance.retention import (
    canonical_tables_are_retention_exempt,
    retention_of,
)


# ─── §4.1/§4.2 classification ────────────────────────────────────────────

@pytest.mark.parametrize(
    "table,expected",
    [
        ("CaseMaster", "CONFIDENTIAL"),
        ("Victim", "RESTRICTED"),
        ("Accused", "RESTRICTED"),
        ("ComplainantDetails", "RESTRICTED"),
        ("Employee", "CONFIDENTIAL"),
        ("lumen_insight", "CONFIDENTIAL"),
        ("lumen_person", "RESTRICTED"),
        ("lumen_event", "INTERNAL"),
        ("lumen_audit", "RESTRICTED"),
        ("State", "PUBLIC"),
        ("District", "PUBLIC"),
    ],
)
def test_classification_matches_spec_table(table, expected):
    assert classification_of(table) == expected


def test_undeclared_table_raises_not_guessed():
    with pytest.raises(KeyError, match="Cannot determine from the specification"):
        classification_of("ArrestSurrender")


def test_highest_classification_is_most_sensitive():
    assert highest_classification("PUBLIC", "RESTRICTED", "INTERNAL") == "RESTRICTED"
    assert highest_classification("PUBLIC", "INTERNAL") == "INTERNAL"


def test_asset_register_has_no_duplicate_declarations():
    tables = [asset.table for asset in ASSET_REGISTER.values()]
    assert len(tables) == len(set(tables))


# ─── §4.2 masking ─────────────────────────────────────────────────────────

def test_victim_masked_below_district_sp():
    assert mask_victim_name("Jane Doe", "station_officer") == "V1"
    assert mask_victim_name("Jane Doe", "investigating_officer") == "V1"
    assert mask_victim_name("Jane Doe", "district_sp") == "Jane Doe"
    assert mask_victim_name("Jane Doe", "state_analyst") == "Jane Doe"


def test_victim_age_banded_below_district_sp():
    # Real age passes through at/above threshold; the spec gives no band
    # format below it, so this only asserts the raw value does NOT pass.
    assert mask_victim_age(34, "district_sp") == 34
    assert mask_victim_age(34, "station_officer") != 34


def test_accused_masked_below_investigating_officer():
    assert mask_accused_name("John Smith", "station_officer") == "A1"
    assert mask_accused_name("John Smith", "investigating_officer") == "John Smith"
    assert mask_accused_name("John Smith", "district_sp") == "John Smith"


def test_complainant_caste_religion_gated_on_both_role_and_view_context():
    assert complainant_caste_religion_visible("district_sp", is_single_case_detail_view=True) is True
    assert complainant_caste_religion_visible("district_sp", is_single_case_detail_view=False) is False
    assert complainant_caste_religion_visible("station_officer", is_single_case_detail_view=True) is False
    assert complainant_caste_religion_visible("state_analyst", is_single_case_detail_view=True) is True


def test_auditor_has_no_position_on_masking_scale():
    with pytest.raises(ValueError):
        mask_victim_name("Jane Doe", "auditor")


def test_employee_p9_adjacent_fields_never_rendered():
    assert EMPLOYEE_NEVER_RENDERED_FIELDS == ("EmployeeDOB", "BloodGroupID", "PhysicallyChallenged")


def test_k_anonymity_suppression():
    assert K_ANONYMITY_THRESHOLD == 5
    assert suppress_small_aggregate(2) == "fewer than 5 — suppressed"
    assert suppress_small_aggregate(4) == "fewer than 5 — suppressed"
    assert suppress_small_aggregate(5) == 5
    assert suppress_small_aggregate(100) == 100


# ─── §4.3 rule 1 retention ────────────────────────────────────────────────

def test_canonical_tables_exempt_from_retention():
    assert canonical_tables_are_retention_exempt("CaseMaster") is True
    assert canonical_tables_are_retention_exempt("Accused") is True
    assert canonical_tables_are_retention_exempt("lumen_insight") is False


def test_lumen_table_retention_periods():
    assert retention_of("lumen_insight") == "180 days then archived"
    assert retention_of("lumen_person") == "180 days, recomputed"
    assert retention_of("lumen_event") == "365 days"
    assert retention_of("lumen_audit") == "365 days"
    assert retention_of("lumen_kb_*") == "Until superseded"


def test_canonical_table_has_no_retention_period_to_look_up():
    with pytest.raises(ValueError, match="exempts it"):
        retention_of("CaseMaster")
