"""
Administration router — command-role restricted.

NOTE: These endpoints depended on the legacy JWT auth dependency
(require_role) and the DB-backed ModuleService, both deleted. Auth is
Session 3 (Catalyst Authentication); the canonical DB schema and its
service layer are Session 2 of LUMEN_MASTER_SPEC_V3.md. Stubbed to 501
until then.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/administration", tags=["Administration"])

_NOT_IMPLEMENTED = "Not yet implemented — pending Session 2 (DB schema) and Session 3 (Catalyst Authentication) of LUMEN_MASTER_SPEC_V3.md"


@router.get("/security-posture")
def get_security_posture():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/personnel")
def get_personnel():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/audit-log")
def get_audit_log():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)
