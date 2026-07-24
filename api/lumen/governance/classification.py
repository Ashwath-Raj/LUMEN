"""
Data classification scheme and asset register — LUMEN_MASTER_SPEC_V3 §4.1-§4.2.

§4.1 defines four classification levels, in ascending sensitivity order.
§4.2 declares the classification, owner role, retention, and masking rule
for every table named in the spec's asset register table. Both are
reproduced here verbatim as data, not re-derived or "improved" — per the
Session 2 precedent, table/column names are not invented or renamed.

This module is a declaration only (§1's tiering: "T1 declaration, T2
enforcement" for §4 as a whole). `masking.py` and `retention.py` consume
this register to apply the rules it declares; `intelligence/guards.py`
enforces the P9 subset of RESTRICTED columns structurally.

**Scope note:** §4.2's table lists explicit rows for `CaseMaster`,
`Victim`, `Accused`, `ComplainantDetails`, `Employee`, `lumen_insight`,
`lumen_person`, `lumen_event`, `lumen_audit`, `lumen_kb_*`, plus a
catch-all row "Lookup tables -> PUBLIC". Every canonical lookup table
from §3.5 (`State`, `District`, `Court`, `UnitType`, `Unit`, `Rank`,
`Designation`, `Act`, `Section`, `CrimeHead`, `CrimeSubHead`,
`CrimeHeadActSection`, `CaseCategory`, `GravityOffence`,
`CaseStatusMaster`, `CasteMaster`, `ReligionMaster`, `OccupationMaster`)
is classified PUBLIC under that catch-all. Canonical tables NOT covered
by any §4.2 row or the lookup catch-all — `ActSectionAssociation`,
`ArrestSurrender`, `inv_arrestsurrenderaccused`, `ChargesheetDetails` —
have no declared classification anywhere in the specification.
`classification_of()` raises for these rather than guessing a value;
inferring one (e.g. "CONFIDENTIAL because it touches CaseMaster") would
be inventing a declaration the spec does not make.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Classification = Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]

# §4.1 — ascending sensitivity order, used for "derived data inherits the
# highest classification of its inputs" (§4.3 rule 2).
CLASSIFICATION_ORDER: dict[Classification, int] = {
    "PUBLIC": 0,
    "INTERNAL": 1,
    "CONFIDENTIAL": 2,
    "RESTRICTED": 3,
}


def highest_classification(*classifications: Classification) -> Classification:
    """§4.3 rule 2: "Derived data inherits the highest classification of
    its inputs. An insight built from Victim is RESTRICTED."."""
    if not classifications:
        raise ValueError("At least one classification is required")
    return max(classifications, key=lambda c: CLASSIFICATION_ORDER[c])


@dataclass(frozen=True)
class DataAsset:
    """One row of the §4.2 asset register (`lumen_data_asset`)."""

    table: str
    classification: Classification
    owner_role: str
    retention: str
    masking: str


# §4.2's explicit rows, reproduced verbatim.
_EXPLICIT_ASSETS: dict[str, DataAsset] = {
    "CaseMaster": DataAsset(
        table="CaseMaster",
        classification="CONFIDENTIAL",
        owner_role="State Analyst",
        retention="Per record-retention policy; not deleted by LUMEN",
        masking="BriefFacts truncated below District SP",
    ),
    "Victim": DataAsset(
        table="Victim",
        classification="RESTRICTED",
        owner_role="District SP",
        retention="As above",
        masking="Name masked to V1, age banded, below District SP",
    ),
    "Accused": DataAsset(
        table="Accused",
        classification="RESTRICTED",
        owner_role="District SP",
        retention="As above",
        masking="Name masked to A1 below Investigating Officer",
    ),
    "ComplainantDetails": DataAsset(
        table="ComplainantDetails",
        classification="RESTRICTED",
        owner_role="District SP",
        retention="As above",
        masking=(
            "Name masked; caste/religion never rendered outside a single "
            "case-detail view for District SP and above, never in any aggregate"
        ),
    ),
    "Employee": DataAsset(
        table="Employee",
        classification="CONFIDENTIAL",
        owner_role="Admin",
        retention="Employment + statutory",
        masking="EmployeeDOB, BloodGroupID, PhysicallyChallenged never rendered in LUMEN at all",
    ),
    "lumen_insight": DataAsset(
        table="lumen_insight",
        classification="CONFIDENTIAL",
        owner_role="State Analyst",
        retention="180 days then archived",
        masking="Inherits the classification of its subject",
    ),
    "lumen_person": DataAsset(
        table="lumen_person",
        classification="RESTRICTED",
        owner_role="State Analyst",
        retention="180 days, recomputed",
        masking="Always shown with confidence (P10)",
    ),
    "lumen_event": DataAsset(
        table="lumen_event",
        classification="INTERNAL",
        owner_role="Auditor",
        retention="365 days",
        masking="Immutable",
    ),
    "lumen_audit": DataAsset(
        table="lumen_audit",
        classification="RESTRICTED",
        owner_role="Auditor",
        retention="365 days",
        masking="Immutable, readable only by Auditor",
    ),
    "lumen_kb_*": DataAsset(
        table="lumen_kb_*",
        classification="INTERNAL",
        owner_role="Admin",
        retention="Until superseded",
        masking="—",
    ),
}

# §4.2's "Lookup tables" catch-all row (PUBLIC / Admin / Indefinite / —),
# applied to every canonical lookup table named in §3.5.
_LOOKUP_TABLES = (
    "State", "District", "Court", "UnitType", "Unit", "Rank", "Designation",
    "Act", "Section", "CrimeHead", "CrimeSubHead", "CrimeHeadActSection",
    "CaseCategory", "GravityOffence", "CaseStatusMaster", "CasteMaster",
    "ReligionMaster", "OccupationMaster",
)
_LOOKUP_ASSET_TEMPLATE = dict(classification="PUBLIC", owner_role="Admin", retention="Indefinite", masking="—")

ASSET_REGISTER: dict[str, DataAsset] = {
    **_EXPLICIT_ASSETS,
    **{name: DataAsset(table=name, **_LOOKUP_ASSET_TEMPLATE) for name in _LOOKUP_TABLES},
}


def classification_of(table: str) -> Classification:
    """Look up a table's declared classification.

    Raises `KeyError` for any canonical table not covered by an explicit
    §4.2 row or the lookup catch-all (e.g. `ActSectionAssociation`,
    `ArrestSurrender`, `inv_arrestsurrenderaccused`, `ChargesheetDetails`)
    — the specification declares no classification for these, and this
    function does not infer one.
    """
    asset = ASSET_REGISTER.get(table)
    if asset is None:
        raise KeyError(
            f"No classification declared in LUMEN_MASTER_SPEC_V3 §4.2 for table {table!r}. "
            "Cannot determine from the specification."
        )
    return asset.classification
