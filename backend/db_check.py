
from app.db.session import SessionLocal, engine
from app.db.models import Base
import sqlalchemy
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv("C:/Users/jaswa/Downloads/LUMEN/LUMEN/backend/.env")

print("--- PostgreSQL Row Counts ---")
try:
    db = SessionLocal()
    metadata = Base.metadata
    metadata.reflect(bind=engine)
    for table in metadata.tables.values():
        count = db.query(table).count()
        print(f"{table.name}: {count} rows")
except Exception as e:
    print(f"Error querying Postgres: {e}")

print("\n--- Neo4j Node Counts ---")
try:
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) as count")
        print(f"Total Nodes: {result.single()[0]}")
        
        result_rels = session.run("MATCH ()-[r]->() RETURN count(r) as count")
        print(f"Total Relationships: {result_rels.single()[0]}")
except Exception as e:
    print(f"Error querying Neo4j: {e}")

