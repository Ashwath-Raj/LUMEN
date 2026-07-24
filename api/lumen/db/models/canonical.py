"""
Canonical data model — SQLAlchemy ORM mirror of `data/schema.sql`, which is
itself copied verbatim from LUMEN_MASTER_SPEC_V3.md §3.5.

Source of truth: the supplied "Police FIR System — ER Diagram" (§3.1),
adopted without modification. Table and column names are NOT "improved",
renamed, added to, or removed, per the spec's explicit instruction in §3.1
and the §33 Session 2 contract ("Do not rename tables. Do not rename
columns. Do not remove columns. Do not add columns.").

Known schema inconsistencies are handled, not silently fixed — see §3.3.
Each is called out at its point of occurrence below with the exact
handling the spec prescribes:

  - `ActSectionAssociation.ActID`/`SectionID` are declared VARCHAR here
    (not INT) per §3.3 row 1: "Store VARCHAR; note the coercion."
  - `Section`, `CrimeHeadActSection`, `ActSectionAssociation` have no
    declared single-column PK in the source ERD; §3.3 prescribes the
    composite primary keys used below.
  - `Victim.VictimPolice` is kept as VARCHAR(2) at the storage layer per
    §3.3 ("keep the type; expose boolean at the semantic layer") — the
    boolean exposure belongs to `semantics/`, not this file.
  - `Accused.PersonID` is VARCHAR ordering data (A1, A2, A3…), NOT an
    identity key — see §3.2 fact 2. Never joined on.
  - Every single-column integer primary key is declared `INT PRIMARY KEY`
    in §3.5's DDL, never `SERIAL`/`GENERATED ALWAYS AS IDENTITY`. These
    IDs originate in the source KSP system, not from a LUMEN-owned
    sequence, so every such column below is `autoincrement=False`.

Referenced-but-undefined entities (§3.4):
  - `Inv_OccuranceTime` is deliberately NOT created — `CaseMaster` already
    carries the occurrence columns (`IncidentFromDate`, `IncidentToDate`).
  - `inv_arrestsurrenderaccused` IS created, as the spec directs, as the
    junction table `(ArrestSurrenderID, AccusedMasterID)`.

This module defines ONLY the 26 canonical tables from §3.5. The `lumen_`
platform tables from §3.6 are out of scope for Session 2 (they belong to
the subsystems — identity resolution, intelligence, graph, quality,
knowledge base, registries, event store — that Session 2 explicitly must
not implement) and are not defined here.
"""
from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CHAR,
    Column,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
)

from lumen.db.session import Base


# ═══ GEOGRAPHY ═══

class State(Base):
    __tablename__ = "State"

    StateID = Column(Integer, primary_key=True, autoincrement=False)
    StateName = Column(String(120), nullable=False)
    NationalityID = Column(Integer)
    Active = Column(Boolean, default=True)


class District(Base):
    __tablename__ = "District"

    DistrictID = Column(Integer, primary_key=True, autoincrement=False)
    DistrictName = Column(String(120), nullable=False)
    StateID = Column(Integer, ForeignKey("State.StateID"))
    Active = Column(Boolean, default=True)


class Court(Base):
    __tablename__ = "Court"

    CourtID = Column(Integer, primary_key=True, autoincrement=False)
    CourtName = Column(String(200), nullable=False)
    DistrictID = Column(Integer, ForeignKey("District.DistrictID"))
    StateID = Column(Integer, ForeignKey("State.StateID"))
    Active = Column(Boolean, default=True)


# ═══ ORGANISATION ═══

class UnitType(Base):
    __tablename__ = "UnitType"

    UnitTypeID = Column(Integer, primary_key=True, autoincrement=False)
    UnitTypeName = Column(String(120))
    CityDistState = Column(String(20))
    Hierarchy = Column(Integer)
    Active = Column(Boolean, default=True)


class Unit(Base):
    __tablename__ = "Unit"

    UnitID = Column(Integer, primary_key=True, autoincrement=False)
    UnitName = Column(String(200), nullable=False)
    TypeID = Column(Integer, ForeignKey("UnitType.UnitTypeID"))
    ParentUnit = Column(Integer, ForeignKey("Unit.UnitID"))
    NationalityID = Column(Integer)
    StateID = Column(Integer, ForeignKey("State.StateID"))
    DistrictID = Column(Integer, ForeignKey("District.DistrictID"))
    Active = Column(Boolean, default=True)


class Rank(Base):
    __tablename__ = "Rank"

    RankID = Column(Integer, primary_key=True, autoincrement=False)
    RankName = Column(String(120))
    Hierarchy = Column(Integer)
    Active = Column(Boolean, default=True)


class Designation(Base):
    __tablename__ = "Designation"

    DesignationID = Column(Integer, primary_key=True, autoincrement=False)
    DesignationName = Column(String(120))
    Active = Column(Boolean, default=True)
    SortOrder = Column(Integer)


