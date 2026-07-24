from sqlalchemy.orm import Session
from lumen.db.models.legacy_models import FIRORM, CaseORM, PersonnelORM

class ExecutiveDashboardService:
    def __init__(self, db: Session):
        self._db = db

    def generate_district_analytics(self) -> dict:
        total_firs = self._db.query(FIRORM).count()
        pending_investigations = self._db.query(CaseORM).filter(CaseORM.status == "Under Investigation").count()
        
        total_ops = self._db.query(PersonnelORM).count()
        if total_ops > 0:
            deployed = self._db.query(PersonnelORM).filter(PersonnelORM.status == "DEPLOYED").count()
            officer_utilization = f"{int((deployed/total_ops)*100)}%"
        else:
            officer_utilization = "N/A"
            
        return {
            "totalFIRs": total_firs,
            "crimeGrowth": "N/A",
            "clearanceRate": "N/A",
            "officerUtilization": officer_utilization,
            "averageInvestigationDuration": "N/A",
            "pendingInvestigations": pending_investigations,
            "repeatOffenderIndex": 0.0,
            "gangActivityScore": 0.0,
            "hotspotScore": 0.0,
            "operationalSummary": "Unavailable"
        }
        
    def generate_executive_briefing(self) -> dict:
        return {
            "statewideSituation": "Unavailable",
            "emergingCrimePatterns": [],
            "districtsRequiringAttention": [],
            "resourceShortages": [],
            "officerWorkloadImbalance": "Unavailable",
            "organizedCrimeObservations": "Unavailable",
            "recommendations": []
        }
