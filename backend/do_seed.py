
from app.db.session import SessionLocal
from app.db.seed import seed_database
db = SessionLocal()
seed_database(db)
db.commit()
print("Seeding complete.")

