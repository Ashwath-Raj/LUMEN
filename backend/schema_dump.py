import psycopg
conn = psycopg.connect('dbname=lumen user=postgres password=JaswanthKumar@2108 host=localhost')

print("--- CASES WITHOUT UNITS ---")
cur = conn.execute("SELECT COUNT(*) FROM cases WHERE police_station_id NOT IN (SELECT id FROM units)")
for r in cur: print(r)

print("--- UNITS WITHOUT DISTRICTS ---")
cur = conn.execute("SELECT COUNT(*) FROM units WHERE district_id IS NULL OR district_id NOT IN (SELECT id FROM districts)")
for r in cur: print(r)

print("--- OPERATORS WITHOUT DISTRICTS OR UNITS ---")
cur = conn.execute("SELECT COUNT(*) FROM operators WHERE district_id IS NULL AND unit_id IS NULL")
for r in cur: print(r)


