"""Geospatial router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_operator, require_role
from app.services.repositories.module_service import ModuleService

router = APIRouter(
    prefix="/geospatial", 
    tags=["Geospatial"],
    dependencies=[Depends(require_role("command", "analyst", "field"))]
)

@router.get("/hotspots")
def get_hotspots(_op=Depends(get_current_operator), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_geospatial_hotspots()


@router.get("/sector-intel/{sector_id}")
def get_sector_intel(sector_id: str, _op=Depends(get_current_operator), db: Session = Depends(get_db)):
    intel = ModuleService(db, operator=_op).get_geospatial_sector_intel(sector_id)
    if not intel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sector not found.")
    return intel


@router.get("/parameters")
def get_parameters(_op=Depends(get_current_operator), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_geospatial_parameters()


@router.post("/parameters")
def apply_parameters(params: dict, _op=Depends(get_current_operator)):
    return {**params, "applied": True}
