"""
SQLAlchemy ORM Models — complete schema for all LUMEN entities.

All tables use String primary keys to match the existing in-memory IDs
(e.g., "case-77", "OP-7729") for zero-friction migration.

Relationships are expressed as JSON columns for now (avoids complex FK
cascades during migration). Proper FK constraints and relationships will
be added when the schema stabilises in a later migration.
"""
from __future__ import annotations

from sqlalchemy.orm import relationship
from sqlalchemy import (
    Float,
    Date,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.db.session import Base


# ── Operators / Auth ──────────────────────────────────────────────────────────

class OperatorORM(Base):
    __tablename__ = "operators"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)           # command | analyst | field
    clearance = Column(String, nullable=False)       # TS/SCI | SECRET | CONFIDENTIAL
    unit = Column(String, nullable=False)
    rank = Column(String, nullable=False)
    date_of_entry = Column(String, nullable=False)
    biometric_hash = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    operator_id = Column(String, nullable=False, unique=True)

    # Datathon ER Fields (Employee integration)
    kgid = Column(String, nullable=True, unique=True)
    first_name = Column(String, nullable=True)
    employee_dob = Column(DateTime(timezone=True), nullable=True)
    blood_group_id = Column(String, nullable=True)
    physically_challenged = Column(Boolean, nullable=True)
    
    district_id = Column(String, ForeignKey("districts.id"), nullable=True)
    unit_id = Column(String, ForeignKey("units.id"), nullable=True)
    rank_id = Column(String, ForeignKey("ranks.id"), nullable=True)
    designation_id = Column(String, ForeignKey("designations.id"), nullable=True)
   # external clearance ID
    assigned_unit = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ACTIVE")
    preferences = Column(JSON, nullable=True, default=dict)
    hashed_password = Column(String, nullable=True)             # bcrypt hash
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class RoleORM(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TokenBlacklistORM(Base):
    __tablename__ = "token_blacklist"

    jti = Column(String, primary_key=True, index=True)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())


