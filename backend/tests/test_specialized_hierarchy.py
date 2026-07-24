import pytest
from sqlalchemy.exc import IntegrityError
from app.db.models import DepartmentORM, SpecializedUnitORM, StateORM, DistrictORM

def test_department_creation_and_uniqueness(db_session):
    """Verify that a department can be created and codes must be unique."""
    # The migration seeded departments, so we should be able to query them
    deps = db_session.query(DepartmentORM).all()
    assert len(deps) >= 24, "Migration should have seeded at least 24 baseline departments"
    
    # Check that a specific department exists
    cid = db_session.query(DepartmentORM).filter_by(code="DEP-CID").first()
    assert cid is not None
    assert cid.name == "Criminal Investigation Department"
    assert cid.department_type == "Investigation"
    
    state_id = cid.state_id
    
    # Attempt to create a duplicate code
    dup = DepartmentORM(
        id="test-dup-id",
        name="Duplicate CID",
        code="DEP-CID",  # duplicate
        state_id=state_id,
        department_type="Investigation"
    )
    db_session.add(dup)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_specialized_unit_requires_department(db_session):
    """Verify that a specialized unit strictly belongs to a department."""
    cid = db_session.query(DepartmentORM).filter_by(code="DEP-CID").first()
    assert cid is not None
    
    # Create valid specialized unit
    su = SpecializedUnitORM(
        id="su-1",
        name="Cyber Forensics Team",
        code="SU-CYB",
        description="Handles advanced cyber forensics",
        department_id=cid.id,
        unit_type="Technical"
    )
    db_session.add(su)
    db_session.commit()
    
    saved_su = db_session.query(SpecializedUnitORM).filter_by(id="su-1").first()
    assert saved_su is not None
    assert saved_su.department_id == cid.id
    
    # Create invalid specialized unit (no department_id)
    invalid_su = SpecializedUnitORM(
        id="su-2",
        name="Invalid Unit",
        code="SU-INV",
        unit_type="Technical"
    )
    db_session.add(invalid_su)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    
def test_territorial_separation_preserved(db_session):
    """Verify that territorial entities are distinct and unchanged by specialized entities."""
    # Ensure districts exist
    districts = db_session.query(DistrictORM).all()
    assert len(districts) > 0, "Territorial districts should remain intact"
    
    # Verify that a DistrictORM does not accidentally inherit department fields
    d = districts[0]
    assert not hasattr(d, "department_id")
    assert not hasattr(d, "department_type")
    
    # Verify a DepartmentORM does not have territorial fields
    deps = db_session.query(DepartmentORM).all()
    dep = deps[0]
    assert not hasattr(dep, "range_id")
    assert not hasattr(dep, "commissionerate_id")
