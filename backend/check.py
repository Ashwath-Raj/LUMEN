import sys
sys.path.append('.')
from sqlalchemy import select, func
from app.db.session import SessionLocal
from app.db.models import OperatorORM, CaseORM, FIRORM

def check():
    with SessionLocal() as session:
        op_count = session.scalar(select(func.count()).select_from(OperatorORM))
        op_with_district = session.scalar(select(func.count()).select_from(OperatorORM).where(OperatorORM.district_id != None))
        op_with_unit_id = session.scalar(select(func.count()).select_from(OperatorORM).where(OperatorORM.unit_id != None))
        op_with_unit = session.scalar(select(func.count()).select_from(OperatorORM).where(OperatorORM.unit != None))
        
        case_count = session.scalar(select(func.count()).select_from(CaseORM))
        case_with_station = session.scalar(select(func.count()).select_from(CaseORM).where(CaseORM.police_station_id != None))
        
        fir_count = session.scalar(select(func.count()).select_from(FIRORM))
        fir_with_district = session.scalar(select(func.count()).select_from(FIRORM).where(FIRORM.district != None))
        
        print(f'Operators: {op_count} | w/ district_id: {op_with_district} | w/ unit_id: {op_with_unit_id} | w/ unit: {op_with_unit}')
        print(f'Cases: {case_count} | w/ police_station_id: {case_with_station}')
        print(f'FIRs: {fir_count} | w/ district: {fir_with_district}')

check()
