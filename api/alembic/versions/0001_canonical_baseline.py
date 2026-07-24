"""canonical baseline — LUMEN v3 schema (§3.5 / §3.6)

Creates the full LUMEN v3 database schema in one baseline migration:
  * 27 official KSP canonical tables (§3.5) + inv_arrestsurrenderaccused (§3.4)
  * lumen_person / lumen_person_link / lumen_person_dispute — identity (§3.6, §6)
  * lumen_quality_finding / lumen_quality_score — data quality (§3.6, §5)

This replaces the deleted legacy-prototype migration chain. The DDL is the
authoritative source of the schema: `alembic upgrade head` on an empty database
produces exactly the ORM metadata in lumen/db/models/. Tables are created in
foreign-key dependency order; indexes follow.

Revision ID: 0001_canonical_baseline
Revises:
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_canonical_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Tables (foreign-key dependency order) ────────────────────────────
    op.create_table('Act',
    sa.Column('ActCode', sa.String(length=40), nullable=False),
    sa.Column('ActDescription', sa.String(length=400), nullable=True),
    sa.Column('ShortName', sa.String(length=80), nullable=True),
    sa.Column('Active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('ActCode', name=op.f('pk_Act'))
    )
    op.create_table('CaseCategory',
    sa.Column('CaseCategoryID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('LookupValue', sa.String(length=80), nullable=True),
    sa.PrimaryKeyConstraint('CaseCategoryID', name=op.f('pk_CaseCategory'))
    )
    op.create_table('CaseStatusMaster',
    sa.Column('CaseStatusID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('CaseStatusName', sa.String(length=120), nullable=True),
    sa.PrimaryKeyConstraint('CaseStatusID', name=op.f('pk_CaseStatusMaster'))
    )
    op.create_table('CasteMaster',
    sa.Column('caste_master_id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('caste_master_name', sa.String(length=120), nullable=True),
    sa.PrimaryKeyConstraint('caste_master_id', name=op.f('pk_CasteMaster'))
    )
    op.create_table('CrimeHead',
    sa.Column('CrimeHeadID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('CrimeGroupName', sa.String(length=200), nullable=True),
    sa.Column('Active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('CrimeHeadID', name=op.f('pk_CrimeHead'))
    )
    op.create_table('Designation',
    sa.Column('DesignationID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('DesignationName', sa.String(length=120), nullable=True),
    sa.Column('Active', sa.Boolean(), nullable=True),
    sa.Column('SortOrder', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('DesignationID', name=op.f('pk_Designation'))
    )
    op.create_table('GravityOffence',
    sa.Column('GravityOffenceID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('LookupValue', sa.String(length=80), nullable=True),
    sa.PrimaryKeyConstraint('GravityOffenceID', name=op.f('pk_GravityOffence'))
    )
    op.create_table('OccupationMaster',
    sa.Column('OccupationID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('OccupationName', sa.String(length=120), nullable=True),
    sa.PrimaryKeyConstraint('OccupationID', name=op.f('pk_OccupationMaster'))
    )
    op.create_table('Rank',
    sa.Column('RankID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('RankName', sa.String(length=120), nullable=True),
    sa.Column('Hierarchy', sa.Integer(), nullable=True),
    sa.Column('Active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('RankID', name=op.f('pk_Rank'))
    )
    op.create_table('ReligionMaster',
    sa.Column('ReligionID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('ReligionName', sa.String(length=120), nullable=True),
    sa.PrimaryKeyConstraint('ReligionID', name=op.f('pk_ReligionMaster'))
    )
    op.create_table('State',
    sa.Column('StateID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('StateName', sa.String(length=120), nullable=False),
    sa.Column('NationalityID', sa.Integer(), nullable=True),
    sa.Column('Active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('StateID', name=op.f('pk_State'))
    )
    op.create_table('UnitType',
    sa.Column('UnitTypeID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('UnitTypeName', sa.String(length=120), nullable=True),
    sa.Column('CityDistState', sa.String(length=20), nullable=True),
    sa.Column('Hierarchy', sa.Integer(), nullable=True),
    sa.Column('Active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('UnitTypeID', name=op.f('pk_UnitType'))
    )
    op.create_table('lumen_person',
    sa.Column('person_id', sa.String(length=36), nullable=False),
    sa.Column('canonical_name', sa.String(length=200), nullable=True),
    sa.Column('first_seen', sa.DateTime(), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.Column('case_count', sa.Integer(), nullable=True),
    sa.Column('district_count', sa.Integer(), nullable=True),
    sa.Column('resolution_confidence', sa.Float(), nullable=True),
    sa.Column('method_version', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('person_id', name=op.f('pk_lumen_person'))
    )
    op.create_table('lumen_quality_finding',
    sa.Column('finding_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('rule_id', sa.String(length=10), nullable=True),
    sa.Column('severity', sa.String(length=20), nullable=True),
    sa.Column('entity_type', sa.String(length=60), nullable=True),
    sa.Column('entity_id', sa.String(length=60), nullable=True),
    sa.Column('detail', sa.JSON(), nullable=True),
    sa.Column('detected_at', sa.DateTime(), nullable=True),
    sa.Column('state', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('finding_id', name=op.f('pk_lumen_quality_finding'))
    )
    op.create_table('lumen_quality_score',
    sa.Column('scope_type', sa.String(length=20), nullable=False),
    sa.Column('scope_id', sa.String(length=60), nullable=False),
    sa.Column('dimension', sa.String(length=20), nullable=False),
    sa.Column('score', sa.Float(), nullable=True),
    sa.Column('computed_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('scope_type', 'scope_id', 'dimension', 'computed_at', name=op.f('pk_lumen_quality_score'))
    )
    op.create_table('CrimeSubHead',
    sa.Column('CrimeSubHeadID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('CrimeHeadID', sa.Integer(), nullable=True),
    sa.Column('CrimeHeadName', sa.String(length=200), nullable=True),
    sa.Column('SeqID', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['CrimeHeadID'], ['CrimeHead.CrimeHeadID'], name=op.f('fk_CrimeSubHead_CrimeHeadID_CrimeHead')),
    sa.PrimaryKeyConstraint('CrimeSubHeadID', name=op.f('pk_CrimeSubHead'))
    )
    op.create_table('District',
    sa.Column('DistrictID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('DistrictName', sa.String(length=120), nullable=False),
    sa.Column('StateID', sa.Integer(), nullable=True),
    sa.Column('Active', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['StateID'], ['State.StateID'], name=op.f('fk_District_StateID_State')),
    sa.PrimaryKeyConstraint('DistrictID', name=op.f('pk_District'))
    )
    op.create_table('Section',
    sa.Column('ActCode', sa.String(length=40), nullable=False),
    sa.Column('SectionCode', sa.String(length=40), nullable=False),
    sa.Column('SectionDescription', sa.String(length=600), nullable=True),
    sa.Column('Active', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['ActCode'], ['Act.ActCode'], name=op.f('fk_Section_ActCode_Act')),
    sa.PrimaryKeyConstraint('ActCode', 'SectionCode', name=op.f('pk_Section'))
    )
    op.create_table('Court',
    sa.Column('CourtID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('CourtName', sa.String(length=200), nullable=False),
    sa.Column('DistrictID', sa.Integer(), nullable=True),
    sa.Column('StateID', sa.Integer(), nullable=True),
    sa.Column('Active', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['DistrictID'], ['District.DistrictID'], name=op.f('fk_Court_DistrictID_District')),
    sa.ForeignKeyConstraint(['StateID'], ['State.StateID'], name=op.f('fk_Court_StateID_State')),
    sa.PrimaryKeyConstraint('CourtID', name=op.f('pk_Court'))
    )
    op.create_table('CrimeHeadActSection',
    sa.Column('CrimeHeadID', sa.Integer(), nullable=False),
    sa.Column('ActCode', sa.String(length=40), nullable=False),
    sa.Column('SectionCode', sa.String(length=40), nullable=False),
    sa.ForeignKeyConstraint(['ActCode', 'SectionCode'], ['Section.ActCode', 'Section.SectionCode'], name=op.f('fk_CrimeHeadActSection_ActCode_Section')),
    sa.ForeignKeyConstraint(['CrimeHeadID'], ['CrimeHead.CrimeHeadID'], name=op.f('fk_CrimeHeadActSection_CrimeHeadID_CrimeHead')),
    sa.PrimaryKeyConstraint('CrimeHeadID', 'ActCode', 'SectionCode', name=op.f('pk_CrimeHeadActSection'))
    )
    op.create_table('Unit',
    sa.Column('UnitID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('UnitName', sa.String(length=200), nullable=False),
    sa.Column('TypeID', sa.Integer(), nullable=True),
    sa.Column('ParentUnit', sa.Integer(), nullable=True),
    sa.Column('NationalityID', sa.Integer(), nullable=True),
    sa.Column('StateID', sa.Integer(), nullable=True),
    sa.Column('DistrictID', sa.Integer(), nullable=True),
    sa.Column('Active', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['DistrictID'], ['District.DistrictID'], name=op.f('fk_Unit_DistrictID_District')),
    sa.ForeignKeyConstraint(['ParentUnit'], ['Unit.UnitID'], name=op.f('fk_Unit_ParentUnit_Unit')),
    sa.ForeignKeyConstraint(['StateID'], ['State.StateID'], name=op.f('fk_Unit_StateID_State')),
    sa.ForeignKeyConstraint(['TypeID'], ['UnitType.UnitTypeID'], name=op.f('fk_Unit_TypeID_UnitType')),
    sa.PrimaryKeyConstraint('UnitID', name=op.f('pk_Unit'))
    )
    op.create_table('Employee',
    sa.Column('EmployeeID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('DistrictID', sa.Integer(), nullable=True),
    sa.Column('UnitID', sa.Integer(), nullable=True),
    sa.Column('RankID', sa.Integer(), nullable=True),
    sa.Column('DesignationID', sa.Integer(), nullable=True),
    sa.Column('KGID', sa.String(length=40), nullable=True),
    sa.Column('FirstName', sa.String(length=120), nullable=True),
    sa.Column('EmployeeDOB', sa.Date(), nullable=True),
    sa.Column('GenderID', sa.Integer(), nullable=True),
    sa.Column('BloodGroupID', sa.Integer(), nullable=True),
    sa.Column('PhysicallyChallenged', sa.Boolean(), nullable=True),
    sa.Column('AppointmentDate', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['DesignationID'], ['Designation.DesignationID'], name=op.f('fk_Employee_DesignationID_Designation')),
    sa.ForeignKeyConstraint(['DistrictID'], ['District.DistrictID'], name=op.f('fk_Employee_DistrictID_District')),
    sa.ForeignKeyConstraint(['RankID'], ['Rank.RankID'], name=op.f('fk_Employee_RankID_Rank')),
    sa.ForeignKeyConstraint(['UnitID'], ['Unit.UnitID'], name=op.f('fk_Employee_UnitID_Unit')),
    sa.PrimaryKeyConstraint('EmployeeID', name=op.f('pk_Employee'))
    )
    op.create_table('CaseMaster',
    sa.Column('CaseMasterID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('CrimeNo', sa.String(length=30), nullable=False),
    sa.Column('CaseNo', sa.String(length=20), nullable=True),
    sa.Column('CrimeRegisteredDate', sa.Date(), nullable=True),
    sa.Column('PolicePersonID', sa.Integer(), nullable=True),
    sa.Column('PoliceStationID', sa.Integer(), nullable=True),
    sa.Column('CaseCategoryID', sa.Integer(), nullable=True),
    sa.Column('GravityOffenceID', sa.Integer(), nullable=True),
    sa.Column('CrimeMajorHeadID', sa.Integer(), nullable=True),
    sa.Column('CrimeMinorHeadID', sa.Integer(), nullable=True),
    sa.Column('CaseStatusID', sa.Integer(), nullable=True),
    sa.Column('CourtID', sa.Integer(), nullable=True),
    sa.Column('IncidentFromDate', sa.DateTime(), nullable=True),
    sa.Column('IncidentToDate', sa.DateTime(), nullable=True),
    sa.Column('InfoReceivedPSDate', sa.DateTime(), nullable=True),
    sa.Column('latitude', sa.DECIMAL(precision=10, scale=7), nullable=True),
    sa.Column('longitude', sa.DECIMAL(precision=10, scale=7), nullable=True),
    sa.Column('BriefFacts', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['CaseCategoryID'], ['CaseCategory.CaseCategoryID'], name=op.f('fk_CaseMaster_CaseCategoryID_CaseCategory')),
    sa.ForeignKeyConstraint(['CaseStatusID'], ['CaseStatusMaster.CaseStatusID'], name=op.f('fk_CaseMaster_CaseStatusID_CaseStatusMaster')),
    sa.ForeignKeyConstraint(['CourtID'], ['Court.CourtID'], name=op.f('fk_CaseMaster_CourtID_Court')),
    sa.ForeignKeyConstraint(['CrimeMajorHeadID'], ['CrimeHead.CrimeHeadID'], name=op.f('fk_CaseMaster_CrimeMajorHeadID_CrimeHead')),
    sa.ForeignKeyConstraint(['CrimeMinorHeadID'], ['CrimeSubHead.CrimeSubHeadID'], name=op.f('fk_CaseMaster_CrimeMinorHeadID_CrimeSubHead')),
    sa.ForeignKeyConstraint(['GravityOffenceID'], ['GravityOffence.GravityOffenceID'], name=op.f('fk_CaseMaster_GravityOffenceID_GravityOffence')),
    sa.ForeignKeyConstraint(['PolicePersonID'], ['Employee.EmployeeID'], name=op.f('fk_CaseMaster_PolicePersonID_Employee')),
    sa.ForeignKeyConstraint(['PoliceStationID'], ['Unit.UnitID'], name=op.f('fk_CaseMaster_PoliceStationID_Unit')),
    sa.PrimaryKeyConstraint('CaseMasterID', name=op.f('pk_CaseMaster'))
    )
    op.create_table('Accused',
    sa.Column('AccusedMasterID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('CaseMasterID', sa.Integer(), nullable=True),
    sa.Column('AccusedName', sa.String(length=200), nullable=True),
    sa.Column('AgeYear', sa.Integer(), nullable=True),
    sa.Column('GenderID', sa.Integer(), nullable=True),
    sa.Column('PersonID', sa.String(length=10), nullable=True),
    sa.ForeignKeyConstraint(['CaseMasterID'], ['CaseMaster.CaseMasterID'], name=op.f('fk_Accused_CaseMasterID_CaseMaster')),
    sa.PrimaryKeyConstraint('AccusedMasterID', name=op.f('pk_Accused'))
    )
    op.create_table('ActSectionAssociation',
    sa.Column('CaseMasterID', sa.Integer(), nullable=False),
    sa.Column('ActID', sa.String(length=40), nullable=False),
    sa.Column('SectionID', sa.String(length=40), nullable=False),
    sa.Column('ActOrderID', sa.Integer(), nullable=True),
    sa.Column('SectionOrderID', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['CaseMasterID'], ['CaseMaster.CaseMasterID'], name=op.f('fk_ActSectionAssociation_CaseMasterID_CaseMaster')),
    sa.PrimaryKeyConstraint('CaseMasterID', 'ActID', 'SectionID', name=op.f('pk_ActSectionAssociation'))
    )
    op.create_table('ChargesheetDetails',
    sa.Column('CSID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('CaseMasterID', sa.Integer(), nullable=True),
    sa.Column('csdate', sa.DateTime(), nullable=True),
    sa.Column('cstype', sa.CHAR(length=1), nullable=True),
    sa.Column('PolicePersonID', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['CaseMasterID'], ['CaseMaster.CaseMasterID'], name=op.f('fk_ChargesheetDetails_CaseMasterID_CaseMaster')),
    sa.ForeignKeyConstraint(['PolicePersonID'], ['Employee.EmployeeID'], name=op.f('fk_ChargesheetDetails_PolicePersonID_Employee')),
    sa.PrimaryKeyConstraint('CSID', name=op.f('pk_ChargesheetDetails'))
    )
    op.create_table('ComplainantDetails',
    sa.Column('ComplainantID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('CaseMasterID', sa.Integer(), nullable=True),
    sa.Column('ComplainantName', sa.String(length=200), nullable=True),
    sa.Column('AgeYear', sa.Integer(), nullable=True),
    sa.Column('OccupationID', sa.Integer(), nullable=True),
    sa.Column('ReligionID', sa.Integer(), nullable=True),
    sa.Column('CasteID', sa.Integer(), nullable=True),
    sa.Column('GenderID', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['CaseMasterID'], ['CaseMaster.CaseMasterID'], name=op.f('fk_ComplainantDetails_CaseMasterID_CaseMaster')),
    sa.ForeignKeyConstraint(['CasteID'], ['CasteMaster.caste_master_id'], name=op.f('fk_ComplainantDetails_CasteID_CasteMaster')),
    sa.ForeignKeyConstraint(['OccupationID'], ['OccupationMaster.OccupationID'], name=op.f('fk_ComplainantDetails_OccupationID_OccupationMaster')),
    sa.ForeignKeyConstraint(['ReligionID'], ['ReligionMaster.ReligionID'], name=op.f('fk_ComplainantDetails_ReligionID_ReligionMaster')),
    sa.PrimaryKeyConstraint('ComplainantID', name=op.f('pk_ComplainantDetails'))
    )
    op.create_table('Victim',
    sa.Column('VictimMasterID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('CaseMasterID', sa.Integer(), nullable=True),
    sa.Column('VictimName', sa.String(length=200), nullable=True),
    sa.Column('AgeYear', sa.Integer(), nullable=True),
    sa.Column('GenderID', sa.Integer(), nullable=True),
    sa.Column('VictimPolice', sa.String(length=2), nullable=True),
    sa.ForeignKeyConstraint(['CaseMasterID'], ['CaseMaster.CaseMasterID'], name=op.f('fk_Victim_CaseMasterID_CaseMaster')),
    sa.PrimaryKeyConstraint('VictimMasterID', name=op.f('pk_Victim'))
    )
    op.create_table('ArrestSurrender',
    sa.Column('ArrestSurrenderID', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('CaseMasterID', sa.Integer(), nullable=True),
    sa.Column('ArrestSurrenderTypeID', sa.Integer(), nullable=True),
    sa.Column('ArrestSurrenderDate', sa.Date(), nullable=True),
    sa.Column('ArrestSurrenderStateId', sa.Integer(), nullable=True),
    sa.Column('ArrestSurrenderDistrictId', sa.Integer(), nullable=True),
    sa.Column('PoliceStationID', sa.Integer(), nullable=True),
    sa.Column('IOID', sa.Integer(), nullable=True),
    sa.Column('CourtID', sa.Integer(), nullable=True),
    sa.Column('AccusedMasterID', sa.Integer(), nullable=True),
    sa.Column('IsAccused', sa.Boolean(), nullable=True),
    sa.Column('IsComplainantAccused', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['AccusedMasterID'], ['Accused.AccusedMasterID'], name=op.f('fk_ArrestSurrender_AccusedMasterID_Accused')),
    sa.ForeignKeyConstraint(['ArrestSurrenderDistrictId'], ['District.DistrictID'], name=op.f('fk_ArrestSurrender_ArrestSurrenderDistrictId_District')),
    sa.ForeignKeyConstraint(['ArrestSurrenderStateId'], ['State.StateID'], name=op.f('fk_ArrestSurrender_ArrestSurrenderStateId_State')),
    sa.ForeignKeyConstraint(['CaseMasterID'], ['CaseMaster.CaseMasterID'], name=op.f('fk_ArrestSurrender_CaseMasterID_CaseMaster')),
    sa.ForeignKeyConstraint(['CourtID'], ['Court.CourtID'], name=op.f('fk_ArrestSurrender_CourtID_Court')),
    sa.ForeignKeyConstraint(['IOID'], ['Employee.EmployeeID'], name=op.f('fk_ArrestSurrender_IOID_Employee')),
    sa.ForeignKeyConstraint(['PoliceStationID'], ['Unit.UnitID'], name=op.f('fk_ArrestSurrender_PoliceStationID_Unit')),
    sa.PrimaryKeyConstraint('ArrestSurrenderID', name=op.f('pk_ArrestSurrender'))
    )
    op.create_table('lumen_person_dispute',
    sa.Column('dispute_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('person_id', sa.String(length=36), nullable=True),
    sa.Column('accused_master_id', sa.Integer(), nullable=True),
    sa.Column('raised_by', sa.String(length=120), nullable=True),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('raised_at', sa.DateTime(), nullable=True),
    sa.Column('resolution', sa.String(length=40), nullable=True),
    sa.ForeignKeyConstraint(['accused_master_id'], ['Accused.AccusedMasterID'], name=op.f('fk_lumen_person_dispute_accused_master_id_Accused')),
    sa.ForeignKeyConstraint(['person_id'], ['lumen_person.person_id'], name=op.f('fk_lumen_person_dispute_person_id_lumen_person')),
    sa.PrimaryKeyConstraint('dispute_id', name=op.f('pk_lumen_person_dispute'))
    )
    op.create_table('lumen_person_link',
    sa.Column('person_id', sa.String(length=36), nullable=False),
    sa.Column('accused_master_id', sa.Integer(), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=True),
    sa.Column('match_features', sa.JSON(), nullable=True),
    sa.Column('state', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['accused_master_id'], ['Accused.AccusedMasterID'], name=op.f('fk_lumen_person_link_accused_master_id_Accused')),
    sa.ForeignKeyConstraint(['person_id'], ['lumen_person.person_id'], name=op.f('fk_lumen_person_link_person_id_lumen_person')),
    sa.PrimaryKeyConstraint('person_id', 'accused_master_id', name=op.f('pk_lumen_person_link'))
    )
    op.create_table('inv_arrestsurrenderaccused',
    sa.Column('ArrestSurrenderID', sa.Integer(), nullable=False),
    sa.Column('AccusedMasterID', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['AccusedMasterID'], ['Accused.AccusedMasterID'], name=op.f('fk_inv_arrestsurrenderaccused_AccusedMasterID_Accused')),
    sa.ForeignKeyConstraint(['ArrestSurrenderID'], ['ArrestSurrender.ArrestSurrenderID'], name=op.f('fk_inv_arrestsurrenderaccused_ArrestSurrenderID_ArrestSurrender')),
    sa.PrimaryKeyConstraint('ArrestSurrenderID', 'AccusedMasterID', name=op.f('pk_inv_arrestsurrenderaccused'))
    )

    # ── Indexes (§3.5 CaseMaster geo/date/unit/head) ─────────────────────
    op.create_index('ix_case_date', 'CaseMaster', ['CrimeRegisteredDate'], unique=False)
    op.create_index('ix_case_head', 'CaseMaster', ['CrimeMajorHeadID', 'CrimeMinorHeadID'], unique=False)
    op.create_index('ix_case_unit', 'CaseMaster', ['PoliceStationID'], unique=False)
    op.create_index('ix_case_geo', 'CaseMaster', ['latitude', 'longitude'], unique=False)


def downgrade() -> None:
    # Reverse order: indexes, then tables (children before parents).
    op.drop_index('ix_case_date', table_name='CaseMaster')
    op.drop_index('ix_case_head', table_name='CaseMaster')
    op.drop_index('ix_case_unit', table_name='CaseMaster')
    op.drop_index('ix_case_geo', table_name='CaseMaster')
    op.drop_table('inv_arrestsurrenderaccused')
    op.drop_table('lumen_person_link')
    op.drop_table('lumen_person_dispute')
    op.drop_table('ArrestSurrender')
    op.drop_table('Victim')
    op.drop_table('ComplainantDetails')
    op.drop_table('ChargesheetDetails')
    op.drop_table('ActSectionAssociation')
    op.drop_table('Accused')
    op.drop_table('CaseMaster')
    op.drop_table('Employee')
    op.drop_table('Unit')
    op.drop_table('CrimeHeadActSection')
    op.drop_table('Court')
    op.drop_table('Section')
    op.drop_table('District')
    op.drop_table('CrimeSubHead')
    op.drop_table('lumen_quality_score')
    op.drop_table('lumen_quality_finding')
    op.drop_table('lumen_person')
    op.drop_table('UnitType')
    op.drop_table('State')
    op.drop_table('ReligionMaster')
    op.drop_table('Rank')
    op.drop_table('OccupationMaster')
    op.drop_table('GravityOffence')
    op.drop_table('Designation')
    op.drop_table('CrimeHead')
    op.drop_table('CasteMaster')
    op.drop_table('CaseStatusMaster')
    op.drop_table('CaseCategory')
    op.drop_table('Act')
