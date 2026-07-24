from sqlalchemy.orm import Session
from app.db.models import CaseORM, FIRORM, ArrestSurrenderORM, ChargesheetDetailsORM, AccusedORM, IncidentORM, HotspotORM, OperatorORM
from datetime import datetime, date

class CommandCenterService:
    def __init__(self, db: Session, operator=None):
        self._db = db
        self.operator = operator

    def get_summary(self) -> dict:
        # Determine authorized cases/FIRs
        case_query = self._db.query(CaseORM)
        fir_query = self._db.query(FIRORM)
        
        op = self.operator
        if op and op.role in ["analyst", "field"]:
            from app.db.models import UnitORM
            op_db = self._db.query(OperatorORM).filter(OperatorORM.id == op.id).first()
            if op_db and op_db.district_id:
                allowed_units = self._db.query(UnitORM.id).filter(UnitORM.district_id == op_db.district_id).all()
                allowed_unit_ids = {u[0] for u in allowed_units}
                case_query = case_query.filter(CaseORM.police_station_id.in_(allowed_unit_ids))
                
                # Filter FIRs by allowed cases
                allowed_case_ids = {c.id for c in case_query.all()}
                fir_query = fir_query.filter(FIRORM.case_id.in_(allowed_case_ids))
            else:
                case_query = case_query.filter(False) # No access
                fir_query = fir_query.filter(False)
                
        total_crimes = case_query.count()
        active_firs = fir_query.count()
        firs_today = fir_query.count()
        pending_investigations = case_query.filter(CaseORM.status == "Under Investigation").count()
        
        # Genuine DB logic for arrests pending. Distinct arrested accused vs total accused.
        from sqlalchemy import text
        if op and op.role in ["analyst", "field"]:
            total_accused = self._db.query(AccusedORM).filter(AccusedORM.case_master_id.in_(list(allowed_case_ids) or [None])).count()
            q = text("SELECT count(distinct a.id) FROM accused a JOIN arrest_surrender_accused asa ON a.id = asa.accused_id WHERE a.case_master_id = ANY(:case_ids)")
            distinct_arrested = self._db.execute(q, {"case_ids": list(allowed_case_ids) or [None]}).scalar()
        else:
            distinct_arrested = self._db.execute(text("SELECT count(distinct accused_id) FROM arrest_surrender_accused")).scalar()
            total_accused = self._db.query(AccusedORM).count()
            
        arrests_pending = max(0, total_accused - (distinct_arrested or 0))
        
        chargesheets_overdue = case_query.count() - case_query.filter(CaseORM.status == "Charge Sheeted").count()
        
        high_risk_areas = self._db.query(HotspotORM).filter(HotspotORM.intensity.in_(["critical", "high"])).count()
            
        active_ops = self._db.query(OperatorORM).filter(OperatorORM.status == "ACTIVE").count()
        total_ops = self._db.query(OperatorORM).count()
        officer_avail = f"{int((active_ops/total_ops)*100)}%" if total_ops > 0 else "N/A"
        
        # Original keys required by frontend
        res = {
            "totalCrimes": {"value": total_crimes, "trend": "N/A", "trendTone": "neutral"},
            "totalIncidents": {"value": total_crimes, "trend": "N/A", "trendTone": "neutral"},
            "activeCases": {"value": pending_investigations, "trend": "N/A", "trendTone": "neutral"},
            "pendingInvestigations": {"value": pending_investigations, "trend": "N/A", "trendTone": "neutral"},
            "highRiskAreas": {"value": high_risk_areas, "trend": "N/A", "trendTone": "neutral"},
            "openFirs": {"value": active_firs, "trend": "N/A", "trendTone": "neutral"},
            "openFIRs": {"value": active_firs, "trend": "N/A", "trendTone": "neutral"},
            "activeFirs": {"value": active_firs, "trend": "N/A", "trendTone": "neutral"},
            "activeFIRs": {"value": active_firs, "trend": "N/A", "trendTone": "neutral"},
            
            # Operational enhancements
            "firsRegisteredToday": {"value": firs_today, "trend": "N/A", "trendTone": "neutral"},
            "arrestsPending": {"value": arrests_pending, "trend": "N/A", "trendTone": "neutral"},
            "chargesheetsOverdue": {"value": chargesheets_overdue, "trend": "N/A", "trendTone": "neutral"},
            "highRiskCriminals": {"value": "N/A", "trend": "N/A", "trendTone": "neutral"},
            "activeGangs": {"value": "N/A", "trend": "N/A", "trendTone": "neutral"},
            "officerAvailability": {"value": officer_avail, "trend": "N/A", "trendTone": "neutral"},
            "districtCrimeComparison": {"value": "N/A", "trend": "N/A", "trendTone": "neutral"},
            "stationWorkloadComparison": {"value": "N/A", "trend": "N/A", "trendTone": "neutral"},
            "investigationCompletionRate": {"value": "N/A", "trend": "N/A", "trendTone": "neutral"},
            "averageInvestigationDuration": {"value": "N/A", "trend": "N/A", "trendTone": "neutral"},
            
            "commandActions": [
                { "id": "action-initiate", "label": "Initiate Investigation", "to": "/investigation" },
                { "id": "action-deploy", "label": "Deploy Resources", "to": "/operations" },
                { "id": "action-briefing", "label": "Generate Briefing", "to": "/analytics" }
            ]
        }
        return res
