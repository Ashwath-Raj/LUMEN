"""
Comprehensive database seed.
Seeds all tables with realistic Karnataka State Police data.
Idempotent - safe to call on every startup.
"""
from __future__ import annotations
import logging
import random
from sqlalchemy.orm import Session

from lumen.config import settings
from lumen.db.models.legacy_models import OperatorORM
from lumen.jobs.seeds.karnataka import geography, units, ranks, classification, fir_generator

logger = logging.getLogger("lumen")

def seed_database(session: Session) -> None:
    """Idempotent - only seeds if no operators exist."""
    if session.query(OperatorORM).count():
        return

    # Deterministic Seed
    random.seed(settings.SEED_RANDOM)
    
    # Scale configurations
    if settings.DATASET_SCALE == "large":
        emp_count = 500
        fir_count = 5000
    elif settings.DATASET_SCALE == "medium":
        emp_count = 150
        fir_count = 500
    else:  # small
        emp_count = 50
        fir_count = 100

    logger.info(f"Initializing Karnataka State Police Master Data (Scale: {settings.DATASET_SCALE})...")

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
    workload_manager = fir_generator.WorkloadManager()
    workload_manager.generate(districts, police_stations, rank_list, desig_list, emp_count)
    
    session.add_all(workload_manager.employees)
    session.flush()
    session.add_all(workload_manager.operators)
    session.flush()

    # 6. FIRs (CaseMaster) & Ecosystem
    logger.info(f"Generating {fir_count} Realistic FIRs & Investigations...")
    firs, relations = fir_generator.generate_firs(
        count=fir_count,
        districts=districts,
        units=police_stations,
        workload_manager=workload_manager
    )
    
    # Batch insertion to avoid memory spikes
    batch_size = 1000
    for i in range(0, len(firs), batch_size):
        session.add_all(firs[i:i + batch_size])
        session.flush()
        
    for i in range(0, len(relations), batch_size):
        session.add_all(relations[i:i + batch_size])
        session.flush()
    
    # 7. Hotspots & Watchlist
    session.add_all(fir_generator.generate_hotspots(30))
    
    accused_list = [r for r in relations if type(r).__name__ == "AccusedORM"]
    session.add_all(fir_generator.generate_watchlist(accused_list))
    
    session.commit()
    logger.info("Karnataka State Police Intelligence seed complete.")
