
import requests
import json

token = requests.post("http://127.0.0.1:8000/api/auth/login", json={"clearance_id": "OP-7729", "passphrase": "lumen2024"}).json()["token"]
headers = {"Authorization": f"Bearer {token}"}

endpoints = [
    "/api/dashboard/summary",
    "/api/dashboard/crime-trend",
    "/api/dashboard/heatmap",
    "/api/dashboard/alerts",
    "/api/investigation/cases",
    "/api/intelligence/workbench",
    "/api/geospatial/hotspots",
    "/api/analytics/statistics",
    "/api/operations/tactical-overview"
]

for ep in endpoints:
    url = f"http://127.0.0.1:8000{ep}"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        length = len(data) if isinstance(data, list) else 1
        print(f"{ep}: 200 OK | {length} records")
        if isinstance(data, list) and length > 0:
            print("  ", json.dumps(data[0])[:150] + "...")
        elif isinstance(data, dict):
            print("  ", json.dumps(data)[:150] + "...")
    else:
        print(f"{ep}: {res.status_code} {res.text}")