class RefreshTokenORM(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, index=True)
    operator_id = Column(String, ForeignKey("operators.id"), nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Cases & Investigations ────────────────────────────────────────────────────

class CaseORM(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, index=True)
    label = Column(String, nullable=False)
    status = Column(String, nullable=False)         # ACTIVE | UNSOLVED | CLOSED
    updated_at = Column(String, nullable=False)     # human-readable label for UI
    evidence_count = Column(Integer, nullable=False, default=0)
    inspector = Column(String, nullable=True)
    timeline = Column(JSON, nullable=True, default=list)
    network = Column(JSON, nullable=True, default=dict)
    case_metadata = Column(JSON, nullable=True, default=dict)

    # Datathon ER Fields (CaseMaster integration)
    crime_no = Column(String, nullable=True) # 14 digit
    case_no = Column(String, nullable=True)  # 9 digit
    crime_registered_date = Column(DateTime(timezone=True), nullable=True)
    incident_from_date = Column(DateTime(timezone=True), nullable=True)
    incident_to_date = Column(DateTime(timezone=True), nullable=True)
    info_received_date = Column(DateTime(timezone=True), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    brief_facts = Column(Text, nullable=True)
    
    # Foreign Keys to new ER models
    police_person_id = Column(String, ForeignKey("employees.id"), nullable=True)
    police_station_id = Column(String, ForeignKey("units.id"), nullable=True)
    case_category_id = Column(String, ForeignKey("case_categories.id"), nullable=True)
    gravity_offence_id = Column(String, ForeignKey("gravity_offences.id"), nullable=True)
    crime_major_head_id = Column(String, ForeignKey("crime_heads.id"), nullable=True)
    crime_minor_head_id = Column(String, ForeignKey("crime_sub_heads.id"), nullable=True)
    case_status_id = Column(String, ForeignKey("case_status_master.id"), nullable=True)
    court_id = Column(String, ForeignKey("courts.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InvestigationORM(Base):
    __tablename__ = "investigations"

    id = Column(String, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InvestigationReportORM(Base):
    __tablename__ = "investigation_reports"

    id = Column(String, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=True)
    date = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── FIRs ──────────────────────────────────────────────────────────────────────

class FIRORM(Base):
    __tablename__ = "firs"

    id = Column(String, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, index=True)
    fir_number = Column(String, nullable=False, unique=True)
    district = Column(String, nullable=False)
    year = Column(String, nullable=False)
    document = Column(JSON, nullable=True, default=dict)
    extracted_entities = Column(JSON, nullable=True, default=list)
    linked_network = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Suspects & Victims ────────────────────────────────────────────────────────

class SuspectORM(Base):
    __tablename__ = "suspects"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)           # Primary Suspect | Person of Interest
    tags = Column(JSON, nullable=True, default=list)
    last_known_location = Column(String, nullable=True)
    risk_level = Column(String, nullable=True)
    case_status = Column(String, nullable=True)
    associated_entities = Column(Integer, nullable=True, default=0)
    linked_case = Column(String, nullable=True)
    dob = Column(String, nullable=True)
    last_sighting = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WatchlistEntryORM(Base):
    __tablename__ = "watchlist"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    risk_level = Column(String, nullable=False)
    last_seen = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VictimORM(Base):
    __tablename__ = "victims"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    case_id = Column(String, ForeignKey("cases.id"), nullable=True, index=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # ER Fields
    case_master_id = Column(String, ForeignKey("cases.id"), nullable=True)
    age_year = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    is_police = Column(Boolean, nullable=True)


# ── Evidence ──────────────────────────────────────────────────────────────────

class EvidenceORM(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, index=True)
    item_id = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    serial_no = Column(String, nullable=False)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Interviews & Forensics ────────────────────────────────────────────────────

class InterviewORM(Base):
    __tablename__ = "interviews"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    case_id = Column(String, ForeignKey("cases.id"), nullable=True, index=True)
    status = Column(String, nullable=True, default="ACTIVE ANALYSIS")
    lines = Column(JSON, nullable=True, default=list)
    extracted_entities = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DeviceForensicsORM(Base):
    __tablename__ = "device_forensics"

    id = Column(String, primary_key=True, index=True)
    label = Column(String, nullable=False)
    decryption_progress = Column(Integer, nullable=True, default=0)
    signal = Column(String, nullable=True)
    gps_data = Column(String, nullable=True)
    technical_summary = Column(Text, nullable=True)
    data_packets = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FieldReportORM(Base):
    __tablename__ = "field_reports"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    case_id = Column(String, ForeignKey("cases.id"), nullable=True, index=True)
    officer = Column(String, nullable=True)
    submitted_at = Column(String, nullable=True)
    location = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    photos = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Geospatial ────────────────────────────────────────────────────────────────

class HotspotORM(Base):
    __tablename__ = "hotspots"

    id = Column(String, primary_key=True, index=True)
    label = Column(String, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    intensity = Column(String, nullable=False)   # critical | high | moderate | low
    probability = Column(Integer, nullable=True)
    incidents = Column(Integer, nullable=True)
    window_hours = Column(Integer, nullable=True, default=72)
    hotspot_type = Column(String, nullable=True, default="crime")  # crime | theatre
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Intelligence ──────────────────────────────────────────────────────────────

class IntelligenceReportORM(Base):
    __tablename__ = "intelligence_reports"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    report_type = Column(String, nullable=True)
    confidence = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IntelligenceLeadCaseORM(Base):
    __tablename__ = "intelligence_lead_cases"
    intelligence_lead_id = Column(String, ForeignKey("intelligence_leads.id", ondelete="CASCADE"), primary_key=True, index=True)
    case_id = Column(String, ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True, index=True)

class IntelligenceLeadORM(Base):
    __tablename__ = "intelligence_leads"

    id = Column(String, primary_key=True, index=True)
    priority = Column(String, nullable=False)           # HIGH PRIORITY | MODERATE | LOW
    priority_tone = Column(String, nullable=False)      # critical | warning | neutral
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    source_cases = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    formal_cases = relationship("CaseORM", secondary="intelligence_lead_cases", lazy="select")


class SignalInterceptORM(Base):
    __tablename__ = "signal_intercepts"

    id = Column(String, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=True, index=True)
    source = Column(String, nullable=False)
    frequency = Column(String, nullable=True)
    timestamp = Column(String, nullable=False)
    linked_case = Column(String, nullable=True)
    confidence = Column(Integer, nullable=True)
    tone = Column(String, nullable=False, default="neutral")
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Operations ────────────────────────────────────────────────────────────────

class OfficerORM(Base):
    __tablename__ = "officers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IncidentORM(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, index=True)
    priority = Column(String, nullable=False)       # CRITICAL | HIGH | ROUTINE
    timestamp = Column(String, nullable=False)
    title = Column(String, nullable=False)
    zone = Column(String, nullable=True)
    required_team = Column(String, nullable=True)
    assignment = Column(String, nullable=True, default="UNASSIGNED")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CoordinationLogORM(Base):
    __tablename__ = "coordination_logs"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(String, nullable=False)
    message = Column(String, nullable=False)
    detail = Column(String, nullable=True)
    tone = Column(String, nullable=False, default="neutral")  # critical | warning | success | neutral
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OperationORM(Base):
    __tablename__ = "operations"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    operation_metadata = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Personnel (Analytics Module) ──────────────────────────────────────────────

class PersonnelORM(Base):
    __tablename__ = "personnel"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Administration ────────────────────────────────────────────────────────────

class AlertORM(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, index=True)
    alert_id = Column(String, nullable=True, unique=True)   # e.g. "ALRT-4471"
    timestamp = Column(String, nullable=False)
    message = Column(String, nullable=False)
    detail = Column(Text, nullable=True)
    tone = Column(String, nullable=False, default="neutral")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLogORM(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=True)
    timestamp = Column(String, nullable=False)
    detail = Column(Text, nullable=True)
    tone = Column(String, nullable=False, default="neutral")
    origin = Column(String, nullable=True)
    actor = Column(String, nullable=True)
    action = Column(String, nullable=True)
    details = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Personnel Roster (Administration Module) ──────────────────────────────────

class PersonnelRosterORM(Base):
    __tablename__ = "personnel_roster"

    id = Column(String, primary_key=True, index=True)
    operative_id = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    designation = Column(String, nullable=True)
    clearance = Column(String, nullable=True)
    assignment = Column(String, nullable=True)
    last_authenticated = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ---------------------------------------------------------
# Datathon ER Diagram Formal Models
# ---------------------------------------------------------

# Hierarchy & Admin
class StateORM(Base):
    __tablename__ = "states"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    nationality_id = Column(String, nullable=True)
    active = Column(Boolean, default=True)

class PoliceRangeORM(Base):
    __tablename__ = "police_ranges"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    state_id = Column(String, ForeignKey("states.id"), nullable=True)

class CommissionerateORM(Base):
    __tablename__ = "commissionerates"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    state_id = Column(String, ForeignKey("states.id"), nullable=True)

class DistrictORM(Base):
    __tablename__ = "districts"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    state_id = Column(String, ForeignKey("states.id"), nullable=True)
    range_id = Column(String, ForeignKey("police_ranges.id"), nullable=True)
    commissionerate_id = Column(String, ForeignKey("commissionerates.id"), nullable=True)
    active = Column(Boolean, default=True)

class UnitTypeORM(Base):
    __tablename__ = "unit_types"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    city_dist_state = Column(String, nullable=True)

class UnitORM(Base):
    __tablename__ = "units"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type_id = Column(String, ForeignKey("unit_types.id"), nullable=True)
    parent_unit = Column(String, ForeignKey("units.id"), nullable=True)
    state_id = Column(String, ForeignKey("states.id"), nullable=True)
    district_id = Column(String, ForeignKey("districts.id"), nullable=True)
    active = Column(Boolean, default=True)

class CourtORM(Base):
    __tablename__ = "courts"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    district_id = Column(String, ForeignKey("districts.id"), nullable=True)
    state_id = Column(String, ForeignKey("states.id"), nullable=True)
    active = Column(Boolean, default=True)

# Master Data Lookups
class CaseCategoryORM(Base):
    __tablename__ = "case_categories"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False) # FIR, UDR, PAR

class GravityOffenceORM(Base):
    __tablename__ = "gravity_offences"
    id = Column(String, primary_key=True, index=True)
    lookup_value = Column(String, nullable=False) # Heinous, Non-Heinous

class CaseStatusMasterORM(Base):
    __tablename__ = "case_status_master"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)

class RankORM(Base):
    __tablename__ = "ranks"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    hierarchy = Column(Integer, nullable=True)
    active = Column(Boolean, default=True)

class DesignationORM(Base):
    __tablename__ = "designations"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sort_order = Column(Integer, nullable=True)
    active = Column(Boolean, default=True)

class CasteMasterORM(Base):
    __tablename__ = "caste_master"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)

class ReligionMasterORM(Base):
    __tablename__ = "religion_master"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)

class OccupationMasterORM(Base):
    __tablename__ = "occupation_master"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)

# Employees
class EmployeeORM(Base):
    __tablename__ = "employees"
    id = Column(String, primary_key=True, index=True)
    kgid = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    district_id = Column(String, ForeignKey("districts.id"), nullable=True)
    unit_id = Column(String, ForeignKey("units.id"), nullable=True)
    rank_id = Column(String, ForeignKey("ranks.id"), nullable=True)
    designation_id = Column(String, ForeignKey("designations.id"), nullable=True)

# Crime Classification
class ActORM(Base):
    __tablename__ = "acts"
    id = Column(String, primary_key=True, index=True)
    description = Column(String, nullable=True)
    short_name = Column(String, nullable=True)
    active = Column(Boolean, default=True)

class SectionORM(Base):
    __tablename__ = "sections"
    id = Column(String, primary_key=True, index=True)
    act_code = Column(String, ForeignKey("acts.id"), nullable=True)
    section_code = Column(String, nullable=False)
    description = Column(String, nullable=True)
    active = Column(Boolean, default=True)

class CrimeHeadORM(Base):
    __tablename__ = "crime_heads"
    id = Column(String, primary_key=True, index=True)
    group_name = Column(String, nullable=False)
    active = Column(Boolean, default=True)

class CrimeSubHeadORM(Base):
    __tablename__ = "crime_sub_heads"
    id = Column(String, primary_key=True, index=True)
    head_id = Column(String, ForeignKey("crime_heads.id"), nullable=True)
    name = Column(String, nullable=False)
    seq_id = Column(Integer, nullable=True)

class CrimeHeadActSectionORM(Base):
    __tablename__ = "crime_head_act_sections"
    id = Column(String, primary_key=True, index=True)
    crime_head_id = Column(String, ForeignKey("crime_heads.id"), nullable=True)
    act_code = Column(String, ForeignKey("acts.id"), nullable=True)
    section_code = Column(String, ForeignKey("sections.id"), nullable=True)

class ActSectionAssociationORM(Base):
    __tablename__ = "act_section_associations"
    id = Column(String, primary_key=True, index=True)
    case_master_id = Column(String, ForeignKey("cases.id"), nullable=True)
    act_id = Column(String, ForeignKey("acts.id"), nullable=True)
    section_id = Column(String, ForeignKey("sections.id"), nullable=True)
    act_order_id = Column(Integer, nullable=True)
    section_order_id = Column(Integer, nullable=True)

# Participants
class ComplainantDetailsORM(Base):
    __tablename__ = "complainant_details"
    id = Column(String, primary_key=True, index=True)
    case_master_id = Column(String, ForeignKey("cases.id"), nullable=True)
    name = Column(String, nullable=False)
    age_year = Column(Integer, nullable=True)
    occupation_id = Column(String, ForeignKey("occupation_master.id"), nullable=True)
    religion_id = Column(String, ForeignKey("religion_master.id"), nullable=True)
    caste_id = Column(String, ForeignKey("caste_master.id"), nullable=True)
    gender = Column(String, nullable=True)



class AccusedORM(Base):
    __tablename__ = "accused"
    id = Column(String, primary_key=True, index=True)
    case_master_id = Column(String, ForeignKey("cases.id"), nullable=True)
    name = Column(String, nullable=False)
    age_year = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    person_sorting = Column(String, nullable=True)

class WitnessORM(Base):
    __tablename__ = "witnesses"
    id = Column(String, primary_key=True, index=True)
    case_master_id = Column(String, ForeignKey("cases.id"), nullable=True)
    name = Column(String, nullable=False)

# Procedural Events
class ArrestSurrenderORM(Base):
    __tablename__ = "arrest_surrenders"
    id = Column(String, primary_key=True, index=True)
    case_master_id = Column(String, ForeignKey("cases.id"), nullable=True)
    event_type = Column(String, nullable=True) # Arrest / Surrender
    event_date = Column(DateTime(timezone=True), nullable=True)
    state_id = Column(String, ForeignKey("states.id"), nullable=True)
    district_id = Column(String, ForeignKey("districts.id"), nullable=True)
    police_station_id = Column(String, ForeignKey("units.id"), nullable=True)
    io_id = Column(String, ForeignKey("employees.id"), nullable=True)
    court_id = Column(String, ForeignKey("courts.id"), nullable=True)

class ArrestSurrenderAccusedORM(Base):
    __tablename__ = "arrest_surrender_accused"
    id = Column(String, primary_key=True, index=True)
    arrest_surrender_id = Column(String, ForeignKey("arrest_surrenders.id"), nullable=True)
    accused_id = Column(String, ForeignKey("accused.id"), nullable=True)
    is_accused = Column(Boolean, nullable=True)
    is_complainant_accused = Column(Boolean, nullable=True)

class ChargesheetDetailsORM(Base):
    __tablename__ = "chargesheet_details"
    id = Column(String, primary_key=True, index=True)
    case_master_id = Column(String, ForeignKey("cases.id"), nullable=True)
    cs_date = Column(DateTime(timezone=True), nullable=True)
    cs_type = Column(String, nullable=True) # Chargesheet, False Case, Undetected
    police_person_id = Column(String, ForeignKey("employees.id"), nullable=True)

class PropertyORM(Base):
    __tablename__ = "properties"
    id = Column(String, primary_key=True, index=True)
    case_master_id = Column(String, ForeignKey("cases.id"), nullable=True)
    description = Column(String, nullable=True)

class EvidenceDetailsORM(Base):
    __tablename__ = "evidence_details"
    id = Column(String, primary_key=True, index=True)
    case_master_id = Column(String, ForeignKey("cases.id"), nullable=True)
    description = Column(String, nullable=True)

class VehicleORM(Base):
    __tablename__ = "vehicles"
    id = Column(String, primary_key=True, index=True)
    case_master_id = Column(String, ForeignKey("cases.id"), nullable=True)
    registration_no = Column(String, nullable=True)

# ---------------------------------------------------------
# Specialized Command Models (Phase 11)
# ---------------------------------------------------------

class DepartmentORM(Base):
    __tablename__ = "departments"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True, index=True)
    description = Column(String, nullable=True)
    state_id = Column(String, ForeignKey("states.id"), nullable=False)
    department_type = Column(String, nullable=False) # e.g. 'Intelligence & Security', 'Investigation'
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class SpecializedUnitORM(Base):
    __tablename__ = "specialized_units"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True, index=True)
    description = Column(String, nullable=True)
    department_id = Column(String, ForeignKey("departments.id"), nullable=False)
    unit_type = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

