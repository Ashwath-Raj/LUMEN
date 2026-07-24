import json
from sqlalchemy import select, text
from app.db.session import SessionLocal

def audit():
    with SessionLocal() as session:
        # 1. Cases
        cases_count = session.scalar(text("SELECT count(*) FROM cases"))
        cases_with_station = session.scalar(text("SELECT count(*) FROM cases WHERE police_station_id IS NOT NULL"))
        cases_with_police = session.scalar(text("SELECT count(*) FROM cases WHERE police_person_id IS NOT NULL"))
        
        # 2. FIRs
        firs_count = session.scalar(text("SELECT count(*) FROM firs"))
        firs_with_case = session.scalar(text("SELECT count(*) FROM firs WHERE case_id IS NOT NULL"))
        firs_districts = session.scalars(text("SELECT DISTINCT district FROM firs")).all()

        # 3. Hotspots
        hotspots_count = session.scalar(text("SELECT count(*) FROM hotspots"))
        
        # 4. Intelligence Leads
        leads_count = session.scalar(text("SELECT count(*) FROM intelligence_leads"))
        leads_sources = session.scalars(text("SELECT source_cases FROM intelligence_leads")).all()
        
        # 5. Signals
        signals_count = session.scalar(text("SELECT count(*) FROM signal_intercepts"))
        signals_cases = session.scalars(text("SELECT DISTINCT linked_case FROM signal_intercepts WHERE linked_case IS NOT NULL")).all()

        print(json.dumps({
            "cases": {
                "total": cases_count,
                "with_station": cases_with_station,
                "with_police": cases_with_police
            },
            "firs": {
                "total": firs_count,
                "with_case": firs_with_case,
                "districts": list(firs_districts)
            },
            "hotspots": {
                "total": hotspots_count
            },
            "intelligence_leads": {
                "total": leads_count,
                "sources_sample": list(leads_sources)[:5] if leads_sources else []
            },
            "signals": {
                "total": signals_count,
                "linked_cases": list(signals_cases)
            }
        }, indent=2))

if __name__ == "__main__":
    audit()
