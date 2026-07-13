"""
Neo4j Graph Database Connection Manager and Seeding Utility.
Provides connections, constraints creation, and graph seeding from medicines.json.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from neo4j import GraphDatabase, Driver

import config

logger = logging.getLogger("mediqr.neo4j")

# Singleton driver instance
_driver: Optional[Driver] = None

def get_neo4j_driver() -> Optional[Driver]:
    """Retrieve the singleton Neo4j driver instance."""
    global _driver
    if _driver is None:
        try:
            uri = getattr(config, "NEO4J_URI", "bolt://localhost:7687")
            user = getattr(config, "NEO4J_USER", "neo4j")
            password = getattr(config, "NEO4J_PASSWORD", "mediqr_pass_2026")
            
            logger.info(f"Connecting to Neo4j at {uri}...")
            _driver = GraphDatabase.driver(uri, auth=(user, password))
            # Verify connectivity
            _driver.verify_connectivity()
            logger.info("✅ Connected to Neo4j successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            _driver = None
    return _driver

def close_neo4j_driver():
    """Close the Neo4j driver instance if it exists."""
    global _driver
    if _driver is not None:
        try:
            _driver.close()
            logger.info("Closed Neo4j driver connection.")
        except Exception as e:
            logger.error(f"Error closing Neo4j driver: {e}")
        finally:
            _driver = None

def init_neo4j_db() -> bool:
    """
    Initialize database by setting up constraints and seeding data if empty.
    Returns True if successfully initialized/seeded, False otherwise.
    """
    driver = get_neo4j_driver()
    if not driver:
        logger.warning("⚠️ Neo4j driver not available. Skipping graph initialization.")
        return False

    try:
        # Create unique constraints
        with driver.session() as session:
            logger.info("Creating Neo4j constraints/indexes...")
            session.run("CREATE CONSTRAINT medicine_id_unique IF NOT EXISTS FOR (m:Medicine) REQUIRE m.medicine_id IS UNIQUE")
            session.run("CREATE CONSTRAINT category_name_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE")
            session.run("CREATE CONSTRAINT manufacturer_name_unique IF NOT EXISTS FOR (m:Manufacturer) REQUIRE m.name IS UNIQUE")
            session.run("CREATE CONSTRAINT substance_name_unique IF NOT EXISTS FOR (s:Substance) REQUIRE s.name IS UNIQUE")
        
        # Check if database is already seeded
        with driver.session() as session:
            result = session.run("MATCH (m:Medicine) RETURN count(m) as count")
            count = result.single()["count"]
            if count > 0:
                logger.info(f"Graph database already contains {count} medicines. Skipping seed.")
                return True

        # Run seeding
        return seed_neo4j_data()

    except Exception as e:
        logger.error(f"❌ Failed to initialize/seed Neo4j database: {e}")
        return False

def seed_neo4j_data() -> bool:
    """
    Load medicines from json, parse relationships, and seed the graph.
    """
    driver = get_neo4j_driver()
    if not driver:
        return False

    # Locate medicines.json
    medicines_path = getattr(config, "AI_MODULE_DIR", Path(__file__).resolve().parent.parent.parent / "ai_module") / "knowledge_base" / "medicines.json"
    if not medicines_path.exists():
        # Try relative paths for safety in other environments
        medicines_path = Path(__file__).resolve().parent.parent.parent / "ai_module" / "knowledge_base" / "medicines.json"
        if not medicines_path.exists():
            logger.error(f"❌ medicines.json not found at {medicines_path}")
            return False

    try:
        with open(medicines_path, "r", encoding="utf-8") as f:
            medicines_data = json.load(f)

        logger.info(f"Seeding Neo4j with {len(medicines_data)} medicines...")

        with driver.session() as session:
            # 1. Create all Medicine, Category, and Manufacturer nodes
            for med in medicines_data:
                # Merge Medicine
                session.run(
                    """
                    MERGE (m:Medicine {medicine_id: $medicine_id})
                    SET m.name = $name,
                        m.generic_name = $generic_name,
                        m.dosage_form = $dosage_form,
                        m.strength = $strength,
                        m.description = $description,
                        m.side_effects = $side_effects,
                        m.interactions = $interactions,
                        m.contraindications = $contraindications,
                        m.storage_instructions = $storage_instructions,
                        m.dosage_schedule = $dosage_schedule,
                        m.missed_dose_guidance = $missed_dose_guidance,
                        m.unit_price = $unit_price
                    """,
                    medicine_id=med["medicine_id"],
                    name=med["name"],
                    generic_name=med.get("generic_name", ""),
                    dosage_form=med.get("dosage_form", ""),
                    strength=med.get("strength", ""),
                    description=med.get("description", ""),
                    side_effects=med.get("side_effects", ""),
                    interactions=med.get("interactions", ""),
                    contraindications=med.get("contraindications", ""),
                    storage_instructions=med.get("storage_instructions", ""),
                    dosage_schedule=med.get("dosage_schedule", ""),
                    missed_dose_guidance=med.get("missed_dose_guidance", ""),
                    unit_price=float(med.get("unit_price", 0.0))
                )

                # Merge Category & Relationship
                category = med.get("category", "").strip()
                if category:
                    # Categories can be semicolon or slash separated (e.g. "Analgesic / Antipyretic")
                    cats = [c.strip() for c in category.replace("/", ";").split(";") if c.strip()]
                    for cat in cats:
                        session.run(
                            """
                            MATCH (m:Medicine {medicine_id: $medicine_id})
                            MERGE (c:Category {name: $category_name})
                            MERGE (m)-[:BELONGS_TO]->(c)
                            """,
                            medicine_id=med["medicine_id"],
                            category_name=cat
                        )

                # Merge Manufacturer & Relationship
                mfg = med.get("manufacturer", "").strip()
                if mfg:
                    session.run(
                        """
                        MATCH (m:Medicine {medicine_id: $medicine_id})
                        MERGE (man:Manufacturer {name: $mfg_name})
                        MERGE (m)-[:MADE_BY]->(man)
                        """,
                        medicine_id=med["medicine_id"],
                        mfg_name=mfg
                    )

            # 2. Parse and Create Interaction Relationships
            # Build list of all generic names and medicine names to match against
            med_keywords = []
            for med in medicines_data:
                med_keywords.append({
                    "medicine_id": med["medicine_id"],
                    "name": med["name"].split()[0].lower(),  # e.g., "Amoxicillin" from "Amoxicillin 500mg"
                    "generic": med.get("generic_name", "").lower(),
                })

            substance_keywords = ["alcohol", "grapefruit", "dairy", "milk", "caffeine"]

            for med in medicines_data:
                interactions_text = med.get("interactions", "").lower()
                if not interactions_text:
                    continue

                # Check for drug-drug interactions
                for kw in med_keywords:
                    # Don't interact with self
                    if kw["medicine_id"] == med["medicine_id"]:
                        continue

                    # Search text for name or generic name matches
                    match_found = False
                    reason = ""
                    if kw["name"] in interactions_text:
                        match_found = True
                        reason = f"Mentioned: {kw['name']}"
                    elif kw["generic"] and kw["generic"] in interactions_text:
                        match_found = True
                        reason = f"Mentioned generic: {kw['generic']}"

                    if match_found:
                        # Extract a snippet around the match for description
                        idx = interactions_text.find(kw["name"]) if kw["name"] in interactions_text else interactions_text.find(kw["generic"])
                        start = max(0, idx - 50)
                        end = min(len(interactions_text), idx + 100)
                        snippet = med.get("interactions", "")[start:end].strip()
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(interactions_text):
                            snippet = snippet + "..."

                        session.run(
                            """
                            MATCH (m1:Medicine {medicine_id: $m1_id})
                            MATCH (m2:Medicine {medicine_id: $m2_id})
                            MERGE (m1)-[r:INTERACTS_WITH {type: 'drug-drug'}]->(m2)
                            SET r.description = $desc
                            """,
                            m1_id=med["medicine_id"],
                            m2_id=kw["medicine_id"],
                            desc=snippet
                        )

                # Check for food/substance interactions
                for sub in substance_keywords:
                    if sub in interactions_text:
                        # Extract context snippet
                        idx = interactions_text.find(sub)
                        start = max(0, idx - 50)
                        end = min(len(interactions_text), idx + 100)
                        snippet = med.get("interactions", "")[start:end].strip()
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(interactions_text):
                            snippet = snippet + "..."

                        session.run(
                            """
                            MATCH (m:Medicine {medicine_id: $m_id})
                            MERGE (s:Substance {name: $sub_name})
                            MERGE (m)-[r:INTERACTS_WITH {type: 'food-substance'}]->(s)
                            SET r.description = $desc
                            """,
                            m_id=med["medicine_id"],
                            sub_name=sub.capitalize(),
                            desc=snippet
                        )

        logger.info("✅ Neo4j seeding completed successfully.")
        return True

    except Exception as e:
        logger.error(f"❌ Error seeding Neo4j: {e}")
        return False
