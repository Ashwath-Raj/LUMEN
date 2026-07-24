"""
Quality rule evaluation engine — LUMEN_MASTER_SPEC_V3 §5.

Runs the eighteen §5.1 rules over a scope and collects their findings.
The engine only *detects*; persisting findings to `lumen_quality_finding`
and scores to `lumen_quality_score` is the batch job's job (§5.2 "written
to lumen_quality_score on every precompute run" — see `jobs/quality.py`).

§5.2 defines three scopes: state, district, unit. The engine runs the full
canonical dataset through every rule once (rules are dataset-wide by
construction), then attributes each finding to the district and unit of the
CaseMaster it concerns, so `scoring.py` can score per scope without
re-running detection.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from lumen.db.models import canonical as m
from lumen.quality.rules import RULES, Finding


@dataclass
class EngineResult:
    findings: list[Finding]
    # records_in_scope per §5.2 denominator, keyed by scope.
    state_records: int
    district_records: dict[int, int]     # district_id -> case count
    unit_records: dict[int, int]         # unit_id -> case count
    # (district_id, unit_id) lookup per case, so findings can be attributed.
    case_district: dict[int, int | None]
    case_unit: dict[int, int | None]


def run_all_rules(session: Session) -> list[Finding]:
    """Run every §5.1 rule; return the flat list of findings."""
    findings: list[Finding] = []
    for rule in RULES:
        findings.extend(rule.detector(session))
    return findings


def evaluate(session: Session) -> EngineResult:
    """Run all rules and build the scope-attribution structures §5.2 needs."""
    findings = run_all_rules(session)

    units = {u.UnitID: u for u in session.query(m.Unit).all()}
    case_district: dict[int, int | None] = {}
    case_unit: dict[int, int | None] = {}
    district_records: dict[int, int] = {}
    unit_records: dict[int, int] = {}
    state_records = 0

    for c in session.query(m.CaseMaster).all():
        state_records += 1
        unit_id = c.PoliceStationID
        district_id = units[unit_id].DistrictID if unit_id in units else None
        case_unit[c.CaseMasterID] = unit_id
        case_district[c.CaseMasterID] = district_id
        if unit_id is not None:
            unit_records[unit_id] = unit_records.get(unit_id, 0) + 1
        if district_id is not None:
            district_records[district_id] = district_records.get(district_id, 0) + 1

    return EngineResult(
        findings=findings,
        state_records=state_records,
        district_records=district_records,
        unit_records=unit_records,
        case_district=case_district,
        case_unit=case_unit,
    )
