from __future__ import annotations

from typing import Any

from app.core.config import settings


_driver_instance = None

def init_neo4j_driver():
    global _driver_instance
    if not settings.NEO4J_ENABLED:
        return
    if _driver_instance is None:
        from neo4j import GraphDatabase
        try:
            _driver_instance = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
        except Exception as e:
            import logging
            logging.error(f"Failed to initialize Neo4j global driver: {e}")
            _driver_instance = None

def close_neo4j_driver():
    global _driver_instance
    if _driver_instance is not None:
        _driver_instance.close()
        _driver_instance = None

class Neo4jGraphService:
    """Service for genuine Neo4j Graph queries."""

    def __init__(self, uri: str | None = None, user: str | None = None, password: str | None = None):
        self.enabled = settings.NEO4J_ENABLED

    def _get_driver(self):
        return _driver_instance

    def get_case_network(self, case_id: str) -> dict:
        """Returns the local graph neighborhood for a specific case."""
        if not self.enabled:
            return {"nodes": [], "edges": []}

        driver = self._get_driver()
        if not driver:
            return {"nodes": [], "edges": []}

        try:
            with driver.session() as session:
                query = """
                MATCH (c:Case {id: $case_id})-[r]-(n)
                RETURN c, type(r) as relation, n, labels(n) as labels
                """
                res = session.run(query, case_id=case_id)
                nodes_map = {}
                edges = []
                
                c_node = None
                for record in res:
                    if not c_node:
                        c_rec = record["c"]
                        c_node = {"id": c_rec["id"], "label": "Case", "name": c_rec.get("label", "Case")}
                        nodes_map[c_rec["id"]] = c_node
                        
                    n_rec = record["n"]
                    lbl = record["labels"][0] if record["labels"] else "Unknown"
                    n_id = n_rec.get("id")
                    if n_id not in nodes_map:
                        name = n_rec.get("name") or n_rec.get("label") or n_rec.get("description") or n_rec.get("registration") or n_id
                        nodes_map[n_id] = {"id": n_id, "label": lbl, "name": name}
                        
                    edges.append({
                        "source": case_id,
                        "target": n_id,
                        "label": record["relation"]
                    })
                
                return {
                    "nodes": list(nodes_map.values()),
                    "edges": edges
                }
        except Exception as e:
            import logging
            logging.error(f"Neo4j get_case_network error: {e}")
            return {"nodes": [], "edges": []}

    def get_evidence_nexus(self) -> dict:
        """Returns a snapshot of the graph for the intelligence workbench."""
        if not self.enabled:
            return {"nodes": [], "edges": []}

        driver = self._get_driver()
        if not driver:
            return {"nodes": [], "edges": []}

        try:
            with driver.session() as session:
                query = """
                MATCH (n)-[r]->(m)
                RETURN n, labels(n) as n_lbl, type(r) as rel, m, labels(m) as m_lbl
                LIMIT 50
                """
                res = session.run(query)
                nodes_map = {}
                edges = []
                
                for record in res:
                    n_rec = record["n"]
                    m_rec = record["m"]
                    n_lbl = record["n_lbl"][0] if record["n_lbl"] else "Unknown"
                    m_lbl = record["m_lbl"][0] if record["m_lbl"] else "Unknown"
                    n_id = n_rec.get("id")
                    m_id = m_rec.get("id")
                    
                    if n_id not in nodes_map:
                        nodes_map[n_id] = {"id": n_id, "label": n_lbl, "name": n_rec.get("name") or n_rec.get("label") or n_rec.get("description") or n_rec.get("registration") or n_id}
                    if m_id not in nodes_map:
                        nodes_map[m_id] = {"id": m_id, "label": m_lbl, "name": m_rec.get("name") or m_rec.get("label") or m_rec.get("description") or m_rec.get("registration") or m_id}
                        
                    edges.append({
                        "source": n_id,
                        "target": m_id,
                        "label": record["rel"]
                    })
                
                return {
                    "nodes": list(nodes_map.values()),
                    "edges": edges
                }
        except Exception as e:
            import logging
            logging.error(f"Neo4j get_evidence_nexus error: {e}")
            return {"nodes": [], "edges": []}
