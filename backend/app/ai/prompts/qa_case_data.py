from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are an AI Investigation Copilot for KSP.
Answer officer questions based ONLY on the provided case data.
CRITICAL HALLUCINATION PREVENTION: If the answer is not in the records, YOU MUST explicitly return 'Information unavailable in current records.'
Never fabricate data."""

from typing import Optional

class QAIntelligenceSchema(BaseModel):
    answer: str = Field(description="Clear answer to the officer's question")
    confidence_score: Optional[int] = Field(default=None, description="Confidence percentage (0-100). Null if a reliable measurement is unavailable.")
    evidence_used: list[str] = Field(description="Facts from the context used to answer")

def build_prompt(question: str, case_data: dict) -> str:
    return f"Context:\n{case_data}\n\nQuestion: {question}"
