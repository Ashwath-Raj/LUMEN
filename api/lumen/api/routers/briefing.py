"""
Case Intelligence Briefing endpoint — LUMEN_MASTER_SPEC_V3 §29.1, §26.1 row 16.

§29.1: "POST /cases/{id}/briefing — SmartBrowz PDF → Stratus URL (T2)."

Router stays §28 rule-1 thin: parse → one accelerator call → return. The
briefing is assembled + rendered by `accelerators.briefing` (the SmartBrowz
accelerator, consumed not duplicated); locally the swappable renderer produces
a deterministic Stratus stub URL, the real SmartBrowz+Stratus client slotting
in at deploy. The requesting user is supplied for the §4.3-rule-5 watermark;
the deployed Catalyst-Authentication binding of identity→user is a deployment
concern (as with /audit in Session 22), disclosed.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from lumen.accelerators import briefing as briefing_accel
from lumen.db.session import get_db

router = APIRouter(prefix="/cases", tags=["Briefing"])


class BriefingRequest(BaseModel):
    requesting_user: str


@router.post("/{case_id}/briefing")
def create_briefing(case_id: int, body: BriefingRequest,
                    db: Session = Depends(get_db)) -> dict:
    """Generate the Case Intelligence Briefing (SmartBrowz PDF → Stratus URL)."""
    try:
        return briefing_accel.generate_briefing(
            db, case_id, requesting_user=body.requesting_user)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
