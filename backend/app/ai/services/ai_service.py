from app.ai.providers.factory import get_ai_provider
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
