import asyncio
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
