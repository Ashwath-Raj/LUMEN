from pydantic import BaseModel, Field

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
    return f"Analyze this intelligence graph:\nNodes: {nodes}\nEdges: {edges}"
