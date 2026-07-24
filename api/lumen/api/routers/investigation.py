"""
Investigation router.

NOTE: These endpoints depended on the legacy JWT auth dependency
(get_current_operator / require_role), the DB-backed ModuleService, and
the Gemini AI service — all deleted. Auth is Session 3 (Catalyst
Authentication); the canonical DB schema is Session 2; the QuickML AI
orchestrator is Session 14 of LUMEN_MASTER_SPEC_V3.md. Stubbed to 501
until then.
"""
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/investigation", tags=["Investigation"])

_NOT_IMPLEMENTED = "Not yet implemented — pending Session 2 (DB schema), Session 3 (Catalyst Authentication), and Session 14 (QuickML AI orchestrator) of LUMEN_MASTER_SPEC_V3.md"


@router.get("/cases")
def get_cases():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/cases/{case_id}/reports")
def get_case_reports(case_id: str):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/cases/{case_id}")
async def get_case(case_id: str):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/suspects")
def get_suspects():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/watchlist")
def get_watchlist():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/evidence-locker")
def get_evidence_locker():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/fir-intelligence/{fir_id}")
def get_fir_intelligence(fir_id: str):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.post("/fir-intelligence")
async def process_fir_intelligence(file: UploadFile = File(...)):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/interviews/{interview_id}")
def get_interview(interview_id: str):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/forensics/{device_id}")
def get_forensics(device_id: str):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/archive")
def get_archive():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)
