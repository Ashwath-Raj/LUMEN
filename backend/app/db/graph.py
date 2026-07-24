"""
Neo4j graph database abstraction layer.

This module provides:
  - Driver initialisation (guarded — returns None if Neo4j is unavailable)
  - GraphRepository base with node/relationship CRUD
  - Domain-specific queries (case network, suspect connections)

No data is migrated here yet. All methods return empty stubs until
Neo4j is configured via NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD in .env.
"""
from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger("lumen")


def _get_driver():
    """
    Return a Neo4j driver instance or None if the package is unavailable
    or NEO4J_ENABLED is false.
    """
    if not settings.NEO4J_ENABLED:
        return None
    try:
        from neo4j import GraphDatabase  # type: ignore
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        driver.verify_connectivity()
        logger.info("Neo4j connected at %s", settings.NEO4J_URI)
        return driver
    except ImportError:
        logger.warning("neo4j driver not installed — graph features disabled.")
        return None
    except Exception as exc:
        logger.warning("Neo4j unavailable: %s", exc)
        return None


_driver = _get_driver()


def is_available() -> bool:
    return _driver is not None


class GraphRepository:
    """
    Generic Neo4j repository.
    All methods are guarded — return empty results if driver is None.
    """

    def run(self, cypher: str, **params):
        """Execute a Cypher query and return raw records."""
        if not _driver:
            return []
        with _driver.session() as session:
            result = session.run(cypher, **params)
            return list(result)

    def merge_node(self, label: str, properties: dict) -> dict:
        """Upsert a node by its `id` property."""
        if not _driver:
            return {}
        cypher = f"MERGE (n:{label} {{id: $id}}) SET n += $props RETURN n"
        records = self.run(cypher, id=properties.get("id"), props=properties)
        return dict(records[0]["n"]) if records else {}

    def merge_relationship(self, from_id: str, to_id: str, rel_type: str,
                           from_label: str = "Entity", to_label: str = "Entity") -> bool:
        """Upsert a directed relationship between two nodes."""
        if not _driver:
            return False
        cypher = (
            f"MATCH (a:{from_label} {{id: $from_id}}), (b:{to_label} {{id: $to_id}}) "
            f"MERGE (a)-[r:{rel_type}]->(b) RETURN r"
        )
        records = self.run(cypher, from_id=from_id, to_id=to_id)
        return bool(records)

    def get_node(self, label: str, node_id: str) -> dict | None:
        if not _driver:
            return None
        records = self.run(f"MATCH (n:{label} {{id: $id}}) RETURN n", id=node_id)
        return dict(records[0]["n"]) if records else None

    def delete_node(self, label: str, node_id: str) -> bool:
        if not _driver:
            return False
        self.run(f"MATCH (n:{label} {{id: $id}}) DETACH DELETE n", id=node_id)
        return True


class GraphService:
    """
    Domain-specific graph service for criminal network analysis.
    Returns JSON-serialisable dicts matching the frontend network shape.
    """

    def __init__(self):
        self._repo = GraphRepository()

    def get_case_network(self, case_id: str) -> dict:
        """
        Return the criminal network for a case as {nodes, edges}.
        Falls back to empty structure if Neo4j unavailable.
        """
        if not is_available():
            return {"nodes": [], "edges": [], "stub": True}

        cypher = """
        MATCH (c:CaseMaster {id: $case_id})-[:INVOLVES]->(entity)
        OPTIONAL MATCH (entity)-[:CONNECTED_TO]->(other)
        RETURN entity, other
        """
        records = self._repo.run(cypher, case_id=case_id)
        nodes, edges, seen = [], [], set()
        for rec in records:
            for key in ("entity", "other"):
                node = rec.get(key)
                if node and node["id"] not in seen:
                    seen.add(node["id"])
                    nodes.append({"id": node["id"], "label": node.get("name", node["id"]),
                                  "kind": node.get("kind", "default")})
            if rec.get("entity") and rec.get("other"):
                edges.append({"source": rec["entity"]["id"], "target": rec["other"]["id"]})
        return {"nodes": nodes, "edges": edges}

    def get_suspect_connections(self, suspect_id: str) -> dict:
        """
        Return all entities connected to a suspect node.
        """
        if not is_available():
            return {"nodes": [], "edges": [], "stub": True}

        cypher = """
        MATCH (s:Accused {id: $suspect_id})-[r]->(connected)
        RETURN s, type(r) as rel, connected
        """
        records = self._repo.run(cypher, suspect_id=suspect_id)
        nodes, edges, seen = [], [], set()
        for rec in records:
            suspect = rec["s"]
            connected = rec["connected"]
            if suspect["id"] not in seen:
                seen.add(suspect["id"])
                nodes.append({"id": suspect["id"], "label": suspect.get("name", suspect["id"]),
                               "kind": "flag"})
            if connected["id"] not in seen:
                seen.add(connected["id"])
                nodes.append({"id": connected["id"], "label": connected.get("name", connected["id"]),
                               "kind": "default"})
            edges.append({"source": suspect["id"], "target": connected["id"], "type": rec["rel"]})
        return {"nodes": nodes, "edges": edges}

    def upsert_case_node(self, case_id: str, label: str) -> dict:
        return self._repo.merge_node("Case", {"id": case_id, "label": label})

    def upsert_suspect_node(self, suspect_id: str, name: str) -> dict:
        return self._repo.merge_node("Suspect", {"id": suspect_id, "name": name, "kind": "flag"})

    def link_suspect_to_case(self, suspect_id: str, case_id: str) -> bool:
        return self._repo.merge_relationship(suspect_id, case_id, "INVOLVED_IN",
                                              from_label="Suspect", to_label="Case")


# Module-level singleton — import and use directly
graph_service = GraphService()
