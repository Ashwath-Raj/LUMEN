
import requests
token = requests.post("http://127.0.0.1:8000/api/auth/login", json={"clearance_id": "OP-7729", "passphrase": "lumen2024"}).json()["token"]
headers = {"Authorization": f"Bearer {token}"}
res = requests.get("http://127.0.0.1:8000/api/investigation/cases", headers=headers).json()
print(f"Returned {len(res)} cases")
if len(res) > 0:
    print(res[0])

