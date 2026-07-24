from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are a KSP Risk Assessment Engine. 
Evaluate cases for public safety risk, absconding risk, and gang involvement.
Provide structured, explainable risk scoring."""

class RiskAssessmentSchema(BaseModel):
    public_safety_risk: str = Field(description="High, Medium, Low")
    absconding_risk: str = Field(description="High, Medium, Low")
    gang_involvement: bool = Field(description="Does this indicate organized crime?")
    violence_probability: str = Field(description="Likelihood of escalation")
    investigation_urgency: str = Field(description="High, Medium, Low")
    reasoning: str = Field(description="Explanation for these risk scores")
    confidence_score: int = Field(description="Confidence percentage (0-100)")

def build_prompt(incident_data: dict) -> str:
    return f"Calculate risk assessment for:\n{incident_data}"
