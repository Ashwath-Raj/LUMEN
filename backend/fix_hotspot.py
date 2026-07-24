import os

def fix_hotspot_schema():
    path = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN\backend\app\db\seeds\karnataka\fir_generator.py"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    correct_hotspot_func = """
def generate_hotspots(count=10):
    hotspots = []
    for i in range(count):
        hotspots.append(HotspotORM(
            id=f"HS-{i:04d}",
            label=f"Hotspot {i}",
            x=12.9716 + random.uniform(-0.1, 0.1),
            y=77.5946 + random.uniform(-0.1, 0.1),
            intensity=random.choice(["critical", "high", "moderate", "low"]),
            probability=random.randint(50, 99),
            incidents=random.randint(5, 50),
            window_hours=72
        ))
    return hotspots
"""

    old_func_start = "def generate_hotspots(count=10):"
    
    # Split content and replace just the function
    parts = content.split(old_func_start)
    if len(parts) > 1:
        content = parts[0] + correct_hotspot_func

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    fix_hotspot_schema()
