"""
Operations router.

NOTE: These endpoints depended on the legacy JWT auth dependency
(get_current_operator / require_role), the DB-backed ModuleService, and
the Gemini AI service — all deleted. Auth is Session 3 (Catalyst
Authentication); the canonical DB schema is Session 2; the QuickML AI
orchestrator is Session 14 of LUMEN_MASTER_SPEC_V3.md. Stubbed to 501
until then.
"""
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/operations", tags=["Operations"])

_NOT_IMPLEMENTED = "Not yet implemented — pending Session 2 (DB schema), Session 3 (Catalyst Authentication), and Session 14 (QuickML AI orchestrator) of LUMEN_MASTER_SPEC_V3.md"


@router.get("/tactical-overview")
def get_tactical_overview():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/operators/{operator_id}")
@router.get("/dossier/{operator_id}")
def get_operator_dossier(operator_id: str):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.patch("/operators/{operator_id}/preferences")
@router.put("/dossier/{operator_id}/preferences")
def update_preferences(operator_id: str, preferences: dict):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.post("/fir-upload")
async def fir_upload(file: UploadFile = File(...)):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/suspects/{suspect_id}/records")
def get_suspect_records(suspect_id: str):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/suspects")
def get_suspects():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)
