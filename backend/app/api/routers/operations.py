"""Operations router."""
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_operator, require_role
from app.services.repositories.module_service import ModuleService

router = APIRouter(prefix="/operations", tags=["Operations"])

_field = require_role("field", "command")


@router.get("/tactical-overview")
def get_tactical_overview(_op=Depends(_field), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_operations_tactical_overview()


@router.get("/operators/{operator_id}")
@router.get("/dossier/{operator_id}")
def get_operator_dossier(operator_id: str, _op=Depends(_field), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_operations_operator_dossier(operator_id)


@router.patch("/operators/{operator_id}/preferences")
@router.put("/dossier/{operator_id}/preferences")
def update_preferences(operator_id: str, preferences: dict,
                       _op=Depends(_field), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).update_operations_operator_preferences(operator_id, preferences)


@router.post("/fir-upload")
async def fir_upload(file: UploadFile = File(...), 
                     _op=Depends(_field),
                     db: Session = Depends(get_db)):
    # Validate MIME type
    if file.content_type not in ["text/plain", "text/csv", "application/json"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only text/plain, text/csv, and application/json are allowed.")
        
    content = await file.read()
    
    # Validate file size (max 5MB)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")
        
    text = content.decode('utf-8', errors='ignore')
    
    # We call the AI Service for NLP extraction on the FIR text.
    # The frontend expects the response to have "suspectPreviousRecords".
    ai_result = await ModuleService(db, operator=_op).ai.analyse_fir_document(text)
    
    # In a fully integrated system, the AI extraction would cross-reference the DB.
    # For now, we return the DB records if we have them, else mock data.
    records = ModuleService(db, operator=_op).get_operations_suspect_records()
    return {"success": True, "suspectPreviousRecords": records, "aiAnalysis": ai_result}



@router.get("/suspects/{suspect_id}/records")
def get_suspect_records(suspect_id: str, _op=Depends(_field), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_operations_suspect_records()


@router.get("/suspects")
def get_suspects(_op=Depends(_field), db: Session = Depends(get_db)):
    return ModuleService(db, operator=_op).get_operations_suspects()
