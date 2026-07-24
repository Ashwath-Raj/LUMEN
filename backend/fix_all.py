import os

def fix_all():
    # Fix seed.py
    seed_path = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN\backend\app\db\seed.py"
    with open(seed_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "session.add_all(fir_generator.generate_hotspots())" not in content:
        content = content.replace(
            "session.commit()",
            "session.add_all(fir_generator.generate_hotspots())\n    session.commit()"
        )
    with open(seed_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Fix fir_generator.py to add password to all operators
    fir_gen_path = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN\backend\app\db\seeds\karnataka\fir_generator.py"
    with open(fir_gen_path, 'r', encoding='utf-8') as f:
        content2 = f.read()
        
    content2 = content2.replace(
        'status="ACTIVE",\n                kgid=emp.kgid',
        'status="ACTIVE",\n                hashed_password=hash_password("lumen2024"),\n                kgid=emp.kgid'
    )
    with open(fir_gen_path, 'w', encoding='utf-8') as f:
        f.write(content2)

if __name__ == "__main__":
    fix_all()
