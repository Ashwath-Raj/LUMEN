"""
Analytics router.

NOTE: These endpoints depended on the legacy JWT auth dependency
(get_current_operator) and the DB-backed ModuleService, both deleted.
Auth is Session 3 (Catalyst Authentication); the canonical DB schema and
its service layer are Session 2 of LUMEN_MASTER_SPEC_V3.md. Stubbed to
501 until then.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/analytics", tags=["Analytics"])

_NOT_IMPLEMENTED = "Not yet implemented — pending Session 2 (DB schema) and Session 3 (Catalyst Authentication) of LUMEN_MASTER_SPEC_V3.md"


@router.get("/statistics")
def get_statistics():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/case-files")
def get_case_files():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/evidence-vault")
def get_evidence_vault():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/field-reports")
def get_field_reports():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/signal-intelligence")
def get_signal_intelligence():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/personnel")
def get_personnel():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/archived")
def get_archived():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)
