
import logging
logging.basicConfig(level=logging.INFO)
from app.db.session import SessionLocal, engine
from app.db.models import Base
from app.db.seed import seed_database

print("Dropping tables...")
Base.metadata.drop_all(bind=engine)
print("Creating tables...")
Base.metadata.create_all(bind=engine)

db = SessionLocal()
print("Starting seed process...")
try:
    seed_database(db)
    db.commit()
    print("Seeding successful!")
except Exception as e:
    db.rollback()
    print(f"Error during seeding: {e}")

