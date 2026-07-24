"""Intelligence router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_operator, require_role
from app.services.repositories.module_service import ModuleService

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])

_analyst = require_role("analyst", "command")


@router.get("/workbench")
def get_workbench(_op=Depends(require_role("analyst", "command", "field")), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_intelligence_workbench()


@router.post("/query")
async def submit_query(body: dict, _op=Depends(_analyst), db: Session = Depends(get_db)):
    query_text = body.get("query", "")
    # Retrieve real active cases for context
    module_service = ModuleService(db, operator=_op)
    active_cases = module_service._cases.list_active()
    
    # Build a concise context dictionary to prevent exceeding token limits
    context_data = []
    for c in active_cases[:15]:
        context_data.append({
            "id": c.id,
            "status": c.status,
            "bns_section": c.case_metadata.get("bns_section", "N/A") if c.case_metadata else "N/A"
        })
        
    try:
        from app.services.graph_service import Neo4jGraphService
        graph_data = Neo4jGraphService().get_evidence_nexus()
    except Exception:
        graph_data = {"nodes": [], "edges": []}
        
    try:
        res = await module_service.ai.qa_over_case_data(
            query_text, 
            {
                "active_cases": context_data,
                "graph_relationships": graph_data
            }
        )
        return res
    except Exception as e:
        return {
            "answer": f"Intelligence Engine Unavailable: {str(e)}",
            "confidence_score": 0,
            "evidence_used": []
        }

from app.dependencies.auth import get_current_operator, require_role

@router.get("/leads/{session_id}")
def get_leads(session_id: str, _op=Depends(require_role("analyst", "command", "field")), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_intelligence_leads()
