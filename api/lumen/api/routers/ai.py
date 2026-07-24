"""
AI ask surface — LUMEN_MASTER_SPEC_V3 §29.1 (`POST /ai/ask`), §16.2, §16.4.

The endpoint §16.4 names explicitly ("/ai/ask returns a template-assembled
insight ..."). Router stays §28 rule-1 thin: parse → one orchestrator call →
return the contract. The response body is the §16.2 output itself — the
serialized Insight(kind="summary") (§8 invariant 1: the answer, its
confidence and evidence never leave except inside an Insight). The request
body shape is not defined by the specification — minimal disclosed form:
{question, district_scope?}.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from lumen.ai.orchestrator import ask
from lumen.db.session import get_db

router = APIRouter(prefix="/ai", tags=["AI"])


class AskRequest(BaseModel):
    question: str
    district_scope: list[int] | None = None


@router.post("/ask")
def ai_ask(body: AskRequest, db: Session = Depends(get_db)) -> dict:
    outcome = ask(db, body.question, district_scope=body.district_scope)
    return outcome.insight.model_dump(mode="json")
