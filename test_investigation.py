
import requests
import json
token = ""
res = requests.post("http://localhost:8000/api/auth/login", json={"clearance_id": "OP-7729", "passphrase": "lumen2024"})
if res.status_code == 200:
    token = res.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}
print("Suspects:", requests.get("http://localhost:8000/api/investigation/suspects", headers=headers).json())
print("Evidence:", requests.get("http://localhost:8000/api/investigation/evidence-locker", headers=headers).json())
print("Case 1:", requests.get("http://localhost:8000/api/investigation/cases/104490102202600001", headers=headers).json())

