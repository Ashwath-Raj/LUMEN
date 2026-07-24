from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()

sql1 = "SELECT strftime('%Y-%m', crime_registered_date) as month, COUNT(*) as cnt FROM cases WHERE crime_registered_date IS NOT NULL GROUP BY month ORDER BY month DESC LIMIT 12"
monthly = db.execute(text(sql1)).fetchall()
print('Cases by month:')
for row in monthly:
    print(f'  {row[0]}: {row[1]}')

sql2 = "SELECT strftime('%w', crime_registered_date) as dow, COUNT(*) as cnt FROM cases WHERE crime_registered_date IS NOT NULL GROUP BY dow ORDER BY dow"
by_day = db.execute(text(sql2)).fetchall()
print('Cases by day (0=Sun):')
for row in by_day:
    print(f'  Day {row[0]}: {row[1]}')

heinous = db.execute(text("SELECT COUNT(*) FROM cases c JOIN gravity_offences go ON c.gravity_offence_id = go.id WHERE go.lookup_value LIKE '%Heinous%'")).scalar()
print(f'Heinous cases: {heinous}')

hotspot_critical = db.execute(text("SELECT COUNT(*) FROM hotspots WHERE intensity='critical'")).scalar()
hotspot_high = db.execute(text("SELECT COUNT(*) FROM hotspots WHERE intensity='high'")).scalar()
print(f'Critical hotspots: {hotspot_critical}, High hotspots: {hotspot_high}')

accused_total = db.execute(text("SELECT COUNT(*) FROM accused")).scalar()
arrest_total = db.execute(text("SELECT COUNT(*) FROM arrest_surrenders")).scalar()
print(f'Accused: {accused_total}, Arrests: {arrest_total}')

property_total = db.execute(text("SELECT COUNT(*) FROM properties")).scalar()
vehicle_total = db.execute(text("SELECT COUNT(*) FROM vehicles")).scalar()
print(f'Properties: {property_total}, Vehicles: {vehicle_total}')

operators_total = db.execute(text("SELECT COUNT(*) FROM operators WHERE status='ACTIVE'")).scalar()
print(f'Active operators: {operators_total}')

# Case labels sample
case_labels = db.execute(text("SELECT label FROM cases LIMIT 5")).fetchall()
print('Case label samples:')
for row in case_labels:
    print(f'  {row[0]}')

# District stats
dist_stats = db.execute(text("SELECT d.name, COUNT(c.id) as cnt FROM cases c JOIN units u ON c.police_station_id=u.id JOIN districts d ON u.district_id=d.id GROUP BY d.name ORDER BY cnt DESC LIMIT 5")).fetchall()
print('Cases by district:')
for row in dist_stats:
    print(f'  {row[0]}: {row[1]}')

db.close()
