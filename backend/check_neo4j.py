import sys
sys.path.append('.')
import asyncio
from app.services.graph_service import get_driver

async def check():
    driver = get_driver()
    if not driver:
        print("Neo4j driver not available")
        return
    with driver.session() as session:
        nodes = session.run("MATCH (n) RETURN count(n)").single()[0]
        rels = session.run("MATCH ()-[r]->() RETURN count(r)").single()[0]
        print(f'Neo4j Nodes: {nodes} | Relationships: {rels}')

asyncio.run(check())
