"""
Dashboard router.

NOTE: These endpoints depended on the legacy JWT auth dependency
(get_current_operator) and the DB-backed ModuleService, both deleted.
Auth is Session 3 (Catalyst Authentication); the canonical DB schema and
its service layer are Session 2 of LUMEN_MASTER_SPEC_V3.md. Stubbed to
501 until then.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

_NOT_IMPLEMENTED = "Not yet implemented — pending Session 2 (DB schema) and Session 3 (Catalyst Authentication) of LUMEN_MASTER_SPEC_V3.md"


@router.get("/summary")
def get_summary():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/crime-trend")
def get_crime_trend():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/alerts")
def get_alerts():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/heatmap")
def get_heatmap():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)
