"""
Dashboard router.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_operator
from app.services.repositories.module_service import ModuleService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_summary(_op=Depends(get_current_operator), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_dashboard_summary()


@router.get("/crime-trend")
def get_crime_trend(_op=Depends(get_current_operator), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_dashboard_crime_trend()


@router.get("/alerts")
def get_alerts(_op=Depends(get_current_operator), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_dashboard_alerts()


@router.get("/heatmap")
def get_heatmap(_op=Depends(get_current_operator), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_dashboard_heatmap()
