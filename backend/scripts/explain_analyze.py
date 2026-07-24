from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("--- EXPLAIN ANALYZE on Accused ---")
    res = conn.execute(text("EXPLAIN ANALYZE SELECT id, name, age_year, gender, case_master_id FROM accused WHERE case_master_id = '104490102202600001'"))
    for row in res:
        print(row[0])
    
    print("\n--- EXPLAIN ANALYZE on Properties ---")
    res = conn.execute(text("EXPLAIN ANALYZE SELECT id, description FROM properties WHERE case_master_id = '104490102202600001'"))
    for row in res:
        print(row[0])
