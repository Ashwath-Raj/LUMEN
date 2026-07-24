"""
Intelligence router.

NOTE: These endpoints depended on the legacy JWT auth dependency
(get_current_operator / require_role), the DB-backed ModuleService, the
legacy Neo4j graph service, and the Gemini AI service — all deleted. Auth
is Session 3 (Catalyst Authentication); the canonical DB schema is
Session 2; the QuickML AI orchestrator is Session 14 of
LUMEN_MASTER_SPEC_V3.md. Stubbed to 501 until then.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])

_NOT_IMPLEMENTED = "Not yet implemented — pending Session 2 (DB schema), Session 3 (Catalyst Authentication), and Session 14 (QuickML AI orchestrator) of LUMEN_MASTER_SPEC_V3.md"


@router.get("/workbench")
def get_workbench():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.post("/query")
async def submit_query(body: dict):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/leads/{session_id}")
def get_leads(session_id: str):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)
