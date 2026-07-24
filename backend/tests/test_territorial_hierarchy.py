import pytest
from app.db.models import StateORM, PoliceRangeORM, CommissionerateORM, DistrictORM, UnitORM, CaseORM, OperatorORM

def test_territorial_hierarchy_structure(db_session):
    """Verify State -> Range/Commissionerate -> District -> Unit foreign keys are structurally valid."""
    # State exists
    state = db_session.query(StateORM).filter_by(id="29").first()
    assert state is not None
    assert state.name == "Karnataka"

    # Ranges exist and link to state
    ranges = db_session.query(PoliceRangeORM).all()
    assert len(ranges) == 6
    for r in ranges:
        assert r.state_id == state.id

    # Commissionerates exist and link to state
    commissionerates = db_session.query(CommissionerateORM).all()
    assert len(commissionerates) == 3
    for c in commissionerates:
        assert c.state_id == state.id

    # Districts exist and link to Range OR Commissionerate
    districts = db_session.query(DistrictORM).all()
    assert len(districts) == 34
    for d in districts:
        assert d.state_id == state.id
        assert (d.range_id is not None) or (d.commissionerate_id is not None), f"District {d.name} is orphaned from command layer"
        assert not (d.range_id is not None and d.commissionerate_id is not None), f"District {d.name} belongs to both Range and Commissionerate"

    # Units exist and link to District
    units = db_session.query(UnitORM).all()
    assert len(units) > 0
    for u in units:
        assert u.district_id is not None, f"Unit {u.name} is orphaned from District layer"

def test_case_jurisdiction_integrity(db_session):
    """Verify that every Case maps deterministically to a Unit, and thus a District."""
    cases = db_session.query(CaseORM).all()
    assert len(cases) > 0
    
    for c in cases:
        assert c.police_station_id is not None, f"Case {c.id} has no police_station_id"
        unit = db_session.query(UnitORM).filter_by(id=c.police_station_id).first()
        assert unit is not None, f"Case {c.id} points to non-existent unit {c.police_station_id}"
        assert unit.district_id is not None, f"Case {c.id} unit {unit.name} has no district"

def test_operator_jurisdiction_integrity(db_session):
    """Verify that Operator district_id is the primary authorization boundary."""
    operators = db_session.query(OperatorORM).all()
    assert len(operators) > 0
    
    for op in operators:
        if op.role in ["analyst", "field"]:
            assert op.district_id is not None, f"Operator {op.id} is {op.role} but lacks district_id"
            d = db_session.query(DistrictORM).filter_by(id=op.district_id).first()
            assert d is not None, f"Operator {op.id} has invalid district_id {op.district_id}"
            
        if op.unit_id is not None:
            u = db_session.query(UnitORM).filter_by(id=op.unit_id).first()
            assert u is not None, f"Operator {op.id} has invalid unit_id {op.unit_id}"
            # Ensure unit matches district
            if op.district_id is not None:
                assert u.district_id == op.district_id, f"Operator {op.id} unit_id district {u.district_id} does not match op district {op.district_id}"
