#!/usr/bin/env python3
"""LUMEN local showcase runtime.

A dependency-free, local-only demonstrator. All records are synthetic and do not
represent Karnataka State Police operational data. The assistant is deterministic
retrieval, not an externally hosted LLM. See README for limitations.
"""
from __future__ import annotations

import json
import math
import os
import random
import re
import sqlite3
import sys
import threading
import webbrowser
from contextlib import contextmanager
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
DATA_DIR = ROOT / "data"
DB_PATH = Path(os.environ.get("LUMEN_DB", DATA_DIR / "lumen_showcase.sqlite3")).expanduser()
DEMO_TODAY = date(2026, 11, 5)
VERSION = "0.1.0-showcase"

DISTRICTS = [
    {"name": "Bengaluru Urban", "lat": 12.9716, "lon": 77.5946, "station": "Central Division"},
    {"name": "Mysuru", "lat": 12.2958, "lon": 76.6394, "station": "City Division"},
    {"name": "Belagavi", "lat": 15.8497, "lon": 74.4977, "station": "North Division"},
    {"name": "Kalaburagi", "lat": 17.3297, "lon": 76.8343, "station": "East Division"},
    {"name": "Dakshina Kannada", "lat": 12.9141, "lon": 74.8560, "station": "Coastal Division"},
    {"name": "Vijayapura", "lat": 16.8302, "lon": 75.7100, "station": "Market Division"},
    {"name": "Shivamogga", "lat": 13.9299, "lon": 75.5681, "station": "Town Division"},
    {"name": "Ballari", "lat": 15.1394, "lon": 76.9214, "station": "Fort Division"},
    {"name": "Tumakuru", "lat": 13.3409, "lon": 77.1010, "station": "West Division"},
    {"name": "Udupi", "lat": 13.3409, "lon": 74.7421, "station": "Harbour Division"},
]
CRIME_TYPES = ["Cyber Fraud", "Vehicle Theft", "Property Crime", "Assault", "Narcotics", "Missing Person", "Financial Fraud"]
DESCRIPTIONS = {
    "Cyber Fraud": "A synthetic cyber-enabled financial complaint is recorded for demonstration.",
    "Vehicle Theft": "A synthetic vehicle theft report is recorded for demonstration.",
    "Property Crime": "A synthetic property-related incident is recorded for demonstration.",
    "Assault": "A synthetic assault report is recorded for demonstration.",
    "Narcotics": "A synthetic narcotics-related report is recorded for demonstration.",
    "Missing Person": "A synthetic missing-person report is recorded for demonstration.",
    "Financial Fraud": "A synthetic financial fraud report is recorded for demonstration.",
}


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session():
    db = connect()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _date_for_month(rng: random.Random, month_offset: int) -> date:
    month_start = (DEMO_TODAY.replace(day=1) - timedelta(days=month_offset * 30)).replace(day=1)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    span = max(1, (next_month - month_start).days)
    if month_start.year == DEMO_TODAY.year and month_start.month == DEMO_TODAY.month:
        span = min(span, DEMO_TODAY.day)
    return month_start + timedelta(days=rng.randrange(span))


