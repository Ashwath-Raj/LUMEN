"""
Semantic repositories — the translation point required by §2 ("nothing
above `db/repositories/` ever references a table or column name") and
§28 structural rule 3 ("table and column names appear only in
`db/repositories/` and `db/models/`").

One repository per semantic entity (§2.1). Each repository is the only
place that queries a canonical ORM model (`db/models/canonical.py`) and
returns a `semantics/entities.py` dataclass — never a raw ORM row, never a
dict keyed by column name.

`Person` and `Insight` (§2.1) are backed by `lumen_person` and
`lumen_insight` (§3.6), which belong to entity resolution (§6, Session 7)
and the intelligence engine (§8-§11, Session 8). Session 2 does not
create those tables (see `db/models/canonical.py`'s module docstring), so
`PersonRepository` and `InsightRepository` below are present for
interface completeness (the entity vocabulary is closed, §2.1) but raise
`NotImplementedError` rather than querying a table that does not exist —
an honest gap, not a fabricated one.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from lumen.db.models import canonical as m
from lumen.semantics.entities import (
    Case,
    CaseParticipant,
    Charge,
    Court,
    CrimeType,
    Insight,
    Jurisdiction,
    Officer,
    Person,
    ProcessEvent,
    Station,
)


class CaseRepository:
    """Backed by `CaseMaster` (§3.5). Returns `Case` (§2.1) — the spine,
    always as an aggregate at the call sites that assemble children, never
    a bare row from this repository alone."""

    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, row: m.CaseMaster) -> Case:
        return Case(
            case_master_id=row.CaseMasterID,
            crime_no=row.CrimeNo,
            case_no=row.CaseNo,
            crime_registered_date=row.CrimeRegisteredDate,
            police_person_id=row.PolicePersonID,
            police_station_id=row.PoliceStationID,
            case_category_id=row.CaseCategoryID,
            gravity_offence_id=row.GravityOffenceID,
            crime_major_head_id=row.CrimeMajorHeadID,
            crime_minor_head_id=row.CrimeMinorHeadID,
            case_status_id=row.CaseStatusID,
            court_id=row.CourtID,
            incident_from_date=row.IncidentFromDate,
            incident_to_date=row.IncidentToDate,
            info_received_ps_date=row.InfoReceivedPSDate,
            latitude=float(row.latitude) if row.latitude is not None else None,
            longitude=float(row.longitude) if row.longitude is not None else None,
            brief_facts=row.BriefFacts,
        )

    def get(self, case_master_id: int) -> Case | None:
        row = self.session.get(m.CaseMaster, case_master_id)
        return self._to_entity(row) if row else None

    def list(self, *, limit: int = 50, offset: int = 0) -> list[Case]:
        rows = (
            self.session.query(m.CaseMaster)
            .order_by(m.CaseMaster.CaseMasterID)
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_entity(r) for r in rows]


class CaseParticipantRepository:
    """Backed by `Accused` | `Victim` | `ComplainantDetails` (§3.5).
    Returns `CaseParticipant` (§2.1) — a role in one case, not a human."""

    def __init__(self, session: Session):
        self.session = session

    def list_for_case(self, case_master_id: int) -> list[CaseParticipant]:
        participants: list[CaseParticipant] = []

        for row in self.session.query(m.Accused).filter_by(CaseMasterID=case_master_id).all():
            participants.append(
                CaseParticipant(
                    role="accused",
                    case_master_id=row.CaseMasterID,
                    accused_master_id=row.AccusedMasterID,
                    accused_name=row.AccusedName,
                    person_id_label=row.PersonID,
                    age_year=row.AgeYear,
                    gender_id=row.GenderID,
                )
            )

        for row in self.session.query(m.Victim).filter_by(CaseMasterID=case_master_id).all():
            participants.append(
                CaseParticipant(
                    role="victim",
                    case_master_id=row.CaseMasterID,
                    victim_master_id=row.VictimMasterID,
                    victim_name=row.VictimName,
                    victim_police=row.VictimPolice,
                    age_year=row.AgeYear,
                    gender_id=row.GenderID,
                )
            )

        for row in self.session.query(m.ComplainantDetails).filter_by(CaseMasterID=case_master_id).all():
            participants.append(
                CaseParticipant(
                    role="complainant",
                    case_master_id=row.CaseMasterID,
                    complainant_id=row.ComplainantID,
                    complainant_name=row.ComplainantName,
                    occupation_id=row.OccupationID,
                    religion_id=row.ReligionID,
                    caste_id=row.CasteID,
                    age_year=row.AgeYear,
                    gender_id=row.GenderID,
                )
            )

        return participants


class OfficerRepository:
    """Backed by `Employee` (§3.5). Returns `Officer` (§2.1) — registering
    officer and IO are both this."""

    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, row: m.Employee) -> Officer:
        return Officer(
            employee_id=row.EmployeeID,
            district_id=row.DistrictID,
            unit_id=row.UnitID,
            rank_id=row.RankID,
            designation_id=row.DesignationID,
            kgid=row.KGID,
            first_name=row.FirstName,
            appointment_date=row.AppointmentDate,
        )

    def get(self, employee_id: int) -> Officer | None:
        row = self.session.get(m.Employee, employee_id)
        return self._to_entity(row) if row else None


class StationRepository:
    """Backed by `Unit` where type = police station (§3.5). Returns
    `Station` (§2.1) — `Unit` hierarchy is flattened here."""

    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, row: m.Unit) -> Station:
        return Station(
            unit_id=row.UnitID,
            unit_name=row.UnitName,
            type_id=row.TypeID,
            parent_unit=row.ParentUnit,
            state_id=row.StateID,
            district_id=row.DistrictID,
        )

    def get(self, unit_id: int) -> Station | None:
        row = self.session.get(m.Unit, unit_id)
        return self._to_entity(row) if row else None


class JurisdictionRepository:
    """Backed by `District` / `State` (§3.5). Returns `Jurisdiction`
    (§2.1)."""

    def __init__(self, session: Session):
        self.session = session

    def get_district(self, district_id: int) -> Jurisdiction | None:
        row = self.session.get(m.District, district_id)
        if not row:
            return None
        return Jurisdiction(
            level="district",
            district_id=row.DistrictID,
            district_name=row.DistrictName,
            state_id=row.StateID,
        )

    def get_state(self, state_id: int) -> Jurisdiction | None:
        row = self.session.get(m.State, state_id)
        if not row:
            return None
        return Jurisdiction(level="state", state_id=row.StateID, state_name=row.StateName)


class CourtRepository:
    """Backed by `Court` (§3.5). Returns `Court` (§2.1)."""

    def __init__(self, session: Session):
        self.session = session

    def get(self, court_id: int) -> Court | None:
        row = self.session.get(m.Court, court_id)
        if not row:
            return None
        return Court(
            court_id=row.CourtID,
            court_name=row.CourtName,
            district_id=row.DistrictID,
            state_id=row.StateID,
        )


class ChargeRepository:
    """Backed by `ActSectionAssociation` + `Act` + `Section` (§3.5).
    Returns `Charge` (§2.1) — rendered as "IPC 302"."""

    def __init__(self, session: Session):
        self.session = session

    def list_for_case(self, case_master_id: int) -> list[Charge]:
        rows = (
            self.session.query(m.ActSectionAssociation)
            .filter_by(CaseMasterID=case_master_id)
            .all()
        )
        result: list[Charge] = []
        for row in rows:
            act = self.session.get(m.Act, row.ActID)
            section = None
            if act is not None:
                section = (
                    self.session.query(m.Section)
                    .filter_by(ActCode=row.ActID, SectionCode=row.SectionID)
                    .first()
                )
            result.append(
                Charge(
                    case_master_id=row.CaseMasterID,
                    act_id=row.ActID,
                    section_id=row.SectionID,
                    act_short_name=act.ShortName if act else None,
                    section_description=section.SectionDescription if section else None,
                )
            )
        return result


class CrimeTypeRepository:
    """Backed by `CrimeHead` + `CrimeSubHead` (§3.5). Returns `CrimeType`
    (§2.1) — two-level."""

    def __init__(self, session: Session):
        self.session = session

    def get(self, crime_head_id: int, crime_sub_head_id: int | None = None) -> CrimeType | None:
        head = self.session.get(m.CrimeHead, crime_head_id)
        if not head:
            return None
        sub_head_name = None
        if crime_sub_head_id is not None:
            sub = self.session.get(m.CrimeSubHead, crime_sub_head_id)
            sub_head_name = sub.CrimeHeadName if sub else None
        return CrimeType(
            crime_head_id=head.CrimeHeadID,
            crime_group_name=head.CrimeGroupName,
            crime_sub_head_id=crime_sub_head_id,
            crime_head_name=sub_head_name,
        )


class ProcessEventRepository:
    """Backed by `ArrestSurrender` | `ChargesheetDetails` | dated
    `CaseMaster` columns (§3.5). Returns `ProcessEvent` (§2.1) —
    everything on the timeline."""

    def __init__(self, session: Session):
        self.session = session

    def list_for_case(self, case_master_id: int) -> list[ProcessEvent]:
        events: list[ProcessEvent] = []

        case = self.session.get(m.CaseMaster, case_master_id)
        if case is not None:
            if case.IncidentFromDate is not None:
                events.append(
                    ProcessEvent(
                        event_id=f"case-{case_master_id}-incident",
                        case_master_id=case_master_id,
                        kind="incident",
                        occurred_at=case.IncidentFromDate,
                    )
                )
            if case.InfoReceivedPSDate is not None:
                events.append(
                    ProcessEvent(
                        event_id=f"case-{case_master_id}-info_received",
                        case_master_id=case_master_id,
                        kind="info_received",
                        occurred_at=case.InfoReceivedPSDate,
                    )
                )
            if case.CrimeRegisteredDate is not None:
                events.append(
                    ProcessEvent(
                        event_id=f"case-{case_master_id}-registered",
                        case_master_id=case_master_id,
                        kind="registered",
                        occurred_at=case.CrimeRegisteredDate,
                    )
                )

        for row in self.session.query(m.ArrestSurrender).filter_by(CaseMasterID=case_master_id).all():
            events.append(
                ProcessEvent(
                    event_id=f"arrest-{row.ArrestSurrenderID}",
                    case_master_id=case_master_id,
                    kind="arrest",
                    occurred_at=row.ArrestSurrenderDate,
                    arrest_surrender_id=row.ArrestSurrenderID,
                    ioid=row.IOID,
                )
            )

        for row in self.session.query(m.ChargesheetDetails).filter_by(CaseMasterID=case_master_id).all():
            events.append(
                ProcessEvent(
                    event_id=f"chargesheet-{row.CSID}",
                    case_master_id=case_master_id,
                    kind="chargesheet",
                    occurred_at=row.csdate,
                    csid=row.CSID,
                    cstype=row.cstype,
                )
            )

        return events


class PersonRepository:
    """Backed by `lumen_person` <- resolved `Accused` (§3.6). NOT
    implemented in Session 2 — entity resolution (§6) is Session 7's
    scope and `lumen_person` is not created by this session's schema
    work. Present for interface completeness against the closed §2.1
    vocabulary only."""

    def __init__(self, session: Session):
        self.session = session

    def get(self, person_id: str) -> Person | None:
        raise NotImplementedError(
            "Person is backed by lumen_person, which belongs to entity "
            "resolution (§6, Session 7). Not implemented in Session 2."
        )


class InsightRepository:
    """Backed by `lumen_insight` (§3.6). NOT implemented in Session 2 —
    the intelligence engine (§8-§11) is Session 8's scope and
    `lumen_insight` is not created by this session's schema work. Present
    for interface completeness against the closed §2.1 vocabulary only."""

    def __init__(self, session: Session):
        self.session = session

    def get(self, insight_id: str) -> Insight | None:
        raise NotImplementedError(
            "Insight is backed by lumen_insight, which belongs to the "
            "intelligence engine (§8-§11, Session 8). Not implemented in "
            "Session 2."
        )
