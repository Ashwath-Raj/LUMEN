
import requests
token = requests.post("http://127.0.0.1:8000/api/auth/login", json={"clearance_id": "OP-7729", "passphrase": "lumen2024"}).json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("--- Dashboard Summary ---")
print(requests.get("http://127.0.0.1:8000/api/dashboard/summary", headers=headers).json())
print("--- Cases ---")
print(requests.get("http://127.0.0.1:8000/api/investigation/cases", headers=headers).json())

