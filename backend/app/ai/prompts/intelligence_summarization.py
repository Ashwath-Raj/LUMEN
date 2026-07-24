from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are drafting a Senior Officer Briefing.
Summarize the case clearly, highlighting current status, pending actions, and risks.
Use professional police reporting style."""

class BriefingSchema(BaseModel):
    incident_summary: str
    evidence_collected: list[str]
    current_status: str
    pending_actions: list[str]
    risk_assessment: str
    recommended_next_step: str

def build_prompt(case_data: dict) -> str:
    return f"Draft a Case Summary briefing for:\n{case_data}"
