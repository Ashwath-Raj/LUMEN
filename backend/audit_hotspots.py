import os
from sqlalchemy import create_engine, text
from app.db.session import SessionLocal

db = SessionLocal()

# 1. Inspect Hotspot Schema in DB
print("=== HOTSPOT SCHEMA ===")
schema_cols = db.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'hotspots'")).fetchall()
for col in schema_cols:
    print(col)

# 2. Existing Hotspot Data Audit
print("\n=== HOTSPOT DATA ===")
count = db.execute(text("SELECT COUNT(*) FROM hotspots")).scalar()
print(f"Total hotspots: {count}")
if count > 0:
    min_x, max_x, min_y, max_y = db.execute(text("SELECT MIN(x), MAX(x), MIN(y), MAX(y) FROM hotspots")).fetchone()
    print(f"X bounds: [{min_x}, {max_x}]")
    print(f"Y bounds: [{min_y}, {max_y}]")
    
    # Check if x/y match typical lat/lng for Karnataka (Lat: ~11-19, Lng: ~74-79)
    # If x is ~74-79, x is longitude. If x is ~11-19, x is latitude.
    sample = db.execute(text("SELECT id, x, y, label, intensity FROM hotspots LIMIT 5")).fetchall()
    for row in sample:
        print(row)

# 3. PostGIS and Spatial Capability Audit
print("\n=== POSTGIS AUDIT ===")
postgis_exists = db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'postgis'")).fetchall()
print(f"PostGIS installed: {len(postgis_exists) > 0}")

if len(postgis_exists) > 0:
    geom_cols = db.execute(text("SELECT f_table_name, f_geometry_column, type FROM geometry_columns")).fetchall()
    print("Geometry columns:")
    for c in geom_cols:
        print(c)

# 4. Jurisdiction Hierarchy Audit
print("\n=== JURISDICTION SPATIAL CAPABILITY ===")
tables_to_check = ['districts', 'units', 'police_stations']
for table in tables_to_check:
    cols = db.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")).fetchall()
    if cols:
        print(f"Table '{table}' columns:")
        for c in cols:
            print(f"  {c[0]} ({c[1]})")

db.close()
