"""Investigation router."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_operator, require_role
from app.services.repositories.module_service import ModuleService

router = APIRouter(prefix="/investigation", tags=["Investigation"])

_inv = require_role("analyst", "field", "command")


@router.get("/cases")
def get_cases(_op=Depends(_inv), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_investigation_cases()


@router.get("/cases/{case_id}/reports")
def get_case_reports(case_id: str, _op=Depends(_inv), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_investigation_case_reports(case_id)


@router.get("/cases/{case_id}")
async def get_case(case_id: str, _op=Depends(_inv), db: Session = Depends(get_db)):
    ms = ModuleService(db, operator=_op)
    case_data = ms.get_investigation_case(case_id)
    if not case_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
        
    try:
        # Generate genuine Gemini case summary
        ai_summary = await ms.ai.summarise_intelligence(case_id, case_data)
        case_data["summary"] = ai_summary
    except Exception as e:
        import logging
        logging.error(f"Failed to generate case summary: {e}")
        case_data["summary"] = "AI Summary Unavailable."
        
    return case_data


@router.get("/suspects")
def get_suspects(_op=Depends(_inv), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_investigation_suspects()


@router.get("/watchlist")
def get_watchlist(_op=Depends(_inv), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_investigation_watchlist()


@router.get("/evidence-locker")
def get_evidence_locker(_op=Depends(_inv), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_investigation_evidence_locker()


@router.get("/fir-intelligence/{fir_id}")
def get_fir_intelligence(fir_id: str, _op=Depends(_inv), db: Session = Depends(get_db)):
    result = ModuleService(db, operator=_op).get_investigation_fir_intelligence(fir_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FIR not found or access denied.")
    return result


@router.post("/fir-intelligence")
async def process_fir_intelligence(
                     file: UploadFile = File(...), 
                     _op=Depends(_inv),
                     db: Session = Depends(get_db)):
    if file.content_type not in ["text/plain", "text/csv", "application/json"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only text/plain, text/csv, and application/json are allowed.")
        
    content = await file.read()
    
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")
        
    text = content.decode('utf-8', errors='ignore')
    return await ModuleService(db, operator=_op).ai.analyse_fir_document(text)


@router.get("/interviews/{interview_id}")
def get_interview(interview_id: str, _op=Depends(_inv), db: Session = Depends(get_db)):
    result = ModuleService(db, operator=_op).get_investigation_interview(interview_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")
    return result


@router.get("/forensics/{device_id}")
def get_forensics(device_id: str, _op=Depends(_inv), db: Session = Depends(get_db)):
    result = ModuleService(db, operator=_op).get_investigation_forensics(device_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")
    return result


@router.get("/archive")
def get_archive(_op=Depends(_inv), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_investigation_archive()
