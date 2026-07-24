import os

def build_phase_4():
    base_dir = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN\backend\app\ai"
    
    # ---------------------------------------------------------
    # 1. GEMINI PROVIDER
    # ---------------------------------------------------------
    gemini_path = os.path.join(base_dir, "providers", "gemini_provider.py")
    with open(gemini_path, 'w', encoding='utf-8') as f:
        f.write('''import json
import logging
from typing import Any, Optional
from google import genai
from google.genai.types import GenerateContentConfig
from google.genai.errors import APIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.ai.interfaces.ai_provider import IAIProvider
from app.ai.providers.mock_provider import MockProvider
from app.ai.utils.json_parser import extract_json_from_text

logger = logging.getLogger(__name__)

class GeminiProvider(IAIProvider):
    """
    Live Gemini Provider using google-genai SDK.
    Upgraded for Phase 4 to natively support Pydantic response schemas for hallucination prevention.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model_name = settings.GEMINI_MODEL
        self.mock_fallback = MockProvider()
        
        # Initialize GenAI Client
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self.client = None
        else:
            self.client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIError, Exception)),
        reraise=True
    )
    async def _call_gemini_api(self, prompt: str, system_instruction: Optional[str] = None, response_schema: Any = None) -> str:
        if not self.client:
            raise ValueError("Gemini API key is not configured or client failed to initialize.")
            
        kwargs = {"temperature": 0.2}
        if system_instruction:
            kwargs["system_instruction"] = system_instruction
            
        if response_schema:
            kwargs["response_mime_type"] = "application/json"
            kwargs["response_schema"] = response_schema
            
        config = GenerateContentConfig(**kwargs)
            
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        return response.text

    async def generate_text(self, prompt: str, context: Optional[dict[str, Any]] = None) -> str:
        """Generates a raw text response given a prompt and optional context."""
        try:
            system_instruction = context.get("system_prompt") if context else None
            return await self._call_gemini_api(prompt, system_instruction)
        except Exception as e:
            logger.warning(f"Gemini API text generation failed: {e}. Falling back to MockProvider.")
            return await self.mock_fallback.generate_text(prompt, context)

    async def generate_structured_data(self, prompt: str, context: Optional[dict[str, Any]] = None) -> dict:
        """Generates structured JSON data natively using response_schema."""
        system_instruction = context.get("system_prompt") if context else None
        response_schema = context.get("response_schema") if context else None
        
        try:
            raw_response = await self._call_gemini_api(prompt, system_instruction, response_schema)
        except Exception as e:
            logger.warning(f"Gemini API structured generation failed: {e}. Falling back to MockProvider.")
            return await self.mock_fallback.generate_structured_data(prompt, context)
            
        try:
            return extract_json_from_text(raw_response)
        except json.JSONDecodeError:
            strict_prompt = prompt + "\\n\\nCRITICAL INSTRUCTION: You must return ONLY valid, parseable JSON."
            try:
                raw_response_retry = await self._call_gemini_api(strict_prompt, system_instruction, response_schema)
                return extract_json_from_text(raw_response_retry)
            except Exception as e:
                logger.error(f"Gemini API strict JSON parsing failed on retry: {e}. Falling back to MockProvider.")
                return await self.mock_fallback.generate_structured_data(prompt, context)
''')

    # ---------------------------------------------------------
    # 2. PROMPTS
    # ---------------------------------------------------------
    prompts_dir = os.path.join(base_dir, "prompts")
    
    # fir_analysis.py
    with open(os.path.join(prompts_dir, "fir_analysis.py"), 'w', encoding='utf-8') as f:
        f.write('''from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are an experienced Karnataka State Police Investigating Officer.
Your task is to analyze FIRs and translate them into Intelligence-Grade structured data.
Use official KSP terminology, Bharatiya Nyaya Sanhita (BNS), BNSS, and BSA frameworks.
Rules:
1. NEVER invent or fabricate names, addresses, phones, vehicles, or BNS sections.
2. If data is missing, output 'Information unavailable in current records.'
3. Provide a strict Confidence Score (0-100) for your extraction."""

class FIRIntelligenceSchema(BaseModel):
    fir_number: str = Field(description="FIR or Crime Number")
    district: str = Field(description="District of occurrence")
    police_station: str = Field(description="Reporting Police Station")
    date_time: str = Field(description="Date and time of incident")
    bns_sections: list[str] = Field(description="Bharatiya Nyaya Sanhita Sections applied")
    accused: list[str] = Field(description="Names of accused individuals")
    victims: list[str] = Field(description="Names of victims")
    vehicles: list[str] = Field(description="Vehicle registrations (e.g. KA-01-AB-1234)")
    evidence: list[str] = Field(description="Physical or digital evidence mentioned")
    timeline: list[str] = Field(description="Chronological events")
    human_summary: str = Field(description="Professional KSP police summary of the incident")
    confidence_score: int = Field(description="0-100 confidence score of the extraction accuracy")

def build_prompt(fir_text: str) -> str:
    return f"Analyze the following FIR and extract intelligence:\\n{fir_text}"
''')

    # investigation_assistant.py
    with open(os.path.join(prompts_dir, "investigation_assistant.py"), 'w', encoding='utf-8') as f:
        f.write('''from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are a senior Karnataka State Police IO acting as an Investigation Assistant.
Your task is to analyze the case context and generate actionable, procedural investigation steps.
Follow BNSS procedures. Never fabricate data.
Every recommendation MUST be explainable with clear reasoning and evidence dependencies."""

class InvestigationStep(BaseModel):
    recommendation: str = Field(description="Clear, actionable next step (e.g., 'Collect CCTV footage', 'Obtain CDR')")
    reason: str = Field(description="Why this step is necessary")
    evidence_used: str = Field(description="Existing evidence that prompted this step")
    priority: str = Field(description="High, Medium, or Low")
    confidence: int = Field(description="Confidence percentage (0-100)")

class InvestigationRecommendationSchema(BaseModel):
    investigation_checklist: list[str] = Field(description="Standardized procedural checklist (e.g., '✓ Visit scene')")
    recommended_steps: list[InvestigationStep] = Field(description="Dynamic, context-aware next steps")
    missing_evidence: list[str] = Field(description="Procedural gaps (e.g., missing FSL report)")

def build_prompt(case_context: dict) -> str:
    return f"Evaluate this case context and generate an Investigation Plan:\\n{case_context}"
''')

    # network_analysis.py
    with open(os.path.join(prompts_dir, "network_analysis.py"), 'w', encoding='utf-8') as f:
        f.write('''from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are a Karnataka State Police Intelligence Analyst specializing in Organized Crime.
Analyze the provided Neo4j graph nodes and edges to detect criminal syndicates, repeat offenders, and network hubs.
Rules:
1. Do not invent associations that do not exist in the graph edges.
2. Provide a 0-100 confidence score for the network evaluation."""

class NetworkIntelligenceSchema(BaseModel):
    key_suspects: list[str] = Field(description="Central figures with highest degree centrality")
    gang_hierarchy: str = Field(description="Explanation of the syndicate structure")
    communication_hubs: list[str] = Field(description="Shared phones or locations")
    repeat_offenders: list[str] = Field(description="Suspects linked to multiple cases")
    confidence_score: int = Field(description="Confidence percentage (0-100)")

def build_prompt(nodes: list, edges: list) -> str:
    return f"Analyze this intelligence graph:\\nNodes: {nodes}\\nEdges: {edges}"
''')

    # incident_risk.py
    with open(os.path.join(prompts_dir, "incident_risk.py"), 'w', encoding='utf-8') as f:
        f.write('''from pydantic import BaseModel, Field

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
    return f"Calculate risk assessment for:\\n{incident_data}"
''')

    # qa_case_data.py
    with open(os.path.join(prompts_dir, "qa_case_data.py"), 'w', encoding='utf-8') as f:
        f.write('''from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are an AI Investigation Copilot for KSP.
Answer officer questions based ONLY on the provided case data.
CRITICAL HALLUCINATION PREVENTION: If the answer is not in the records, YOU MUST explicitly return 'Information unavailable in current records.'
Never fabricate data."""

class QAIntelligenceSchema(BaseModel):
    answer: str = Field(description="Clear answer to the officer's question")
    confidence_score: int = Field(description="Confidence percentage (0-100)")
    evidence_used: list[str] = Field(description="Facts from the context used to answer")

def build_prompt(question: str, case_data: dict) -> str:
    return f"Context:\\n{case_data}\\n\\nQuestion: {question}"
''')

    # intelligence_summarization.py
    with open(os.path.join(prompts_dir, "intelligence_summarization.py"), 'w', encoding='utf-8') as f:
        f.write('''from pydantic import BaseModel, Field

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
    return f"Draft a Case Summary briefing for:\\n{case_data}"
''')

    # report_generation.py
    with open(os.path.join(prompts_dir, "report_generation.py"), 'w', encoding='utf-8') as f:
        f.write('''from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are drafting an official KSP Intelligence Report.
Generate professional, accurate, and concise sections suitable for Morning Briefings, Cyber Crime Reports, or Daily Crime Reports."""

class ReportSchema(BaseModel):
    title: str = Field(description="Official Report Title")
    critical_cases: list[str] = Field(description="High priority cases")
    district_hotspots: list[str] = Field(description="Emerging threat areas")
    repeat_offenders_flagged: list[str] = Field(description="Habitual criminals detected")
    executive_summary: str = Field(description="Professional briefing summary")

def build_prompt(template: str, context_data: dict) -> str:
    return f"Draft a {template} using this data:\\n{context_data}"
''')

    # crime_prediction.py
    with open(os.path.join(prompts_dir, "crime_prediction.py"), 'w', encoding='utf-8') as f:
        f.write('''from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are a Geospatial Intelligence Analyst for KSP.
Analyze coordinates and sector data to identify crime clustering, emerging areas, and patrol recommendations."""

class GeoIntelligenceSchema(BaseModel):
    hotspot_explanation: str = Field(description="Why this area is active")
    crime_clustering: str = Field(description="Observed patterns in the coordinates")
    emerging_areas: list[str] = Field(description="Zones likely to escalate")
    patrol_recommendations: list[str] = Field(description="Actionable deployment advice")
    confidence_score: int = Field(description="Confidence percentage (0-100)")

def build_prompt(sector_data: dict) -> str:
    return f"Generate Geo-Intelligence for:\\n{sector_data}"
''')

    # ---------------------------------------------------------
    # 3. AI SERVICE
    # ---------------------------------------------------------
    ai_service_path = os.path.join(base_dir, "services", "ai_service.py")
    with open(ai_service_path, 'w', encoding='utf-8') as f:
        f.write('''from app.ai.providers.factory import get_ai_provider
from app.ai.prompts import (
    crime_prediction, fir_analysis, network_analysis, intelligence_summarization,
    incident_risk, report_generation, investigation_assistant, qa_case_data
)

class AIService:
    def __init__(self):
        self.provider = get_ai_provider()

    def _sanitize_input(self, text: str) -> str:
        if not text: return ""
        for tag in ["<system>", "</system>", "<instruction>", "</instruction>", "[SYSTEM]", "Ignore previous instructions"]:
            text = text.replace(tag, "")
        return text

    async def predict_crime_hotspots(self, sector_data: dict) -> dict:
        prompt = crime_prediction.build_prompt(sector_data)
        context = {"task_type": "crime_prediction", "system_prompt": crime_prediction.SYSTEM_PROMPT, "response_schema": crime_prediction.GeoIntelligenceSchema}
        return await self.provider.generate_structured_data(prompt, context)

    async def analyse_fir_document(self, text: str) -> dict:
        prompt = fir_analysis.build_prompt(self._sanitize_input(text))
        context = {"task_type": "fir_analysis", "system_prompt": fir_analysis.SYSTEM_PROMPT, "response_schema": fir_analysis.FIRIntelligenceSchema}
        return await self.provider.generate_structured_data(prompt, context)

    async def analyse_criminal_network(self, nodes: list, edges: list) -> dict:
        prompt = network_analysis.build_prompt(nodes, edges)
        context = {"task_type": "network_analysis", "system_prompt": network_analysis.SYSTEM_PROMPT, "response_schema": network_analysis.NetworkIntelligenceSchema}
        return await self.provider.generate_structured_data(prompt, context)

    async def summarise_intelligence(self, case_id: str, case_data: dict) -> str:
        # Note: Frontend might expect a string, but we can return structured JSON serialized as string or dict.
        prompt = intelligence_summarization.build_prompt(case_data)
        context = {"task_type": "intelligence_summarization", "system_prompt": intelligence_summarization.SYSTEM_PROMPT, "response_schema": intelligence_summarization.BriefingSchema}
        result = await self.provider.generate_structured_data(prompt, context)
        # Fallback to string if frontend expects it
        import json
        return json.dumps(result, indent=2)

    async def assess_incident_risk(self, incident_data: dict) -> dict:
        prompt = incident_risk.build_prompt(incident_data)
        context = {"task_type": "incident_risk", "system_prompt": incident_risk.SYSTEM_PROMPT, "response_schema": incident_risk.RiskAssessmentSchema}
        return await self.provider.generate_structured_data(prompt, context)

    async def generate_report(self, template: str, context_data: dict) -> str:
        prompt = report_generation.build_prompt(template, context_data)
        context = {"task_type": "report_generation", "system_prompt": report_generation.SYSTEM_PROMPT, "response_schema": report_generation.ReportSchema}
        result = await self.provider.generate_structured_data(prompt, context)
        import json
        return json.dumps(result, indent=2)

    async def investigation_assistant(self, case_context: dict) -> dict:
        prompt = investigation_assistant.build_prompt(case_context)
        context = {"task_type": "investigation_assistant", "system_prompt": investigation_assistant.SYSTEM_PROMPT, "response_schema": investigation_assistant.InvestigationRecommendationSchema}
        return await self.provider.generate_structured_data(prompt, context)

    async def qa_over_case_data(self, question: str, case_data: dict) -> dict:
        prompt = qa_case_data.build_prompt(self._sanitize_input(question), case_data)
        context = {"task_type": "intelligence_query", "system_prompt": qa_case_data.SYSTEM_PROMPT, "response_schema": qa_case_data.QAIntelligenceSchema}
        return await self.provider.generate_structured_data(prompt, context)
''')

    # ---------------------------------------------------------
    # 4. MOCK PROVIDER
    # ---------------------------------------------------------
    mock_provider_path = os.path.join(base_dir, "providers", "mock_provider.py")
    with open(mock_provider_path, 'w', encoding='utf-8') as f:
        f.write('''import asyncio
import logging
from typing import Any, Optional
from app.ai.interfaces.ai_provider import IAIProvider

logger = logging.getLogger(__name__)

class MockProvider(IAIProvider):
    """
    Offline MockProvider guaranteeing schema compliance with Phase 4 structures.
    """
    async def generate_text(self, prompt: str, context: Optional[dict[str, Any]] = None) -> str:
        await asyncio.sleep(0.5)
        return "Mock Intelligence Summary: Case involves multiple interconnected suspect nodes in Bengaluru."

    async def generate_structured_data(self, prompt: str, context: Optional[dict[str, Any]] = None) -> dict:
        await asyncio.sleep(0.5)
        task = context.get("task_type", "") if context else ""
        
        if task == "fir_analysis":
            return {
                "fir_number": "Cr.No 145/2026",
                "district": "Bengaluru City",
                "police_station": "Peenya PS",
                "date_time": "14 July 2026 21:15",
                "bns_sections": ["BNS 303(2)", "BNS 305"],
                "accused": ["Rahul Sharma"],
                "victims": ["Kiran Reddy"],
                "vehicles": ["KA-01-AB-1234"],
                "evidence": ["CCTV Footage"],
                "timeline": ["Incident", "FIR Registered"],
                "human_summary": "Vehicle theft reported near Peenya.",
                "confidence_score": 95
            }
        elif task == "investigation_assistant":
            return {
                "investigation_checklist": ["✓ Visit scene", "✓ Photograph evidence", "✓ Check CCTV"],
                "recommended_steps": [{
                    "recommendation": "Recover nearby CCTV footage.",
                    "reason": "Incident occurred near commercial establishments.",
                    "evidence_used": "Incident location and time",
                    "priority": "High",
                    "confidence": 92
                }],
                "missing_evidence": ["Forensic fingerprint report"]
            }
        elif task == "network_analysis":
            return {
                "key_suspects": ["Rahul Sharma"],
                "gang_hierarchy": "Suspect is a member of the Peenya Vehicle Network.",
                "communication_hubs": ["9999999999"],
                "repeat_offenders": ["Amit Kumar"],
                "confidence_score": 88
            }
        elif task == "incident_risk":
            return {
                "public_safety_risk": "Low",
                "absconding_risk": "High",
                "gang_involvement": True,
                "violence_probability": "Low",
                "investigation_urgency": "High",
                "reasoning": "Suspect is part of an organized theft ring with a history of absconding.",
                "confidence_score": 91
            }
        elif task == "intelligence_query":
            return {
                "answer": "The suspect fled towards Tumakuru Road.",
                "confidence_score": 96,
                "evidence_used": ["Complainant Statement"]
            }
        elif task == "intelligence_summarization":
            return {
                "incident_summary": "Vehicle theft by organized network.",
                "evidence_collected": ["CCTV"],
                "current_status": "Under Investigation",
                "pending_actions": ["Arrest Suspect"],
                "risk_assessment": "High absconding risk",
                "recommended_next_step": "Deploy search team"
            }
        elif task == "report_generation":
            return {
                "title": "Daily Crime Intelligence Brief",
                "critical_cases": ["Cr.No 145/2026"],
                "district_hotspots": ["Peenya"],
                "repeat_offenders_flagged": ["Rahul Sharma"],
                "executive_summary": "Routine operations in Bengaluru City with focus on vehicle theft."
            }
        elif task == "crime_prediction":
            return {
                "hotspot_explanation": "Dense commercial area with historically high property crime.",
                "crime_clustering": "Clustered near major transport hubs.",
                "emerging_areas": ["Whitefield", "Electronic City"],
                "patrol_recommendations": ["Increase night patrols along Tumakuru Road"],
                "confidence_score": 85
            }
        
        # Default fallback
        return {"result": "Success", "confidence": 100}
''')

if __name__ == "__main__":
    build_phase_4()
