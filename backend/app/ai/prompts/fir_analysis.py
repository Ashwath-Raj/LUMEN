from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are an experienced Karnataka State Police Investigating Officer.
Your task is to analyze FIRs and translate them into Intelligence-Grade structured data.
Use official KSP terminology, Bharatiya Nyaya Sanhita (BNS), BNSS, and BSA frameworks.
Rules:
1. NEVER invent or fabricate names, addresses, phones, vehicles, or BNS sections.
2. If data is missing, output 'Information unavailable in current records.'
3. Provide a strict Confidence Score (0-100) for your extraction."""

from typing import Optional, List, Dict, Any

class DocumentInfo(BaseModel):
    caseId: str
    district: str
    year: str
    firNo: str

class ExtractedEntity(BaseModel):
    id: str
    label: str
    type: str
    confidence: Optional[int] = Field(default=None, description="0-100 confidence score, null if unavailable")

class LinkedNetwork(BaseModel):
    nodes: List[Dict[str, str]]
    edges: List[Dict[str, str]]

class FIRIntelligenceSchema(BaseModel):
    document: DocumentInfo
    extractedEntities: List[ExtractedEntity]
    linkedNetwork: LinkedNetwork
    suspectPreviousRecords: List[Dict[str, Any]] = []

def build_prompt(fir_text: str) -> str:
    return f"Analyze the following FIR and extract intelligence:\n{fir_text}"
