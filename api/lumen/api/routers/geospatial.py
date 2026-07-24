"""
Geospatial router.

NOTE: These endpoints depended on the legacy JWT auth dependency
(get_current_operator / require_role) and the DB-backed ModuleService,
both deleted. Auth is Session 3 (Catalyst Authentication); the canonical
DB schema and its service layer are Session 2 of LUMEN_MASTER_SPEC_V3.md.
Stubbed to 501 until then (including /parameters POST, which previously
required an authenticated operator — that gate no longer exists to
enforce, so it is stubbed rather than left open).
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/geospatial", tags=["Geospatial"])

_NOT_IMPLEMENTED = "Not yet implemented — pending Session 2 (DB schema) and Session 3 (Catalyst Authentication) of LUMEN_MASTER_SPEC_V3.md"


@router.get("/hotspots")
def get_hotspots():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/sector-intel/{sector_id}")
def get_sector_intel(sector_id: str):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/parameters")
def get_parameters():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.post("/parameters")
def apply_parameters(params: dict):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)
