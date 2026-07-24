import sys
sys.path.append('.')
from sqlalchemy import select, func
from app.db.session import SessionLocal
from app.db.models import CaseORM, UnitORM

def check():
    with SessionLocal() as session:
        units_used_in_cases = session.execute(select(CaseORM.police_station_id).distinct()).scalars().all()
        
        units_with_district = session.scalar(
            select(func.count())
            .select_from(UnitORM)
            .where(UnitORM.id.in_(units_used_in_cases))
            .where(UnitORM.district_id != None)
        )
        
        print(f'Unique police stations in cases: {len(units_used_in_cases)}')
        print(f'Police stations with district_id: {units_with_district}')

check()
