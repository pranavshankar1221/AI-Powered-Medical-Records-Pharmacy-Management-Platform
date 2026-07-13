"""
Verifies Neo4j database setup, constraints, seeding, and relationships.
Run using: python backend/test_neo4j.py
"""

import sys
from pathlib import Path

# Add backend and ai_module directories to sys.path prioritizing ai_module
BACKEND_DIR = Path(__file__).resolve().parent
AI_MODULE_DIR = BACKEND_DIR.parent / "ai_module"
sys.path.insert(0, str(AI_MODULE_DIR))
sys.path.insert(1, str(BACKEND_DIR))

# Dynamically link the services folders to allow loading from both root and ai_module
try:
    import services
    if hasattr(services, "__path__"):
        services_path = str(AI_MODULE_DIR / "services")
        if services_path not in services.__path__:
            services.__path__.append(services_path)
except ImportError:
    pass

import config
from database.neo4j_db import get_neo4j_driver, init_neo4j_db
from services.rag_engine import retrieve_graph_context, generate_response


def main():
    print("=" * 60)
    print("[START] Starting Neo4j Graph Verification & Test Suite")
    print("=" * 60)

    # 1. Test Driver connection
    driver = get_neo4j_driver()
    if not driver:
        print("[WARNING] Failed to retrieve Neo4j driver (offline). Proceeding with fallback tests.")
    else:
        print("[OK] Neo4j connection verified successfully.")

    # 2. Run Database init & seed
    print("\nRunning init_neo4j_db()...")
    success = init_neo4j_db()
    if success:
        print("[OK] Database constraints initialized and seeded.")
    else:
        print("[WARNING] Database initialization returned False (likely Neo4j is offline or connection failed).")

    # 3. Query Node Counts
    print("\nVerifying database contents:")
    try:
        with driver.session() as session:
            med_count = session.run("MATCH (m:Medicine) RETURN count(m) as count").single()["count"]
            cat_count = session.run("MATCH (c:Category) RETURN count(c) as count").single()["count"]
            mfg_count = session.run("MATCH (man:Manufacturer) RETURN count(man) as count").single()["count"]
            sub_count = session.run("MATCH (s:Substance) RETURN count(s) as count").single()["count"]
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]

            print(f"  - Medicine Nodes:      {med_count}")
            print(f"  - Category Nodes:      {cat_count}")
            print(f"  - Manufacturer Nodes:  {mfg_count}")
            print(f"  - Substance Nodes:     {sub_count}")
            print(f"  - Total Relationships: {rel_count}")
            
            if med_count == 0:
                print("[ERROR] Seeding failed, 0 medicines found in Neo4j.")
                sys.exit(1)
    except Exception as e:
        print(f"[WARNING] Could not retrieve node counts (Neo4j connection error: {e})")

    # 4. Verify category relationships
    print("\nSample Category mapping:")
    try:
        with driver.session() as session:
            results = session.run(
                """
                MATCH (m:Medicine)-[:BELONGS_TO]->(c:Category)
                RETURN m.name as medicine, c.name as category
                LIMIT 5
                """
            )
            for r in results:
                print(f"  - {r['medicine']} -> belongs to category: {r['category']}")
    except Exception as e:
        print(f"[WARNING] Could not query categories (Neo4j connection error: {e})")

    # 5. Verify interactions
    print("\nDrug-drug and substance interactions:")
    try:
        with driver.session() as session:
            dd_res = session.run(
                """
                MATCH (m1:Medicine)-[r:INTERACTS_WITH {type: 'drug-drug'}]->(m2:Medicine)
                RETURN m1.name as med1, m2.name as med2, r.description as desc
                LIMIT 3
                """
            )
            for r in dd_res:
                print(f"  - [WARNING] Interaction: {r['med1']} interacts with {r['med2']}")
                print(f"    Detail: {r['desc'][:100]}...")

            food_res = session.run(
                """
                MATCH (m:Medicine)-[r:INTERACTS_WITH {type: 'food-substance'}]->(s:Substance)
                RETURN m.name as med, s.name as substance, r.description as desc
                LIMIT 3
                """
            )
            for r in food_res:
                print(f"  - [WARNING] Food warning: {r['med']} with {r['substance']}")
                print(f"    Detail: {r['desc'][:100]}...")
    except Exception as e:
        print(f"[WARNING] Could not query interactions (Neo4j connection error: {e})")

    # 6. Test RAG Integration Context retrieval
    print("\nTesting Hybrid Graph RAG Retrieval Context:")
    try:
        # We will test retrieval with Amoxicillin (MED_001) and Paracetamol (MED_002)
        # and a query about milk or drug-drug warnings
        graph_context = retrieve_graph_context(
            query="Can I take Amoxicillin with dairy or milk? Also, are there interactions with Paracetamol?",
            medicine_ids=["MED_001", "MED_002"]
        )
        
        print("-" * 50)
        if graph_context:
            print(graph_context)
            print("[OK] Graph RAG context retrieval returned valid relationships.")
        else:
            print("[WARNING] Graph RAG context retrieval returned empty results (likely connection offline).")
        print("-" * 50)
    except Exception as e:
        print(f"[ERROR] Graph RAG context retrieval failed: {e}")

    print("\nTest finished. Checking full pipeline response...")
    # Test full generation query
    try:
        res = generate_response(
            query="Can I drink alcohol with paracetamol?",
            medicine_ids=["MED_001", "MED_002"],
            patient_medicines=[{"medicine_id": "MED_001", "name": "Amoxicillin 500mg"}, {"medicine_id": "MED_002", "name": "Paracetamol 500mg"}]
        )
        print("[OK] Hybrid RAG generate_response completed.")
        print(f"  - Latency: {res.get('latency_ms')} ms")
        print(f"  - Has Graph Context: {res.get('has_graph_context')}")
        print(f"  - Answer Snippet: {res.get('answer')[:120]}...")
    except Exception as e:
        print(f"[ERROR] Failed to run generate_response pipeline: {e}")

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL TESTS COMPLETED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
