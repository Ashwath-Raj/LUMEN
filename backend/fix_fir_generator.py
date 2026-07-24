import os

def fix_fir_generator():
    path = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN\backend\app\db\seeds\karnataka\fir_generator.py"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Import hash_password and HotspotORM
    if "hash_password" not in content:
        content = content.replace(
            "from app.services.crime_number_service import CrimeNumberService",
            "from app.services.crime_number_service import CrimeNumberService\nfrom app.core.hashing import hash_password\nfrom app.db.models import HotspotORM"
        )
    
    # 2. Add hashed_password to Command Operator
    if "hashed_password" not in content:
        content = content.replace(
            'status="ACTIVE",',
            'status="ACTIVE",\n                         hashed_password=hash_password("lumen2024"),'
        )

    # 3. Add Hotspot generation
    hotspot_func = """
def generate_hotspots(count=10):
    hotspots = []
    for i in range(count):
        hotspots.append(HotspotORM(
            id=f"HS-{i:04d}",
            name=f"Hotspot {i}",
            category="Theft",
            risk_level=random.choice(["HIGH", "MEDIUM", "LOW"]),
            latitude=12.9716 + random.uniform(-0.1, 0.1),
            longitude=77.5946 + random.uniform(-0.1, 0.1),
            radius_meters=random.randint(50, 500),
            active=True
        ))
    return hotspots
"""
    if "def generate_hotspots" not in content:
        content += hotspot_func
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    fix_fir_generator()
