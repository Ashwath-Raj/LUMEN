import asyncio
import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
PG_URL = os.environ.get("DATABASE_URL", "")
NEO4J_URI = os.environ.get("NEO4J_URI")
NEO4J_USER = os.environ.get("NEO4J_USER")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")

def get_pg_data():
    engine = create_engine(PG_URL)
    session_maker = sessionmaker(bind=engine)
    
    data = {}
    with session_maker() as session:
        # Cases
        res = session.execute(text("SELECT id, label, status, police_station_id FROM cases"))
        data['cases'] = [dict(row._mapping) for row in res]
        
        # Accused
        res = session.execute(text("SELECT id, name, case_master_id FROM accused WHERE case_master_id IS NOT NULL"))
        data['accused'] = [dict(row._mapping) for row in res]
        
        # Victims
        res = session.execute(text("SELECT id, name, case_master_id FROM victims WHERE case_master_id IS NOT NULL"))
        data['victims'] = [dict(row._mapping) for row in res]
        
        # Vehicles
        res = session.execute(text("SELECT id, registration_no, case_master_id FROM vehicles WHERE case_master_id IS NOT NULL"))
        data['vehicles'] = [dict(row._mapping) for row in res]
        
        # Properties
        res = session.execute(text("SELECT id, description, case_master_id FROM properties WHERE case_master_id IS NOT NULL"))
        data['properties'] = [dict(row._mapping) for row in res]
        
        # Evidence
        res = session.execute(text("SELECT id, name, case_id FROM evidence WHERE case_id IS NOT NULL"))
        data['evidence'] = [dict(row._mapping) for row in res]
        
        # Districts
        res = session.execute(text("SELECT id, name FROM districts"))
        data['districts'] = [dict(row._mapping) for row in res]
        
        # Units
        res = session.execute(text("SELECT id, name, district_id FROM units WHERE district_id IS NOT NULL"))
        data['units'] = [dict(row._mapping) for row in res]
        
    engine.dispose()
    return data


def sync_neo4j(data):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # Setup constraints
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Case) REQUIRE c.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Accused) REQUIRE a.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (v:Victim) REQUIRE v.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (vh:Vehicle) REQUIRE vh.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Property) REQUIRE p.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:Unit) REQUIRE u.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:District) REQUIRE d.id IS UNIQUE")
        
        print("Constraints ensured.")
        
        # Cases
        for c in data['cases']:
            session.run("""
                MERGE (case:Case {id: $id})
                SET case.label = $label, case.status = $status
            """, id=c['id'], label=c['label'] or 'Unknown', status=c['status'] or 'Unknown')
            
            if c['police_station_id']:
                session.run("""
                    MATCH (c:Case {id: $case_id})
                    MERGE (u:Unit {id: $unit_id})
                    MERGE (c)-[:ASSIGNED_TO_UNIT]->(u)
                """, case_id=c['id'], unit_id=c['police_station_id'])

        # Accused
        for a in data['accused']:
            session.run("""
                MERGE (n:Accused {id: $id})
                SET n.name = $name
                WITH n
                MATCH (c:Case {id: $case_id})
                MERGE (c)-[:HAS_ACCUSED]->(n)
            """, id=a['id'], name=a['name'] or 'Unknown', case_id=a['case_master_id'])
            
        # Victims
        for v in data['victims']:
            session.run("""
                MERGE (n:Victim {id: $id})
                SET n.name = $name
                WITH n
                MATCH (c:Case {id: $case_id})
                MERGE (c)-[:HAS_VICTIM]->(n)
            """, id=v['id'], name=v['name'] or 'Unknown', case_id=v['case_master_id'])
            
        # Vehicles
        for vh in data['vehicles']:
            session.run("""
                MERGE (n:Vehicle {id: $id})
                SET n.registration = $reg
                WITH n
                MATCH (c:Case {id: $case_id})
                MERGE (c)-[:HAS_VEHICLE]->(n)
            """, id=vh['id'], reg=vh['registration_no'] or 'Unknown', case_id=vh['case_master_id'])
            
        # Properties
        for p in data['properties']:
            session.run("""
                MERGE (n:Property {id: $id})
                SET n.description = $desc
                WITH n
                MATCH (c:Case {id: $case_id})
                MERGE (c)-[:HAS_PROPERTY]->(n)
            """, id=p['id'], desc=p['description'][:100] if p['description'] else 'Unknown', case_id=p['case_master_id'])
            
        # Evidence
        for e in data['evidence']:
            session.run("""
                MERGE (n:Evidence {id: $id})
                SET n.name = $name
                WITH n
                MATCH (c:Case {id: $case_id})
                MERGE (c)-[:HAS_EVIDENCE]->(n)
            """, id=e['id'], name=e['name'] or 'Unknown', case_id=e['case_id'])
            
        # Districts & Units
        for d in data['districts']:
            session.run("""
                MERGE (n:District {id: $id})
                SET n.name = $name
            """, id=d['id'], name=d['name'] or 'Unknown')
            
        for u in data['units']:
            session.run("""
                MERGE (n:Unit {id: $id})
                SET n.name = $name
                WITH n
                MATCH (d:District {id: $dist_id})
                MERGE (n)-[:IN_DISTRICT]->(d)
            """, id=u['id'], name=u['name'] or 'Unknown', dist_id=u['district_id'])
            
        # Summary
        res = session.run('MATCH (n) RETURN labels(n) as label, count(n) as count')
        print("Nodes:")
        for r in res:
            print(f"  {r['label']}: {r['count']}")
            
        res = session.run('MATCH ()-[r]->() RETURN type(r) as type, count(r) as count')
        print("Relationships:")
        for r in res:
            print(f"  {r['type']}: {r['count']}")
            
        # Total
        node_count = session.run('MATCH (n) RETURN count(n) as c').single()['c']
        rel_count = session.run('MATCH ()-[r]->() RETURN count(r) as c').single()['c']
        print(f"Total Nodes: {node_count}, Total Relationships: {rel_count}")

    driver.close()

def main():
    print("Fetching data from PG...")
    data = get_pg_data()
    for k, v in data.items():
        print(f"  {k}: {len(v)} records")
        
    print("Syncing to Neo4j...")
    sync_neo4j(data)
    print("Sync complete.")

if __name__ == "__main__":
    main()
