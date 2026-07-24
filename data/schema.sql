-- LUMEN canonical data model — copied verbatim from LUMEN_MASTER_SPEC_V3.md §3.5.
-- Source of truth: the supplied "Police FIR System — ER Diagram" (§3.1), adopted
-- without modification. PostgreSQL types shown for local development; Data Store
-- mapping notes are in §26.2 of the spec. Do not "improve" column or key names.
--
-- Known schema inconsistencies are handled, not silently fixed — see §3.3 and
-- docs/SCHEMA_NOTES.md. Two referenced-but-undefined entities are addressed per
-- §3.4: Inv_OccuranceTime is NOT created (CaseMaster already carries occurrence
-- columns); inv_arrestsurrenderaccused IS created (junction table, defined below).

-- ═══ GEOGRAPHY ═══
CREATE TABLE State (StateID INT PRIMARY KEY, StateName VARCHAR(120) NOT NULL,
  NationalityID INT, Active BOOLEAN DEFAULT TRUE);

CREATE TABLE District (DistrictID INT PRIMARY KEY, DistrictName VARCHAR(120) NOT NULL,
  StateID INT REFERENCES State(StateID), Active BOOLEAN DEFAULT TRUE);

CREATE TABLE Court (CourtID INT PRIMARY KEY, CourtName VARCHAR(200) NOT NULL,
  DistrictID INT REFERENCES District(DistrictID),
  StateID INT REFERENCES State(StateID), Active BOOLEAN DEFAULT TRUE);

-- ═══ ORGANISATION ═══
CREATE TABLE UnitType (UnitTypeID INT PRIMARY KEY, UnitTypeName VARCHAR(120),
  CityDistState VARCHAR(20), Hierarchy INT, Active BOOLEAN DEFAULT TRUE);

CREATE TABLE Unit (UnitID INT PRIMARY KEY, UnitName VARCHAR(200) NOT NULL,
  TypeID INT REFERENCES UnitType(UnitTypeID),
  ParentUnit INT REFERENCES Unit(UnitID), NationalityID INT,
  StateID INT REFERENCES State(StateID),
  DistrictID INT REFERENCES District(DistrictID), Active BOOLEAN DEFAULT TRUE);

CREATE TABLE Rank (RankID INT PRIMARY KEY, RankName VARCHAR(120),
  Hierarchy INT, Active BOOLEAN DEFAULT TRUE);

CREATE TABLE Designation (DesignationID INT PRIMARY KEY, DesignationName VARCHAR(120),
  Active BOOLEAN DEFAULT TRUE, SortOrder INT);

CREATE TABLE Employee (EmployeeID INT PRIMARY KEY,
  DistrictID INT REFERENCES District(DistrictID),
  UnitID INT REFERENCES Unit(UnitID),
  RankID INT REFERENCES Rank(RankID),
  DesignationID INT REFERENCES Designation(DesignationID),
  KGID VARCHAR(40), FirstName VARCHAR(120), EmployeeDOB DATE,
  GenderID INT, BloodGroupID INT,            -- P9
  PhysicallyChallenged BOOLEAN,              -- P9
  AppointmentDate DATE);

-- ═══ LEGAL ═══
CREATE TABLE Act (ActCode VARCHAR(40) PRIMARY KEY, ActDescription VARCHAR(400),
  ShortName VARCHAR(80), Active BOOLEAN DEFAULT TRUE);

CREATE TABLE Section (ActCode VARCHAR(40) REFERENCES Act(ActCode),
  SectionCode VARCHAR(40), SectionDescription VARCHAR(600),
  Active BOOLEAN DEFAULT TRUE, PRIMARY KEY (ActCode, SectionCode));

CREATE TABLE CrimeHead (CrimeHeadID INT PRIMARY KEY,
  CrimeGroupName VARCHAR(200), Active BOOLEAN DEFAULT TRUE);

CREATE TABLE CrimeSubHead (CrimeSubHeadID INT PRIMARY KEY,
  CrimeHeadID INT REFERENCES CrimeHead(CrimeHeadID),
  CrimeHeadName VARCHAR(200), SeqID INT);

CREATE TABLE CrimeHeadActSection (
  CrimeHeadID INT REFERENCES CrimeHead(CrimeHeadID),
  ActCode VARCHAR(40), SectionCode VARCHAR(40),
  PRIMARY KEY (CrimeHeadID, ActCode, SectionCode),
  FOREIGN KEY (ActCode, SectionCode) REFERENCES Section(ActCode, SectionCode));

-- ═══ LOOKUPS ═══
CREATE TABLE CaseCategory (CaseCategoryID INT PRIMARY KEY, LookupValue VARCHAR(80));
CREATE TABLE GravityOffence (GravityOffenceID INT PRIMARY KEY, LookupValue VARCHAR(80));
CREATE TABLE CaseStatusMaster (CaseStatusID INT PRIMARY KEY, CaseStatusName VARCHAR(120));
CREATE TABLE CasteMaster (caste_master_id INT PRIMARY KEY, caste_master_name VARCHAR(120));
CREATE TABLE ReligionMaster (ReligionID INT PRIMARY KEY, ReligionName VARCHAR(120));
CREATE TABLE OccupationMaster (OccupationID INT PRIMARY KEY, OccupationName VARCHAR(120));

