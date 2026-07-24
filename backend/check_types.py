from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()

columns = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'intelligence_leads'")).fetchall()
print("intelligence_leads columns:", columns)

lead_count = db.execute(text("SELECT count(*) FROM intelligence_leads")).fetchone()[0]
print(f"Total leads: {lead_count}")

if lead_count > 0:
    empty_count = db.execute(text("SELECT count(*) FROM intelligence_leads WHERE source_cases IS NULL OR source_cases::text = '[]'")).fetchone()[0]
    print(f"Empty source_cases: {empty_count}")
    
db.close()
