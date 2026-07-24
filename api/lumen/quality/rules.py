"""
Data quality rule catalogue — LUMEN_MASTER_SPEC_V3 §5.1.

The eighteen rules Q01–Q18, each reproduced from §5.1's table: rule id,
dimension, severity, and a detector implementing the "Detection" column
exactly as written. Detectors run over a SQLAlchemy session against the
canonical §3.5 schema and yield `Finding` objects — one per offending
record — which `engine.py` collects and `scoring.py` weighs.

Constants shared with Session 5's deterministic seed (the Karnataka
bounding box) are imported from `jobs.seed` rather than re-declared, per
the instruction to consume Session 5 rather than rewrite it.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Callable, Iterator

from sqlalchemy.orm import Session

from lumen.db.models import canonical as m
from lumen.jobs.seed import KARNATAKA_LAT, KARNATAKA_LNG

# §5.2's severity weights (Critical 4, High 2, Medium 1, Low 0.5).
SEVERITY_WEIGHT = {"Critical": 4.0, "High": 2.0, "Medium": 1.0, "Low": 0.5}

# §5.1 / §5.2 dimensions.
DIMENSIONS = ("completeness", "validity", "consistency", "integrity", "uniqueness", "timeliness")

# §3.2 fact 4 — documented CrimeNo category digits (FIR 1, UDR 3, PAR 4, Zero FIR 8).
DOCUMENTED_CRIMENO_CATEGORIES = {"1", "3", "4", "8"}

# §5.1 Q16: "no process event in 180 days".
STALE_DAYS = 180


@dataclass(frozen=True)
class Finding:
    rule_id: str
    dimension: str
    severity: str
    entity_type: str
    entity_id: str
    detail: dict


@dataclass(frozen=True)
class Rule:
    rule_id: str
    name: str
    dimension: str
    severity: str
    detector: Callable[[Session], Iterator[Finding]]


# ── individual detectors ──────────────────────────────────────────────────

def _q01_missing_coordinates(session: Session) -> Iterator[Finding]:
    for c in session.query(m.CaseMaster).all():
        if c.latitude is None or c.longitude is None:
            yield Finding("Q01", "completeness", "High", "CaseMaster", str(c.CaseMasterID),
                          {"latitude": c.latitude, "longitude": c.longitude})


def _q02_impossible_coordinates(session: Session) -> Iterator[Finding]:
    for c in session.query(m.CaseMaster).all():
        if c.latitude is None or c.longitude is None:
            continue  # missing is Q01, not Q02
        lat, lng = float(c.latitude), float(c.longitude)
        if (lat == 0.0 and lng == 0.0) or not (
            KARNATAKA_LAT[0] <= lat <= KARNATAKA_LAT[1] and KARNATAKA_LNG[0] <= lng <= KARNATAKA_LNG[1]
        ):
            yield Finding("Q02", "validity", "Critical", "CaseMaster", str(c.CaseMasterID),
                          {"latitude": lat, "longitude": lng})


def _q03_malformed_crimeno(session: Session) -> Iterator[Finding]:
    for c in session.query(m.CaseMaster).all():
        cn = c.CrimeNo or ""
        if len(cn) != 18 or not cn.isdigit() or cn[0] not in DOCUMENTED_CRIMENO_CATEGORIES:
            yield Finding("Q03", "validity", "High", "CaseMaster", str(c.CaseMasterID),
                          {"crime_no": cn})


def _q04_crimeno_unit_mismatch(session: Session) -> Iterator[Finding]:
    units = {u.UnitID: u for u in session.query(m.Unit).all()}
    for c in session.query(m.CaseMaster).all():
        cn = c.CrimeNo or ""
        if len(cn) != 18 or not cn.isdigit():
            continue  # malformed is Q03; can't decode here
        embedded_district = int(cn[1:5])
        embedded_unit = int(cn[5:9])
        unit = units.get(c.PoliceStationID)
        if unit is None:
            continue
        if embedded_unit != unit.UnitID or (unit.DistrictID is not None and embedded_district != unit.DistrictID):
            yield Finding("Q04", "consistency", "High", "CaseMaster", str(c.CaseMasterID),
                          {"embedded_district": embedded_district, "embedded_unit": embedded_unit,
                           "registering_unit": unit.UnitID, "registering_district": unit.DistrictID})


def _q05_incident_after_registration(session: Session) -> Iterator[Finding]:
    for c in session.query(m.CaseMaster).all():
        if c.IncidentFromDate is not None and c.CrimeRegisteredDate is not None:
            inc = c.IncidentFromDate.date() if isinstance(c.IncidentFromDate, datetime) else c.IncidentFromDate
            if inc > c.CrimeRegisteredDate:
                yield Finding("Q05", "consistency", "High", "CaseMaster", str(c.CaseMasterID),
                              {"incident_from": str(c.IncidentFromDate), "registered": str(c.CrimeRegisteredDate)})


def _q06_info_before_incident(session: Session) -> Iterator[Finding]:
    for c in session.query(m.CaseMaster).all():
        if c.InfoReceivedPSDate is not None and c.IncidentFromDate is not None:
            if c.InfoReceivedPSDate < c.IncidentFromDate:
                yield Finding("Q06", "consistency", "High", "CaseMaster", str(c.CaseMasterID),
                              {"info_received": str(c.InfoReceivedPSDate), "incident_from": str(c.IncidentFromDate)})


def _q07_chargesheet_before_registration(session: Session) -> Iterator[Finding]:
    cases = {c.CaseMasterID: c for c in session.query(m.CaseMaster).all()}
    for cs in session.query(m.ChargesheetDetails).all():
        case = cases.get(cs.CaseMasterID)
        if case is None or cs.csdate is None or case.CrimeRegisteredDate is None:
            continue
        csd = cs.csdate.date() if isinstance(cs.csdate, datetime) else cs.csdate
        if csd < case.CrimeRegisteredDate:
            yield Finding("Q07", "consistency", "Critical", "ChargesheetDetails", str(cs.CSID),
                          {"csdate": str(cs.csdate), "registered": str(case.CrimeRegisteredDate)})


def _q08_arrest_before_incident(session: Session) -> Iterator[Finding]:
    cases = {c.CaseMasterID: c for c in session.query(m.CaseMaster).all()}
    for a in session.query(m.ArrestSurrender).all():
        case = cases.get(a.CaseMasterID)
        if case is None or a.ArrestSurrenderDate is None or case.IncidentFromDate is None:
            continue
        inc = case.IncidentFromDate.date() if isinstance(case.IncidentFromDate, datetime) else case.IncidentFromDate
        if a.ArrestSurrenderDate < inc:
            yield Finding("Q08", "consistency", "Critical", "ArrestSurrender", str(a.ArrestSurrenderID),
                          {"arrest_date": str(a.ArrestSurrenderDate), "incident_from": str(case.IncidentFromDate)})


def _q09_orphan_child_row(session: Session) -> Iterator[Finding]:
    """CaseMasterID with no parent — a case-child row referencing a
    CaseMaster that does not exist."""
    case_ids = {c.CaseMasterID for c in session.query(m.CaseMaster).all()}
    children = (
        (m.Victim, "Victim", lambda r: r.VictimMasterID),
        (m.Accused, "Accused", lambda r: r.AccusedMasterID),
        (m.ComplainantDetails, "ComplainantDetails", lambda r: r.ComplainantID),
        (m.ActSectionAssociation, "ActSectionAssociation", lambda r: f"{r.CaseMasterID}:{r.ActID}:{r.SectionID}"),
        (m.ArrestSurrender, "ArrestSurrender", lambda r: r.ArrestSurrenderID),
        (m.ChargesheetDetails, "ChargesheetDetails", lambda r: r.CSID),
    )
    for model, entity_type, id_of in children:
        for row in session.query(model).all():
            if row.CaseMasterID not in case_ids:
                yield Finding("Q09", "integrity", "Critical", entity_type, str(id_of(row)),
                              {"orphan_case_master_id": row.CaseMasterID})


def _q10_broken_lookup_reference(session: Session) -> Iterator[Finding]:
    """FK to a missing or inactive lookup. Checks CaseMaster's lookup FKs
    against the presence (and Active flag, where the lookup has one) of the
    referenced row."""
    def active_ids(model, id_attr):
        out = {}
        for row in session.query(model).all():
            active = getattr(row, "Active", True)
            out[getattr(row, id_attr)] = active if active is not None else True
        return out

    categories = active_ids(m.CaseCategory, "CaseCategoryID")
    gravities = active_ids(m.GravityOffence, "GravityOffenceID")
    heads = active_ids(m.CrimeHead, "CrimeHeadID")
    subheads = active_ids(m.CrimeSubHead, "CrimeSubHeadID")
    statuses = active_ids(m.CaseStatusMaster, "CaseStatusID")
    units = active_ids(m.Unit, "UnitID")
    courts = active_ids(m.Court, "CourtID")

    checks = [
        ("CaseCategoryID", lambda c: c.CaseCategoryID, categories),
        ("GravityOffenceID", lambda c: c.GravityOffenceID, gravities),
        ("CrimeMajorHeadID", lambda c: c.CrimeMajorHeadID, heads),
        ("CrimeMinorHeadID", lambda c: c.CrimeMinorHeadID, subheads),
        ("CaseStatusID", lambda c: c.CaseStatusID, statuses),
        ("PoliceStationID", lambda c: c.PoliceStationID, units),
        ("CourtID", lambda c: c.CourtID, courts),
    ]
    for c in session.query(m.CaseMaster).all():
        for col, getter, lookup in checks:
            fk = getter(c)
            if fk is None:
                continue
            if fk not in lookup:
                yield Finding("Q10", "integrity", "High", "CaseMaster", str(c.CaseMasterID),
                              {"column": col, "value": fk, "reason": "missing"})
            elif lookup[fk] is False:
                yield Finding("Q10", "integrity", "High", "CaseMaster", str(c.CaseMasterID),
                              {"column": col, "value": fk, "reason": "inactive"})


def _q11_head_subhead_disagreement(session: Session) -> Iterator[Finding]:
    subheads = {sh.CrimeSubHeadID: sh.CrimeHeadID for sh in session.query(m.CrimeSubHead).all()}
    for c in session.query(m.CaseMaster).all():
        if c.CrimeMinorHeadID is None or c.CrimeMajorHeadID is None:
            continue
        expected = subheads.get(c.CrimeMinorHeadID)
        if expected is not None and expected != c.CrimeMajorHeadID:
            yield Finding("Q11", "consistency", "Medium", "CaseMaster", str(c.CaseMasterID),
                          {"major_head": c.CrimeMajorHeadID, "sub_head": c.CrimeMinorHeadID,
                           "sub_head_parent": expected})


def _q12_duplicate_case_suspicion(session: Session) -> Iterator[Finding]:
    """Same unit + date + head + ≥1 shared participant name."""
    accused_by_case = defaultdict(set)
    for a in session.query(m.Accused).all():
        if a.AccusedName:
            accused_by_case[a.CaseMasterID].add(a.AccusedName)
    victims_by_case = defaultdict(set)
    for v in session.query(m.Victim).all():
        if v.VictimName:
            victims_by_case[v.CaseMasterID].add(v.VictimName)

    groups = defaultdict(list)
    for c in session.query(m.CaseMaster).all():
        key = (c.PoliceStationID, c.CrimeRegisteredDate, c.CrimeMajorHeadID)
        groups[key].append(c)

    for key, cases in groups.items():
        if len(cases) < 2:
            continue
        for i in range(len(cases)):
            for j in range(i + 1, len(cases)):
                a, b = cases[i], cases[j]
                names_a = accused_by_case[a.CaseMasterID] | victims_by_case[a.CaseMasterID]
                names_b = accused_by_case[b.CaseMasterID] | victims_by_case[b.CaseMasterID]
                shared = names_a & names_b
                if shared:
                    yield Finding("Q12", "uniqueness", "Medium", "CaseMaster", str(b.CaseMasterID),
                                  {"duplicate_of": a.CaseMasterID, "shared_names": sorted(shared),
                                   "unit": key[0], "date": str(key[1]), "head": key[2]})


def _q13_implausible_age(session: Session) -> Iterator[Finding]:
    for model, entity_type, id_of in (
        (m.Accused, "Accused", lambda r: r.AccusedMasterID),
        (m.Victim, "Victim", lambda r: r.VictimMasterID),
        (m.ComplainantDetails, "ComplainantDetails", lambda r: r.ComplainantID),
    ):
        for row in session.query(model).all():
            age = row.AgeYear
            if age is not None and (age < 1 or age > 110):
                yield Finding("Q13", "validity", "Medium", entity_type, str(id_of(row)),
                              {"age_year": age})


def _q14_accused_no_personid(session: Session) -> Iterator[Finding]:
    """PersonID null where siblings (same case) have it."""
    by_case = defaultdict(list)
    for a in session.query(m.Accused).all():
        by_case[a.CaseMasterID].append(a)
    for case_id, rows in by_case.items():
        siblings_have = any(r.PersonID for r in rows)
        if not siblings_have:
            continue
        for r in rows:
            if not r.PersonID:
                yield Finding("Q14", "completeness", "Low", "Accused", str(r.AccusedMasterID),
                              {"case_master_id": case_id})


def _q15_case_no_charges(session: Session) -> Iterator[Finding]:
    charged = {a.CaseMasterID for a in session.query(m.ActSectionAssociation).all()}
    for c in session.query(m.CaseMaster).all():
        if c.CaseMasterID not in charged:
            yield Finding("Q15", "completeness", "Medium", "CaseMaster", str(c.CaseMasterID), {})


def _q16_stale_open_case(session: Session, *, now: date | None = None) -> Iterator[Finding]:
    """Status open, no process event in 180 days. Process events: arrest,
    chargesheet, or the dated case columns (§2.1 ProcessEvent)."""
    now = now or date.today()
    statuses = {s.CaseStatusID: s.CaseStatusName for s in session.query(m.CaseStatusMaster).all()}
    arrests = defaultdict(list)
    for a in session.query(m.ArrestSurrender).all():
        if a.ArrestSurrenderDate:
            arrests[a.CaseMasterID].append(a.ArrestSurrenderDate)
    chargesheets = defaultdict(list)
    for cs in session.query(m.ChargesheetDetails).all():
        if cs.csdate:
            d = cs.csdate.date() if isinstance(cs.csdate, datetime) else cs.csdate
            chargesheets[cs.CaseMasterID].append(d)

    for c in session.query(m.CaseMaster).all():
        status_name = (statuses.get(c.CaseStatusID) or "").lower()
        is_open = "investigation" in status_name or "open" in status_name
        if not is_open:
            continue
        event_dates = list(arrests[c.CaseMasterID]) + list(chargesheets[c.CaseMasterID])
        if c.CrimeRegisteredDate:
            event_dates.append(c.CrimeRegisteredDate)
        if c.IncidentFromDate:
            event_dates.append(
                c.IncidentFromDate.date() if isinstance(c.IncidentFromDate, datetime) else c.IncidentFromDate
            )
        if c.InfoReceivedPSDate:
            event_dates.append(
                c.InfoReceivedPSDate.date() if isinstance(c.InfoReceivedPSDate, datetime) else c.InfoReceivedPSDate
            )
        if not event_dates:
            continue
        last_event = max(event_dates)
        if (now - last_event) > timedelta(days=STALE_DAYS):
            yield Finding("Q16", "timeliness", "Medium", "CaseMaster", str(c.CaseMasterID),
                          {"last_event": str(last_event), "days_stale": (now - last_event).days})


def _q17_inactive_act_section(session: Session) -> Iterator[Finding]:
    """ActSectionAssociation → Active = false. The association references an
    Act/Section that is inactive."""
    inactive_acts = {a.ActCode for a in session.query(m.Act).all() if a.Active is False}
    inactive_sections = {
        (s.ActCode, s.SectionCode) for s in session.query(m.Section).all() if s.Active is False
    }
    for assoc in session.query(m.ActSectionAssociation).all():
        act_inactive = assoc.ActID in inactive_acts
        section_inactive = (assoc.ActID, assoc.SectionID) in inactive_sections
        if act_inactive or section_inactive:
            yield Finding("Q17", "validity", "Medium", "ActSectionAssociation",
                          f"{assoc.CaseMasterID}:{assoc.ActID}:{assoc.SectionID}",
                          {"act_inactive": act_inactive, "section_inactive": section_inactive})


def _q18_empty_brief_facts(session: Session) -> Iterator[Finding]:
    for c in session.query(m.CaseMaster).all():
        bf = c.BriefFacts
        if bf is None or len(bf) < 20:
            yield Finding("Q18", "completeness", "Low", "CaseMaster", str(c.CaseMasterID),
                          {"length": 0 if bf is None else len(bf)})


# ── the catalogue ─────────────────────────────────────────────────────────

RULES: list[Rule] = [
    Rule("Q01", "missing coordinates", "completeness", "High", _q01_missing_coordinates),
    Rule("Q02", "impossible coordinates", "validity", "Critical", _q02_impossible_coordinates),
    Rule("Q03", "malformed CrimeNo", "validity", "High", _q03_malformed_crimeno),
    Rule("Q04", "CrimeNo/Unit mismatch", "consistency", "High", _q04_crimeno_unit_mismatch),
    Rule("Q05", "incident after registration", "consistency", "High", _q05_incident_after_registration),
    Rule("Q06", "info received before incident", "consistency", "High", _q06_info_before_incident),
    Rule("Q07", "chargesheet before registration", "consistency", "Critical", _q07_chargesheet_before_registration),
    Rule("Q08", "arrest before incident", "consistency", "Critical", _q08_arrest_before_incident),
    Rule("Q09", "orphan child row", "integrity", "Critical", _q09_orphan_child_row),
    Rule("Q10", "broken lookup reference", "integrity", "High", _q10_broken_lookup_reference),
    Rule("Q11", "crime head / sub-head disagreement", "consistency", "Medium", _q11_head_subhead_disagreement),
    Rule("Q12", "duplicate case suspicion", "uniqueness", "Medium", _q12_duplicate_case_suspicion),
    Rule("Q13", "implausible age", "validity", "Medium", _q13_implausible_age),
    Rule("Q14", "accused with no PersonID", "completeness", "Low", _q14_accused_no_personid),
    Rule("Q15", "case with no charges", "completeness", "Medium", _q15_case_no_charges),
    Rule("Q16", "stale open case", "timeliness", "Medium", _q16_stale_open_case),
    Rule("Q17", "inactive act/section in use", "validity", "Medium", _q17_inactive_act_section),
    Rule("Q18", "empty BriefFacts", "completeness", "Low", _q18_empty_brief_facts),
]

RULES_BY_ID = {r.rule_id: r for r in RULES}
