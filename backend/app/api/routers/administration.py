"""Administration router — command-role restricted."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_role
from app.services.repositories.module_service import ModuleService

router = APIRouter(prefix="/administration", tags=["Administration"])

_admin = require_role("command")


@router.get("/security-posture")
def get_security_posture(_op=Depends(_admin), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_administration_security_posture()


@router.get("/personnel")
def get_personnel(_op=Depends(_admin), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_administration_personnel()


@router.get("/audit-log")
def get_audit_log(_op=Depends(_admin), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_administration_audit_log()
