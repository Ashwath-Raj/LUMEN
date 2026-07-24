import asyncio
import os
import time
from sqlalchemy import event
from sqlalchemy.engine import Engine
from fastapi.testclient import TestClient

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.db.session import engine

query_count = 0

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    global query_count
    query_count += 1

client = TestClient(app)

def login():
    resp = client.post("/api/auth/login", json={"clearance_id": "OP-7729", "passphrase": "password"})
    return {"Authorization": f"Bearer {resp.json()['token']}"}

def measure(endpoint, method="GET", json=None, headers=None):
    global query_count
    query_count = 0
    start = time.time()
    
    if method == "GET":
        resp = client.get(endpoint, headers=headers)
    else:
        resp = client.post(endpoint, json=json, headers=headers)
        
    end = time.time()
    ms = (end - start) * 1000
    
    status = resp.status_code
    
    return {
        "status": status,
        "queries": query_count,
        "ms": ms,
        "records": len(resp.json()) if isinstance(resp.json(), list) else 1
    }

def run_audit():
    print("Logging in...")
    headers = login()
    
    endpoints = [
        {"url": "/api/dashboard/summary", "method": "GET"},
        {"url": "/api/investigation/cases", "method": "GET"},
        {"url": "/api/analytics/statistics", "method": "GET"},
        {"url": "/api/geospatial/hotspots", "method": "GET"},
        {"url": "/api/operations/tactical-overview", "method": "GET"},
        {"url": "/api/intelligence/workbench", "method": "GET"},
        {"url": "/api/investigation/suspects", "method": "GET"}
    ]
    
    print(f"{'Endpoint':<40} | {'Status'} | {'Queries':<7} | {'Records':<7} | {'Time (ms)'}")
    print("-" * 80)
    for ep in endpoints:
        res = measure(ep["url"], method=ep["method"], headers=headers)
        print(f"{ep['url']:<40} | {res['status']:<6} | {res['queries']:<7} | {res['records']:<7} | {res['ms']:.2f}ms")
        
    # Get a single case
    cases_resp = client.get("/api/investigation/cases", headers=headers)
    if cases_resp.status_code == 200 and len(cases_resp.json()) > 0:
        case_id = cases_resp.json()[0]["id"]
        res = measure(f"/api/investigation/cases/{case_id}", headers=headers)
        print(f"{'/api/investigation/cases/{id}':<40} | {res['status']:<6} | {res['queries']:<7} | {res['records']:<7} | {res['ms']:.2f}ms")
        
run_audit()