-- ═══ CASE CORE ═══
CREATE TABLE CaseMaster (
  CaseMasterID INT PRIMARY KEY,
  CrimeNo VARCHAR(30) NOT NULL, CaseNo VARCHAR(20),
  CrimeRegisteredDate DATE,
  PolicePersonID INT REFERENCES Employee(EmployeeID),
  PoliceStationID INT REFERENCES Unit(UnitID),
  CaseCategoryID INT REFERENCES CaseCategory(CaseCategoryID),
  GravityOffenceID INT REFERENCES GravityOffence(GravityOffenceID),
  CrimeMajorHeadID INT REFERENCES CrimeHead(CrimeHeadID),
  CrimeMinorHeadID INT REFERENCES CrimeSubHead(CrimeSubHeadID),
  CaseStatusID INT REFERENCES CaseStatusMaster(CaseStatusID),
  CourtID INT REFERENCES Court(CourtID),
  IncidentFromDate TIMESTAMP, IncidentToDate TIMESTAMP, InfoReceivedPSDate TIMESTAMP,
  latitude DECIMAL(10,7), longitude DECIMAL(10,7),
  BriefFacts TEXT);

CREATE INDEX ix_case_geo  ON CaseMaster(latitude, longitude);
CREATE INDEX ix_case_date ON CaseMaster(CrimeRegisteredDate);
CREATE INDEX ix_case_unit ON CaseMaster(PoliceStationID);
CREATE INDEX ix_case_head ON CaseMaster(CrimeMajorHeadID, CrimeMinorHeadID);

CREATE TABLE Victim (VictimMasterID INT PRIMARY KEY,
  CaseMasterID INT REFERENCES CaseMaster(CaseMasterID),
  VictimName VARCHAR(200), AgeYear INT, GenderID INT, VictimPolice VARCHAR(2));

CREATE TABLE Accused (AccusedMasterID INT PRIMARY KEY,
  CaseMasterID INT REFERENCES CaseMaster(CaseMasterID),
  AccusedName VARCHAR(200), AgeYear INT, GenderID INT,
  PersonID VARCHAR(10));                     -- ordering, NOT identity

CREATE TABLE ComplainantDetails (ComplainantID INT PRIMARY KEY,
  CaseMasterID INT REFERENCES CaseMaster(CaseMasterID),
  ComplainantName VARCHAR(200), AgeYear INT,
  OccupationID INT REFERENCES OccupationMaster(OccupationID),
  ReligionID INT REFERENCES ReligionMaster(ReligionID),          -- P9
  CasteID INT REFERENCES CasteMaster(caste_master_id),           -- P9
  GenderID INT);

CREATE TABLE ActSectionAssociation (
  CaseMasterID INT REFERENCES CaseMaster(CaseMasterID),
  ActID VARCHAR(40), SectionID VARCHAR(40),
  ActOrderID INT, SectionOrderID INT,
  PRIMARY KEY (CaseMasterID, ActID, SectionID));

CREATE TABLE ArrestSurrender (ArrestSurrenderID INT PRIMARY KEY,
  CaseMasterID INT REFERENCES CaseMaster(CaseMasterID),
  ArrestSurrenderTypeID INT, ArrestSurrenderDate DATE,
  ArrestSurrenderStateId INT REFERENCES State(StateID),
  ArrestSurrenderDistrictId INT REFERENCES District(DistrictID),
  PoliceStationID INT REFERENCES Unit(UnitID),
  IOID INT REFERENCES Employee(EmployeeID),
  CourtID INT REFERENCES Court(CourtID),
  AccusedMasterID INT REFERENCES Accused(AccusedMasterID),
  IsAccused BOOLEAN, IsComplainantAccused BOOLEAN);

CREATE TABLE inv_arrestsurrenderaccused (
  ArrestSurrenderID INT REFERENCES ArrestSurrender(ArrestSurrenderID),
  AccusedMasterID INT REFERENCES Accused(AccusedMasterID),
  PRIMARY KEY (ArrestSurrenderID, AccusedMasterID));

CREATE TABLE ChargesheetDetails (CSID INT PRIMARY KEY,
  CaseMasterID INT REFERENCES CaseMaster(CaseMasterID),
  csdate TIMESTAMP, cstype CHAR(1),
  PolicePersonID INT REFERENCES Employee(EmployeeID));

-- ═══ LUMEN-owned tables (§3.6) — NOT part of this file ═══
-- Every lumen_ table is prefixed, keyed to canonical IDs above, and never
-- duplicates a canonical column. See LUMEN_MASTER_SPEC_V3.md §3.6 for the
-- full list (lumen_person, lumen_insight, lumen_graph_edge, lumen_hotspot,
-- lumen_kb_document, lumen_quality_finding, lumen_event, lumen_audit, etc.).
-- Not yet implemented as DDL — this file currently holds only the canonical
-- (non-LUMEN) schema per the migration's "don't invent, don't implement" scope.
