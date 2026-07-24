import os

def rewrite_models():
    models_path = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN\backend\app\db\models.py"
    
    with open(models_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Append new imports if missing
    if "from sqlalchemy import Float" not in content:
        content = content.replace("from sqlalchemy import (", "from sqlalchemy import (\n    Float,\n    Date,")
    
    # Inject into CaseORM
    case_orm_injection = """
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
"""
    if "crime_no = Column" not in content:
        content = content.replace("case_metadata = Column(JSON, nullable=True, default=dict)", 
                                  "case_metadata = Column(JSON, nullable=True, default=dict)\n" + case_orm_injection)

    # Inject into OperatorORM
    operator_orm_injection = """
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
"""
    if "kgid = Column" not in content:
        content = content.replace("operator_id = Column(String, nullable=False, unique=True)",
                                  "operator_id = Column(String, nullable=False, unique=True)\n" + operator_orm_injection)

    # Now append the new ORM classes
    new_orms = """
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

class VictimORM(Base):
    __tablename__ = "victims"
    id = Column(String, primary_key=True, index=True)
    case_master_id = Column(String, ForeignKey("cases.id"), nullable=True)
    name = Column(String, nullable=False)
    age_year = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    is_police = Column(Boolean, nullable=True)

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
"""
    if "class StateORM(Base):" not in content:
        content += new_orms
        
    with open(models_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Database models successfully rewritten.")

if __name__ == "__main__":
    rewrite_models()
