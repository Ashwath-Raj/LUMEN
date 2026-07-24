import os

def rewrite_seed_py():
    seed_path = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN\backend\app\db\seed.py"
    
    content = """\"\"\"
Comprehensive database seed.

Seeds all tables with realistic Karnataka State Police data.
Idempotent - safe to call on every startup.
\"\"\"
from __future__ import annotations
import logging
from sqlalchemy.orm import Session

from app.db.models import OperatorORM
from app.db.seeds.karnataka import geography, units, ranks, classification, fir_generator

logger = logging.getLogger("lumen")

def seed_database(session: Session) -> None:
    \"\"\"Idempotent - only seeds if no operators exist.\"\"\"
    if session.query(OperatorORM).count():
        return

    logger.info("Initializing Karnataka State Police Master Data...")

    # 1. Geography
    states = geography.get_states()
    session.add_all(states)
    session.add_all(geography.get_ranges())
    session.add_all(geography.get_commissionerates())
    
    districts = geography.get_districts()
    session.add_all(districts)
    session.flush()

    # 2. Units & Stations
    session.add_all(units.get_unit_types())
    police_stations = units.get_units()
    session.add_all(police_stations)
    session.flush()

    # 3. Ranks & Designations
    rank_list = ranks.get_ranks()
    desig_list = ranks.get_designations()
    session.add_all(rank_list)
    session.add_all(desig_list)
    session.flush()

    # 4. Crime Classification
    session.add_all(classification.get_acts())
    sections = classification.get_sections()
    session.add_all(sections)
    crime_heads = classification.get_crime_heads()
    session.add_all(crime_heads)
    session.add_all(classification.get_crime_sub_heads())
    session.add_all(classification.get_master_lookups())
    session.flush()

    # 5. Employees & Operators
    logger.info("Generating KSP Personnel...")
    employees, operators = fir_generator.generate_employees(
        districts=districts,
        units=police_stations,
        ranks=rank_list,
        designations=desig_list,
        count=50
    )
    session.add_all(employees)
    session.flush()
    session.add_all(operators)
    session.flush()

    # 6. FIRs (CaseMaster)
    logger.info("Generating Realistic FIRs...")
    firs, relations = fir_generator.generate_firs(
        count=150,
        units=police_stations,
        employees=employees,
        sections=sections,
        crime_heads=crime_heads
    )
    session.add_all(firs)
    session.flush()
    session.add_all(relations)
    session.flush()
    
    # 7. Watchlist
    accused_list = [r for r in relations if type(r).__name__ == "AccusedORM"]
    session.add_all(fir_generator.generate_watchlist(accused_list))
    
    session.commit()
    logger.info("Karnataka State Police seed complete.")
"""
    with open(seed_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    rewrite_seed_py()
