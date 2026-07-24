from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are a Geospatial Intelligence Analyst for KSP.
Analyze coordinates and sector data to identify crime clustering, emerging areas, and patrol recommendations."""

class GeoIntelligenceSchema(BaseModel):
    hotspot_explanation: str = Field(description="Why this area is active")
    crime_clustering: str = Field(description="Observed patterns in the coordinates")
    emerging_areas: list[str] = Field(description="Zones likely to escalate")
    patrol_recommendations: list[str] = Field(description="Actionable deployment advice")
    confidence_score: int = Field(description="Confidence percentage (0-100)")

def build_prompt(sector_data: dict) -> str:
    return f"Generate Geo-Intelligence for:\n{sector_data}"