def init_db(reset: bool = False) -> None:
    with db_session() as db:
        if reset:
            db.executescript("DROP TABLE IF EXISTS audit_events; DROP TABLE IF EXISTS case_person; DROP TABLE IF EXISTS cases; DROP TABLE IF EXISTS persons;")
        db.executescript("""
        CREATE TABLE IF NOT EXISTS persons (
          id TEXT PRIMARY KEY, label TEXT NOT NULL, first_seen TEXT NOT NULL,
          case_count INTEGER NOT NULL DEFAULT 0, confidence REAL NOT NULL DEFAULT 1.0
        );
        CREATE TABLE IF NOT EXISTS cases (
          id TEXT PRIMARY KEY, crime_type TEXT NOT NULL, district TEXT NOT NULL,
          station TEXT NOT NULL, severity TEXT NOT NULL, status TEXT NOT NULL,
          incident_date TEXT NOT NULL, registered_date TEXT NOT NULL,
          latitude REAL NOT NULL, longitude REAL NOT NULL, summary TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS case_person (
          case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
          person_id TEXT NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
          role TEXT NOT NULL, confidence REAL NOT NULL,
          PRIMARY KEY(case_id, person_id, role)
        );
        CREATE TABLE IF NOT EXISTS audit_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL,
          actor TEXT NOT NULL, subject TEXT NOT NULL, created_at TEXT NOT NULL,
          detail TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_cases_district ON cases(district);
        CREATE INDEX IF NOT EXISTS ix_cases_date ON cases(registered_date);
        CREATE INDEX IF NOT EXISTS ix_case_person_person ON case_person(person_id);
        """)
        existing = db.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        if existing:
            return
        rng = random.Random(20261105)
        person_ids = [f"P-{i:03d}" for i in range(1, 31)]
        for i, pid in enumerate(person_ids, 1):
            db.execute("INSERT INTO persons(id,label,first_seen,case_count,confidence) VALUES(?,?,?,?,?)",
                       (pid, f"Demo Person {i:03d}", (DEMO_TODAY - timedelta(days=rng.randint(10, 420))).isoformat(), 0, 1.0))
        for i in range(1, 81):
            district = DISTRICTS[(i * 7 + rng.randrange(len(DISTRICTS))) % len(DISTRICTS)]
            crime = rng.choices(CRIME_TYPES, weights=[24, 17, 15, 12, 8, 6, 18])[0]
            incident = _date_for_month(rng, rng.randrange(0, 12))
            registered = min(incident + timedelta(days=rng.randint(0, 8)), DEMO_TODAY)
            severity = rng.choices(["High", "Medium", "Low"], weights=[24, 48, 28])[0]
            status = rng.choices(["Under Investigation", "Chargesheet Filed", "Pending Review", "Closed"], weights=[38, 25, 22, 15])[0]
            offset_lat = rng.uniform(-0.22, 0.22)
            offset_lon = rng.uniform(-0.22, 0.22)
            case_id = f"DEMO-FIR-{i:05d}"
            station = district["station"] + f" {1 + (i % 3)}"
            db.execute("""INSERT INTO cases VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                       (case_id, crime, district["name"], station, severity, status,
                        incident.isoformat(), registered.isoformat(), district["lat"] + offset_lat,
                        district["lon"] + offset_lon, DESCRIPTIONS[crime]))
            # Repeat identities are intentionally planted for demonstrating resolution.
            p1 = person_ids[(i * 3) % len(person_ids)]
            p2 = person_ids[(i * 3 + rng.randrange(1, 11)) % len(person_ids)]
            db.execute("INSERT INTO case_person VALUES(?,?,?,?)", (case_id, p1, "Accused", round(rng.uniform(.86, .99), 3)))
            if i % 4 != 0:
                db.execute("INSERT INTO case_person VALUES(?,?,?,?)", (case_id, p2, "Associated", round(rng.uniform(.66, .84), 3)))
            if i % 3 == 0:
                p3 = person_ids[(i + 13) % len(person_ids)]
                db.execute("INSERT OR IGNORE INTO case_person VALUES(?,?,?,?)", (case_id, p3, "Victim", 1.0))
        db.execute("UPDATE persons SET case_count=(SELECT COUNT(*) FROM case_person cp WHERE cp.person_id=persons.id)")
        db.execute("UPDATE persons SET confidence=COALESCE((SELECT AVG(confidence) FROM case_person cp WHERE cp.person_id=persons.id),1.0)")
        db.execute("INSERT INTO audit_events(event_type,actor,subject,created_at,detail) VALUES(?,?,?,?,?)",
                   ("SHOWCASE_INITIALIZED", "local-demo", "synthetic-dataset", datetime.now().isoformat(timespec="seconds"), "Created 80 synthetic demo cases and 30 synthetic demo entities."))
        db.commit()


def rows(db: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    return [dict(r) for r in db.execute(sql, params).fetchall()]


def audit(event_type: str, subject: str, detail: str) -> None:
    with db_session() as db:
        db.execute("INSERT INTO audit_events(event_type,actor,subject,created_at,detail) VALUES(?,?,?,?,?)",
                   (event_type, "local-demo-user", subject, datetime.now().isoformat(timespec="seconds"), detail[:500]))


def get_cases(db: sqlite3.Connection, query: str = "", district: str = "", limit: int = 100) -> list[dict]:
    sql = "SELECT * FROM cases WHERE 1=1"
    params: list = []
    if query:
        like = f"%{query[:80]}%"
        sql += " AND (id LIKE ? OR crime_type LIKE ? OR district LIKE ? OR station LIKE ? OR status LIKE ?)"
        params.extend([like] * 5)
    if district:
        sql += " AND district = ?"
        params.append(district)
    sql += " ORDER BY registered_date DESC, id DESC LIMIT ?"
    params.append(max(1, min(limit, 250)))
    return rows(db, sql, tuple(params))


def overview(db: sqlite3.Connection) -> dict:
    cases = rows(db, "SELECT * FROM cases")
    people = db.execute("SELECT COUNT(*) FROM persons").fetchone()[0]
    total = len(cases)
    active = sum(c["status"] != "Closed" for c in cases)
    high = sum(c["severity"] == "High" for c in cases)
    anomalies = []
    by_district = Counter(c["district"] for c in cases)
    counts = list(by_district.values())
    mean = sum(counts) / max(1, len(counts))
    std = math.sqrt(sum((x - mean) ** 2 for x in counts) / max(1, len(counts)))
    districts = []
    for district in DISTRICTS:
        count = by_district[district["name"]]
        score = min(99, max(18, round(28 + (count / max(1, mean)) * 30 + (max(0, count - mean) * 2))))
        band = "High" if score >= 70 else "Moderate" if score >= 48 else "Low"
        districts.append({"district": district["name"], "cases": count, "risk_score": score, "risk_band": band,
                          "latitude": district["lat"], "longitude": district["lon"]})
        if std and count > mean + std:
            anomalies.append({"district": district["name"], "observed": count, "baseline": round(mean, 1), "z_score": round((count - mean) / std, 2)})
    month_counts = Counter(c["registered_date"][:7] for c in cases)
    month_keys = []
    current = DEMO_TODAY.replace(day=1)
    for n in range(11, -1, -1):
        d = (current - timedelta(days=n * 30)).replace(day=1)
        key = d.strftime("%Y-%m")
        if key not in month_keys:
            month_keys.append(key)
    trends = [{"month": m, "count": month_counts.get(m, 0)} for m in month_keys]
    categories = [{"label": k, "count": v} for k, v in Counter(c["crime_type"] for c in cases).most_common()]
    latest = rows(db, "SELECT id,event_type,subject,created_at,detail FROM audit_events ORDER BY id DESC LIMIT 5")
    return {"total_cases": total, "active_cases": active, "high_severity": high,
            "persons_of_interest": people, "districts_monitored": len(DISTRICTS),
            "anomaly_flags": len(anomalies), "trends": trends, "categories": categories,
            "district_risk": sorted(districts, key=lambda d: d["risk_score"], reverse=True),
            "anomalies": anomalies, "recent_activity": latest}


def graph_data(db: sqlite3.Connection) -> dict:
    people = rows(db, "SELECT id,label,case_count,confidence FROM persons ORDER BY case_count DESC")
    edges = rows(db, """SELECT a.person_id AS source, b.person_id AS target, COUNT(DISTINCT a.case_id) AS weight
        FROM case_person a JOIN case_person b ON a.case_id=b.case_id AND a.person_id != b.person_id
        WHERE a.role='Accused' AND b.role IN ('Accused','Associated')
        GROUP BY a.person_id,b.person_id HAVING COUNT(DISTINCT a.case_id)>0 ORDER BY weight DESC LIMIT 90""")
    return {"nodes": people, "edges": edges}


def person_dossier(db: sqlite3.Connection, person_id: str) -> dict | None:
    p = db.execute("SELECT * FROM persons WHERE id=?", (person_id,)).fetchone()
    if not p:
        return None
    cases = rows(db, """SELECT c.*, cp.role, cp.confidence AS link_confidence FROM cases c
        JOIN case_person cp ON cp.case_id=c.id WHERE cp.person_id=? ORDER BY c.registered_date DESC""", (person_id,))
    return {"person": dict(p), "cases": cases,
            "note": "Synthetic entity linkage for demonstration; a match is an investigative lead, not proof of identity or wrongdoing."}


def entity_candidates(db: sqlite3.Connection) -> list[dict]:
    # Demonstrate reviewable identity-linkage records without asserting identity.
    result = rows(db, """SELECT p.id AS person_id,p.label,p.case_count,p.confidence
        FROM persons p WHERE p.case_count > 1 ORDER BY p.case_count DESC LIMIT 12""")
    return [{**r, "match_state": "candidate_for_review" if r["confidence"] < .85 else "linked_demo_cluster",
             "decision": "Human review required"} for r in result]


def ask_demo(db: sqlite3.Connection, question: str) -> dict:
    q = question.strip()
    lowered = q.lower()
    if not q:
        return {"answer": "Enter a question about the synthetic showcase dataset.", "evidence": [], "mode": "deterministic_demo_retrieval"}
    protected = ("caste", "religion", "blood group", "disability")
    if any(term in lowered for term in protected):
        return {"answer": "This request concerns a protected attribute. LUMEN's design excludes caste, religion, blood group and disability status from analytical use.", "evidence": [], "mode": "policy_refusal"}
    if any(term in lowered for term in ("will he commit", "will she commit", "future criminality", "likely to offend", "predict a person")):
        return {"answer": "LUMEN does not predict individual criminality or rank people by likelihood of offending. The showcase supports case- and district-level decision support only.", "evidence": [], "mode": "policy_refusal"}
    all_cases = rows(db, "SELECT * FROM cases")
    matches = []
    for c in all_cases:
        haystack = " ".join([c["id"], c["crime_type"], c["district"], c["station"], c["status"], c["summary"]]).lower()
        if any(word in haystack for word in [w for w in re.findall(r"[a-z0-9]+", lowered) if len(w) > 3]):
            matches.append(c)
    if ("high risk" in lowered or "risk" in lowered or "hotspot" in lowered
            or ("district" in lowered and any(t in lowered for t in ("highest", "most", "count", "activity", "volume")))):
        result = overview(db)
        leaders = result["district_risk"][:4]
        answer = "District-level demonstration indicators (synthetic records): " + "; ".join(f"{x['district']} has {x['cases']} cases and a {x['risk_band'].lower()} relative risk band" for x in leaders) + ". These scores are descriptive heuristics, not validated forecasts."
        evidence = [{"id": f"aggregate:{x['district']}", "label": f"Aggregate · {x['district']}", "kind": "district aggregate"} for x in leaders]
    elif "trend" in lowered or "month" in lowered:
        result = overview(db)
        peak = max(result["trends"], key=lambda x: x["count"])
        answer = f"Across the synthetic 12-month sample, {peak['month']} has the highest recorded count ({peak['count']}). The time series is illustrative and is not an operational trend."
        evidence = [{"id": f"month:{x['month']}", "label": f"Monthly aggregate · {x['month']}", "kind": "aggregate"} for x in result["trends"] if x["count"]]
    elif any(t in lowered for t in ("privacy", "governance", "safeguard", "protected")):
        answer = "The showcase excludes protected attributes from analytical use, carries confidence on entity links, displays source references, and records selected audit events. Real deployment would require independently validated access controls, retention, masking, and security review."
        evidence = [{"id": "control:protected-attributes", "label": "Governance control · protected attributes", "kind": "design control"}, {"id": "control:evidence", "label": "Design control · evidence references", "kind": "design control"}]
    elif "person" in lowered or "network" in lowered or "repeat" in lowered or "linked" in lowered:
        linked = rows(db, "SELECT id,label,case_count FROM persons WHERE case_count>1 ORDER BY case_count DESC LIMIT 5")
        answer = "The demo graph contains repeat-linked synthetic entity nodes. The highest connected demo entities are " + ", ".join(f"{x['label']} ({x['case_count']} linked records)" for x in linked[:4]) + ". Every association is a reviewable lead, not an identity determination."
        evidence = [{"id": x["id"], "label": x["label"], "kind": "synthetic entity"} for x in linked]
    else:
        if not matches:
            matches = all_cases[:6]
        matches = sorted(matches, key=lambda x: x["registered_date"], reverse=True)[:6]
        answer = f"I retrieved {len(matches)} potentially relevant synthetic case records. " + "; ".join(f"{x['id']} · {x['crime_type']} · {x['district']} · {x['status']}" for x in matches[:4]) + ". Review the cited records before drawing conclusions."
        evidence = [{"id": x["id"], "label": f"{x['id']} · {x['crime_type']} · {x['district']}", "kind": "case record"} for x in matches]
    audit("AI_QUERY_DEMO", "synthetic-evidence-bundle", f"Question length={len(q)}; evidence_count={len(evidence)}")
    return {"answer": answer, "evidence": evidence, "mode": "deterministic_demo_retrieval",
            "disclaimer": "No external LLM is called in this local showcase. Evidence is synthetic."}


class Handler(BaseHTTPRequestHandler):
    server_version = "LUMEN-Showcase/" + VERSION

    def log_message(self, fmt: str, *args) -> None:
        sys.stdout.write("[HTTP] " + fmt % args + "\n")

    def send_json(self, payload: dict | list, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path) -> None:
        if not path.is_file() or not path.resolve().is_relative_to(WEB_DIR.resolve()):
            self.send_error(404)
            return
        data = path.read_bytes()
        mime = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8", ".svg": "image/svg+xml"}.get(path.suffix, "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)
        if path in ("/", "/index.html"):
            return self.send_file(WEB_DIR / "index.html")
        if path.startswith("/assets/"):
            return self.send_file(WEB_DIR / path.removeprefix("/assets/"))
        if path == "/healthz":
            return self.send_json({"status": "ok", "service": "lumen-showcase", "version": VERSION, "data_mode": "synthetic"})
        if not path.startswith("/api/v1/"):
            return self.send_json({"error": "not_found"}, 404)
        with db_session() as db:
            if path == "/api/v1/overview":
                return self.send_json(overview(db))
            if path == "/api/v1/cases":
                try:
                    limit = int(qs.get("limit", [100])[0])
                except (TypeError, ValueError):
                    limit = 100
                return self.send_json({"items": get_cases(db, qs.get("q", [""])[0], qs.get("district", [""])[0], limit)})
            if path.startswith("/api/v1/cases/"):
                case_id = path.rsplit("/", 1)[-1]
                record = db.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
                if not record:
                    return self.send_json({"error": "case_not_found"}, 404)
                case = dict(record)
                case["entities"] = rows(db, "SELECT p.id,p.label,cp.role,cp.confidence FROM persons p JOIN case_person cp ON cp.person_id=p.id WHERE cp.case_id=?", (case_id,))
                audit("CASE_DOSSIER_VIEW", case_id, "Viewed synthetic case dossier")
                return self.send_json(case)
            if path == "/api/v1/persons":
                return self.send_json({"items": rows(db, "SELECT * FROM persons ORDER BY case_count DESC")})
            if path.startswith("/api/v1/persons/"):
                dossier = person_dossier(db, path.rsplit("/", 1)[-1])
                return self.send_json(dossier if dossier else {"error": "person_not_found"}, 200 if dossier else 404)
            if path == "/api/v1/network":
                return self.send_json(graph_data(db))
            if path == "/api/v1/entity-resolution":
                return self.send_json({"items": entity_candidates(db), "thresholds": {"candidate": 0.65, "auto_link_demo": 0.85}, "caution": "Synthetic linkage; no real identities."})
            if path == "/api/v1/geo":
                points = rows(db, "SELECT id,crime_type,district,severity,status,latitude,longitude,registered_date FROM cases")
                return self.send_json({"districts": overview(db)["district_risk"], "points": points, "map_mode": "coordinate_plot_no_external_basemap"})
            if path == "/api/v1/insights":
                result = overview(db)
                insights = []
                for d in result["district_risk"][:5]:
                    insights.append({"title": f"{d['district']} · relative activity indicator", "description": f"{d['cases']} synthetic case records; heuristic score {d['risk_score']}/100.", "severity": d["risk_band"], "evidence": f"Aggregate · {d['district']}"})
                for a in result["anomalies"]:
                    insights.append({"title": f"Volume deviation · {a['district']}", "description": f"{a['observed']} records against sample mean {a['baseline']} (z={a['z_score']}).", "severity": "Review", "evidence": f"Aggregate · {a['district']}"})
                return self.send_json({"items": insights, "disclaimer": "Descriptive demonstration signals only; not validated predictions."})
            if path == "/api/v1/quality":
                total = db.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
                coord = db.execute("SELECT COUNT(*) FROM cases WHERE latitude IS NOT NULL AND longitude IS NOT NULL").fetchone()[0]
                linked = db.execute("SELECT COUNT(DISTINCT case_id) FROM case_person").fetchone()[0]
                return self.send_json({"records": total, "coordinate_completeness": round(coord / max(total, 1) * 100, 1),
                                       "entity_link_coverage": round(linked / max(total, 1) * 100, 1), "protected_attributes_used": False,
                                       "data_classification": "SYNTHETIC_PUBLIC_DEMO", "auth_mode": "local_no_auth_demo",
                                       "controls": ["Synthetic dataset only", "Protected attributes excluded", "Case-person links carry confidence", "Evidence shown with assistant responses", "Audit events for selected actions"]})
            if path == "/api/v1/audit":
                return self.send_json({"items": rows(db, "SELECT * FROM audit_events ORDER BY id DESC LIMIT 100")})
        return self.send_json({"error": "not_found"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/v1/ask":
            return self.send_json({"error": "not_found"}, 404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 10_000:
                return self.send_json({"error": "invalid_request_size"}, 413)
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                return self.send_json({"error": "request_must_be_an_object"}, 400)
            question = str(body.get("question", ""))[:1000]
        except (TypeError, ValueError, json.JSONDecodeError):
            return self.send_json({"error": "invalid_json"}, 400)
        with db_session() as db:
            self.send_json(ask_demo(db, question))


def main() -> None:
    init_db(reset=os.environ.get("LUMEN_RESET_DEMO", "0") == "1")
    host = os.environ.get("LUMEN_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", os.environ.get("LUMEN_PORT", "8765")))
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    print("\nLUMEN showcase runtime is ready")
    print(f"  UI:      http://{host}:{port}")
    print(f"  API:     http://{host}:{port}/api/v1")
    print(f"  Health:  http://{host}:{port}/healthz")
    print(f"  DB:      {DB_PATH}")
    print("  MODE:    synthetic local showcase (not a KSP production system)\n")
    if os.environ.get("LUMEN_OPEN_BROWSER", "1") == "1":
        threading.Timer(0.8, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    try:
        server.serve_forever(poll_interval=0.4)
    except KeyboardInterrupt:
        print("\nShutting down LUMEN showcase...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
