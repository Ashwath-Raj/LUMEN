# NOTE: This is a standalone debug script (not a pytest test), and it
# imports the deleted legacy DB models and ModuleService. Expected to
# fail until the canonical DB schema/service layer is rebuilt in a later
# LUMEN_MASTER_SPEC_V3 session (Session 2). Left as-is (not deleted, not
# patched) per the sanitation-pass scope.
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lumen.db.session import SessionLocal
from lumen.db.models.legacy_models import OperatorORM, FIRORM
from lumen.services.module_service import ModuleService
import uuid

def debug():
    db = SessionLocal()
    try:
        op = db.query(OperatorORM).filter(OperatorORM.role == "command").first()
        if not op:
            print("No command operator")
            return
            
        from sqlalchemy import text
        case_id = db.execute(text("SELECT id FROM cases LIMIT 1")).scalar()
        
        fir_id = str(uuid.uuid4())
        fir = FIRORM(
            id=fir_id,
            case_id=case_id,
            fir_number=f"FIR-{fir_id[:8]}",
            district="Mock",
            year="2026"
        )
        db.add(fir)
        db.flush()
        
        from lumen.contracts.operator import Operator
        operator = Operator.model_validate(op, from_attributes=True)
        
        ms = ModuleService(db, operator=operator)
        rows = ms._get_authorized_firs()
        print(f"Total FIRs: {len(rows)}")
        
        found = any(r.id == fir_id for r in rows)
        print(f"FIR found in rows? {found}")
        
        result = ms.get_investigation_fir_intelligence(fir_id)
        print(f"Result: {result is not None}")
        
    finally:
        db.rollback()
        db.close()

if __name__ == "__main__":
    debug()
