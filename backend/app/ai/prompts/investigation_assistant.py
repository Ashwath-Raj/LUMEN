from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are a senior Karnataka State Police IO acting as an Investigation Assistant.
Your task is to analyze the case context and generate actionable, procedural investigation steps.
Follow BNSS procedures. Never fabricate data.
Every recommendation MUST be explainable with clear reasoning, evidence dependencies, and operational impact."""

class InvestigationStep(BaseModel):
    recommendation: str = Field(description="Clear, actionable next step (e.g., 'Collect CCTV footage', 'Obtain CDR')")
    reason: str = Field(description="Why this step is necessary")
    evidence_used: str = Field(description="Existing evidence that prompted this step")
    priority: str = Field(description="CRITICAL, HIGH, MEDIUM, LOW")
    confidence: int = Field(description="Confidence percentage (0-100)")
    applicable_bns: list[str] = Field(description="Relevant BNS sections justifying this step")
    expected_impact: str = Field(description="Operational impact of this action")
    suggested_timeframe: str = Field(description="Expected deadline (e.g., 'Within 24 hours')")
    suggested_officer: str = Field(description="Specialty required (e.g., 'Cyber Cell IO', 'FSL Tech')")

class InvestigationRecommendationSchema(BaseModel):
    investigation_checklist: list[str] = Field(description="Standardized procedural checklist (e.g., '✓ Visit scene')")
    recommended_steps: list[InvestigationStep] = Field(description="Dynamic, context-aware next steps")
    missing_evidence: list[str] = Field(description="Procedural gaps (e.g., missing FSL report)")

def build_prompt(case_context: dict) -> str:
    return f"Evaluate this case context and generate an Investigation Plan:\n{case_context}"