class Employee(Base):
    __tablename__ = "Employee"

    EmployeeID = Column(Integer, primary_key=True, autoincrement=False)
    DistrictID = Column(Integer, ForeignKey("District.DistrictID"))
    UnitID = Column(Integer, ForeignKey("Unit.UnitID"))
    RankID = Column(Integer, ForeignKey("Rank.RankID"))
    DesignationID = Column(Integer, ForeignKey("Designation.DesignationID"))
    KGID = Column(String(40))
    FirstName = Column(String(120))
    EmployeeDOB = Column(Date)
    GenderID = Column(Integer)
    BloodGroupID = Column(Integer)                # P9 — stored, never analysed
    PhysicallyChallenged = Column(Boolean)         # P9 — stored, never analysed
    AppointmentDate = Column(Date)


# ═══ LEGAL ═══

class Act(Base):
    __tablename__ = "Act"

    ActCode = Column(String(40), primary_key=True)
    ActDescription = Column(String(400))
    ShortName = Column(String(80))
    Active = Column(Boolean, default=True)


class Section(Base):
    __tablename__ = "Section"
    __table_args__ = (
        PrimaryKeyConstraint("ActCode", "SectionCode"),  # §3.3 — no declared PK in source
    )

    ActCode = Column(String(40), ForeignKey("Act.ActCode"))
    SectionCode = Column(String(40))
    SectionDescription = Column(String(600))
    Active = Column(Boolean, default=True)


class CrimeHead(Base):
    __tablename__ = "CrimeHead"

    CrimeHeadID = Column(Integer, primary_key=True, autoincrement=False)
    CrimeGroupName = Column(String(200))
    Active = Column(Boolean, default=True)


class CrimeSubHead(Base):
    __tablename__ = "CrimeSubHead"

    CrimeSubHeadID = Column(Integer, primary_key=True, autoincrement=False)
    CrimeHeadID = Column(Integer, ForeignKey("CrimeHead.CrimeHeadID"))
    CrimeHeadName = Column(String(200))
    SeqID = Column(Integer)


class CrimeHeadActSection(Base):
    __tablename__ = "CrimeHeadActSection"
    __table_args__ = (
        PrimaryKeyConstraint("CrimeHeadID", "ActCode", "SectionCode"),  # §3.3 — no declared PK
        ForeignKeyConstraint(["ActCode", "SectionCode"], ["Section.ActCode", "Section.SectionCode"]),
    )

    CrimeHeadID = Column(Integer, ForeignKey("CrimeHead.CrimeHeadID"))
    ActCode = Column(String(40))
    SectionCode = Column(String(40))


# ═══ LOOKUPS ═══

class CaseCategory(Base):
    __tablename__ = "CaseCategory"

    CaseCategoryID = Column(Integer, primary_key=True, autoincrement=False)
    LookupValue = Column(String(80))


class GravityOffence(Base):
    __tablename__ = "GravityOffence"

    GravityOffenceID = Column(Integer, primary_key=True, autoincrement=False)
    LookupValue = Column(String(80))


class CaseStatusMaster(Base):
    __tablename__ = "CaseStatusMaster"

    CaseStatusID = Column(Integer, primary_key=True, autoincrement=False)
    CaseStatusName = Column(String(120))


class CasteMaster(Base):
    __tablename__ = "CasteMaster"

    caste_master_id = Column(Integer, primary_key=True, autoincrement=False)
    caste_master_name = Column(String(120))


class ReligionMaster(Base):
    __tablename__ = "ReligionMaster"

    ReligionID = Column(Integer, primary_key=True, autoincrement=False)
    ReligionName = Column(String(120))


class OccupationMaster(Base):
    __tablename__ = "OccupationMaster"

    OccupationID = Column(Integer, primary_key=True, autoincrement=False)
    OccupationName = Column(String(120))


# ═══ CASE CORE ═══

class CaseMaster(Base):
    __tablename__ = "CaseMaster"
    __table_args__ = (
        Index("ix_case_geo", "latitude", "longitude"),
        Index("ix_case_date", "CrimeRegisteredDate"),
        Index("ix_case_unit", "PoliceStationID"),
        Index("ix_case_head", "CrimeMajorHeadID", "CrimeMinorHeadID"),
    )

    CaseMasterID = Column(Integer, primary_key=True, autoincrement=False)
    CrimeNo = Column(String(30), nullable=False)
    CaseNo = Column(String(20))
    CrimeRegisteredDate = Column(Date)
    PolicePersonID = Column(Integer, ForeignKey("Employee.EmployeeID"))
    PoliceStationID = Column(Integer, ForeignKey("Unit.UnitID"))
    CaseCategoryID = Column(Integer, ForeignKey("CaseCategory.CaseCategoryID"))
    GravityOffenceID = Column(Integer, ForeignKey("GravityOffence.GravityOffenceID"))
    CrimeMajorHeadID = Column(Integer, ForeignKey("CrimeHead.CrimeHeadID"))
    CrimeMinorHeadID = Column(Integer, ForeignKey("CrimeSubHead.CrimeSubHeadID"))
    CaseStatusID = Column(Integer, ForeignKey("CaseStatusMaster.CaseStatusID"))
    CourtID = Column(Integer, ForeignKey("Court.CourtID"))
    IncidentFromDate = Column(DateTime)
    IncidentToDate = Column(DateTime)
    InfoReceivedPSDate = Column(DateTime)
    latitude = Column(DECIMAL(10, 7))
    longitude = Column(DECIMAL(10, 7))
    BriefFacts = Column(Text)


