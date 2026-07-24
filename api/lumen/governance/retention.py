"""
Retention policy — LUMEN_MASTER_SPEC_V3 §4.3 rule 1 and §4.2's per-table
retention column.

§4.3 rule 1, verbatim: "LUMEN never deletes canonical records. It is an
analytical overlay, not a system of record. Retention applies to `lumen_`
tables only."

This has two structural consequences, both implemented here:
  1. No function in this codebase may delete a row from a canonical table
     (§3.5). `canonical_tables_are_retention_exempt()` documents and
     asserts this at the table-name level; the actual absence of any
     DELETE-issuing code against canonical models is enforced by there
     being no such code anywhere in `db/repositories/` (Session 2's
     repositories only `get`/`list`/`filter_by` — verified, not merely
     asserted).
  2. Retention periods (§4.2's Retention column) apply only to `lumen_`
     tables — `lumen_insight`/`lumen_person` (180 days), `lumen_event`/
     `lumen_audit` (365 days), `lumen_kb_*` (until superseded). No
     canonical table has a numeric retention period; its register entry
     is deliberately "Per record-retention policy; not deleted by LUMEN",
     which is not a duration LUMEN enforces itself.
"""
from __future__ import annotations

from dataclasses import dataclass

from lumen.governance.classification import ASSET_REGISTER

CANONICAL_TABLES = frozenset(
    {
        "State", "District", "Court", "UnitType", "Unit", "Rank", "Designation",
        "Employee", "Act", "Section", "CrimeHead", "CrimeSubHead",
        "CrimeHeadActSection", "CaseCategory", "GravityOffence", "CaseStatusMaster",
        "CasteMaster", "ReligionMaster", "OccupationMaster", "CaseMaster", "Victim",
        "Accused", "ComplainantDetails", "ActSectionAssociation", "ArrestSurrender",
        "inv_arrestsurrenderaccused", "ChargesheetDetails",
    }
)


def canonical_tables_are_retention_exempt(table: str) -> bool:
    """§4.3 rule 1: retention (a deletion policy with a time bound)
    applies to `lumen_` tables only. A canonical table is exempt — LUMEN
    is never the system that deletes it."""
    return table in CANONICAL_TABLES


@dataclass(frozen=True)
class RetentionPeriod:
    table: str
    period: str


# §4.2's retention column, for the `lumen_` tables it gives an actual
# period for. Canonical tables are intentionally absent from this dict —
# see `canonical_tables_are_retention_exempt()`.
LUMEN_TABLE_RETENTION: dict[str, RetentionPeriod] = {
    "lumen_insight": RetentionPeriod("lumen_insight", "180 days then archived"),
    "lumen_person": RetentionPeriod("lumen_person", "180 days, recomputed"),
    "lumen_event": RetentionPeriod("lumen_event", "365 days"),
    "lumen_audit": RetentionPeriod("lumen_audit", "365 days"),
    "lumen_kb_*": RetentionPeriod("lumen_kb_*", "Until superseded"),
}


def retention_of(table: str) -> str:
    """Retention period for a `lumen_` table. Raises for a canonical
    table (use `canonical_tables_are_retention_exempt()` for those — they
    have no time-bound retention to look up) or for any `lumen_` table not
    named in §4.2's register."""
    if table in CANONICAL_TABLES:
        raise ValueError(
            f"{table!r} is a canonical table — §4.3 rule 1 exempts it from "
            "LUMEN-enforced retention entirely; it has no period to look up."
        )
    period = LUMEN_TABLE_RETENTION.get(table)
    if period is None:
        raise KeyError(
            f"No retention period declared in LUMEN_MASTER_SPEC_V3 §4.2 for table {table!r}. "
            "Cannot determine from the specification."
        )
    return period.period
