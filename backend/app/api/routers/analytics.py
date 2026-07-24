"""Analytics router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_operator
from app.services.repositories.module_service import ModuleService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/statistics")
def get_statistics(_op=Depends(get_current_operator), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_analytics_statistics()


@router.get("/case-files")
def get_case_files(_op=Depends(get_current_operator), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_analytics_case_files()


@router.get("/evidence-vault")
def get_evidence_vault(_op=Depends(get_current_operator), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_analytics_evidence_vault()


@router.get("/field-reports")
def get_field_reports(_op=Depends(get_current_operator), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_analytics_field_reports()


@router.get("/signal-intelligence")
def get_signal_intelligence(_op=Depends(get_current_operator), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_analytics_signal_intelligence()


@router.get("/personnel")
def get_personnel(_op=Depends(get_current_operator), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_analytics_personnel()


@router.get("/archived")
def get_archived(_op=Depends(get_current_operator), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_analytics_archived()
