from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are drafting an official KSP Intelligence Report.
Generate professional, accurate, and concise sections suitable for Morning Briefings, Cyber Crime Reports, or Daily Crime Reports."""

class ReportSchema(BaseModel):
    title: str = Field(description="Official Report Title")
    critical_cases: list[str] = Field(description="High priority cases")
    district_hotspots: list[str] = Field(description="Emerging threat areas")
    repeat_offenders_flagged: list[str] = Field(description="Habitual criminals detected")
    executive_summary: str = Field(description="Professional briefing summary")

def build_prompt(template: str, context_data: dict) -> str:
    return f"Draft a {template} using this data:\n{context_data}"
