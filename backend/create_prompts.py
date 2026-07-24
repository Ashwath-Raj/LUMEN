import os

prompts = {
    "crime_prediction.py": '''"""Prompt templates for Crime Prediction."""
SYSTEM_PROMPT = "You are a crime prediction analyst. Given historical incident data and sector context, predict the likelihood of future incidents."
def build_prompt(sector_data: dict) -> str:
    return f"Analyze the following sector data and predict crime hotspots: {sector_data}"
''',
    "fir_analysis.py": '''"""Prompt templates for FIR / Complaint NLP Analysis."""
SYSTEM_PROMPT = "You are an NLP extraction assistant specializing in First Information Reports (FIRs). Extract persons, locations, vehicles, and objects."
def build_prompt(fir_text: str) -> str:
    return f"Extract entities from the following FIR text: {fir_text}"
''',
    "network_analysis.py": '''"""Prompt templates for Criminal Network Analysis."""
SYSTEM_PROMPT = "You are an intelligence analyst specializing in criminal networks. Analyze nodes and edges to identify central figures and clusters."
def build_prompt(nodes: list, edges: list) -> str:
    return f"Analyze this network. Nodes: {nodes}, Edges: {edges}"
''',
    "intelligence_summarization.py": '''"""Prompt templates for Intelligence Summarization."""
SYSTEM_PROMPT = "You are a senior intelligence officer. Summarize case files, evidence, and field reports into a concise, actionable intelligence brief."
def build_prompt(case_data: dict) -> str:
    return f"Summarize the following case intelligence: {case_data}"
''',
    "incident_risk.py": '''"""Prompt templates for Incident Risk Assessment."""
SYSTEM_PROMPT = "You are a tactical operations risk assessor. Evaluate incoming incidents and assign a risk level (LOW, MEDIUM, HIGH, CRITICAL)."
def build_prompt(incident_data: dict) -> str:
    return f"Assess the risk of this incident: {incident_data}"
''',
    "report_generation.py": '''"""Prompt templates for Report Generation."""
SYSTEM_PROMPT = "You are a professional law enforcement report generator. Draft comprehensive reports based on provided case context and templates."
def build_prompt(template: str, context: dict) -> str:
    return f"Generate a report using template '{template}' with context: {context}"
''',
    "investigation_assistant.py": '''"""Prompt templates for Investigation Assistant."""
SYSTEM_PROMPT = "You are an AI investigation assistant. Help the investigator by suggesting next steps, identifying missing evidence, or proposing hypotheses."
def build_prompt(case_context: dict) -> str:
    return f"Suggest next investigation steps for this case: {case_context}"
''',
    "qa_case_data.py": '''"""Prompt templates for Question Answering over case data."""
SYSTEM_PROMPT = "You are a data retrieval assistant. Answer questions precisely based only on the provided case data context."
def build_prompt(question: str, context: dict) -> str:
    return f"Context: {context}\\n\\nQuestion: {question}\\nAnswer:"
'''
}

for filename, content in prompts.items():
    with open(f"app/ai/prompts/{filename}", "w", encoding="utf-8") as f:
        f.write(content)