class Victim(Base):
    __tablename__ = "Victim"

    VictimMasterID = Column(Integer, primary_key=True, autoincrement=False)
    CaseMasterID = Column(Integer, ForeignKey("CaseMaster.CaseMasterID"))
    VictimName = Column(String(200))
    AgeYear = Column(Integer)
    GenderID = Column(Integer)
    VictimPolice = Column(String(2))   # §3.3 — VARCHAR "1"/"0"; boolean exposed at semantic layer


class Accused(Base):
    __tablename__ = "Accused"

    AccusedMasterID = Column(Integer, primary_key=True, autoincrement=False)
    CaseMasterID = Column(Integer, ForeignKey("CaseMaster.CaseMasterID"))
    AccusedName = Column(String(200))
    AgeYear = Column(Integer)
    GenderID = Column(Integer)
    PersonID = Column(String(10))      # §3.2 fact 2 — ordering (A1, A2…), NOT identity. Never join on it.


class ComplainantDetails(Base):
    __tablename__ = "ComplainantDetails"

    ComplainantID = Column(Integer, primary_key=True, autoincrement=False)
    CaseMasterID = Column(Integer, ForeignKey("CaseMaster.CaseMasterID"))
    ComplainantName = Column(String(200))
    AgeYear = Column(Integer)
    OccupationID = Column(Integer, ForeignKey("OccupationMaster.OccupationID"))
    ReligionID = Column(Integer, ForeignKey("ReligionMaster.ReligionID"))    # P9
    CasteID = Column(Integer, ForeignKey("CasteMaster.caste_master_id"))    # P9
    GenderID = Column(Integer)


class ActSectionAssociation(Base):
    __tablename__ = "ActSectionAssociation"
    __table_args__ = (
        PrimaryKeyConstraint("CaseMasterID", "ActID", "SectionID"),  # §3.3 — no declared PK
    )

    CaseMasterID = Column(Integer, ForeignKey("CaseMaster.CaseMasterID"))
    ActID = Column(String(40))     # §3.3 row 1 — stored VARCHAR though source references Act.ActCode; coercion noted
    SectionID = Column(String(40))
    ActOrderID = Column(Integer)
    SectionOrderID = Column(Integer)


class ArrestSurrender(Base):
    __tablename__ = "ArrestSurrender"

    ArrestSurrenderID = Column(Integer, primary_key=True, autoincrement=False)
    CaseMasterID = Column(Integer, ForeignKey("CaseMaster.CaseMasterID"))
    ArrestSurrenderTypeID = Column(Integer)
    ArrestSurrenderDate = Column(Date)
    ArrestSurrenderStateId = Column(Integer, ForeignKey("State.StateID"))
    ArrestSurrenderDistrictId = Column(Integer, ForeignKey("District.DistrictID"))
    PoliceStationID = Column(Integer, ForeignKey("Unit.UnitID"))
    IOID = Column(Integer, ForeignKey("Employee.EmployeeID"))
    CourtID = Column(Integer, ForeignKey("Court.CourtID"))
    AccusedMasterID = Column(Integer, ForeignKey("Accused.AccusedMasterID"))
    IsAccused = Column(Boolean)
    IsComplainantAccused = Column(Boolean)


class InvArrestSurrenderAccused(Base):
    """§3.4 — referenced but undefined in the source ERD; created per the
    spec's explicit instruction: `(ArrestSurrenderID, AccusedMasterID)`."""

    __tablename__ = "inv_arrestsurrenderaccused"
    __table_args__ = (
        PrimaryKeyConstraint("ArrestSurrenderID", "AccusedMasterID"),
    )

    ArrestSurrenderID = Column(Integer, ForeignKey("ArrestSurrender.ArrestSurrenderID"))
    AccusedMasterID = Column(Integer, ForeignKey("Accused.AccusedMasterID"))


class ChargesheetDetails(Base):
    __tablename__ = "ChargesheetDetails"

    CSID = Column(Integer, primary_key=True, autoincrement=False)
    CaseMasterID = Column(Integer, ForeignKey("CaseMaster.CaseMasterID"))
    csdate = Column(DateTime)
    cstype = Column(CHAR(1))           # 'A' chargesheet / 'B' false / 'C' undetected — §3.2 fact 6
    PolicePersonID = Column(Integer, ForeignKey("Employee.EmployeeID"))
