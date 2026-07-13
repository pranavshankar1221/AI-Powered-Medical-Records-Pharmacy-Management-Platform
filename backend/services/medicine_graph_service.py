"""
Medicine Knowledge Graph Service
Provides drug interaction checking and alternative medicine recommendations using Neo4j.
"""

import logging
from typing import List, Dict, Any, Optional
from database.neo4j_db import get_neo4j_driver

logger = logging.getLogger("mediqr.medicine_graph")


class MedicineGraphService:
    """Service for medicine knowledge graph operations."""
    
    def __init__(self):
        self.driver = get_neo4j_driver()
    
    def check_drug_interactions(
        self, 
        medicine_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Check for drug-drug interactions among a list of medicines.
        
        Args:
            medicine_ids: List of medicine IDs to check for interactions
            
        Returns:
            Dictionary containing:
            - has_interactions: boolean
            - interactions: list of interaction details
            - severity_counts: dict of severity levels
        """
        if not self.driver:
            logger.error("Neo4j driver not available")
            return {"has_interactions": False, "interactions": [], "error": "Database unavailable"}
        
        if len(medicine_ids) < 2:
            return {"has_interactions": False, "interactions": [], "message": "Need at least 2 medicines to check interactions"}
        
        try:
            with self.driver.session() as session:
                # Query for drug-drug interactions between the given medicines
                query = """
                MATCH (m1:Medicine)-[r:INTERACTS_WITH {type: 'drug-drug'}]->(m2:Medicine)
                WHERE m1.medicine_id IN $medicine_ids AND m2.medicine_id IN $medicine_ids
                RETURN m1.medicine_id as med1_id, 
                       m1.name as med1_name,
                       m2.medicine_id as med2_id,
                       m2.name as med2_name,
                       r.description as description
                """
                
                result = session.run(query, medicine_ids=medicine_ids)
                interactions = []
                
                for record in result:
                    interactions.append({
                        "medicine_1": {
                            "id": record["med1_id"],
                            "name": record["med1_name"]
                        },
                        "medicine_2": {
                            "id": record["med2_id"],
                            "name": record["med2_name"]
                        },
                        "description": record["description"],
                        "severity": self._classify_severity(record["description"])
                    })
                
                has_interactions = len(interactions) > 0
                
                # Count by severity
                severity_counts = {}
                for interaction in interactions:
                    severity = interaction["severity"]
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                return {
                    "has_interactions": has_interactions,
                    "interactions": interactions,
                    "severity_counts": severity_counts,
                    "total_interactions": len(interactions)
                }
                
        except Exception as e:
            logger.error(f"Error checking drug interactions: {e}")
            return {"has_interactions": False, "interactions": [], "error": str(e)}
    
    def check_food_substance_interactions(
        self, 
        medicine_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Check for food/substance interactions for given medicines.
        
        Args:
            medicine_ids: List of medicine IDs to check
            
        Returns:
            Dictionary containing food/substance interactions
        """
        if not self.driver:
            logger.error("Neo4j driver not available")
            return {"has_interactions": False, "interactions": [], "error": "Database unavailable"}
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (m:Medicine)-[r:INTERACTS_WITH {type: 'food-substance'}]->(s:Substance)
                WHERE m.medicine_id IN $medicine_ids
                RETURN m.medicine_id as med_id,
                       m.name as med_name,
                       s.name as substance,
                       r.description as description
                """
                
                result = session.run(query, medicine_ids=medicine_ids)
                interactions = []
                
                for record in result:
                    interactions.append({
                        "medicine": {
                            "id": record["med_id"],
                            "name": record["med_name"]
                        },
                        "substance": record["substance"],
                        "description": record["description"],
                        "severity": self._classify_severity(record["description"])
                    })
                
                return {
                    "has_interactions": len(interactions) > 0,
                    "interactions": interactions,
                    "total_interactions": len(interactions)
                }
                
        except Exception as e:
            logger.error(f"Error checking food interactions: {e}")
            return {"has_interactions": False, "interactions": [], "error": str(e)}
    
    def get_alternative_medicines(
        self, 
        medicine_id: str, 
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Recommend alternative medicines based on:
        1. Same category (therapeutic class)
        2. Same generic name (generic equivalents)
        3. Similar manufacturer
        
        Args:
            medicine_id: ID of the medicine to find alternatives for
            limit: Maximum number of alternatives to return
            
        Returns:
            Dictionary containing alternative medicine recommendations
        """
        if not self.driver:
            logger.error("Neo4j driver not available")
            return {"alternatives": [], "error": "Database unavailable"}
        
        try:
            with self.driver.session() as session:
                # First get the medicine details
                med_query = """
                MATCH (m:Medicine {medicine_id: $medicine_id})
                OPTIONAL MATCH (m)-[:BELONGS_TO]->(c:Category)
                OPTIONAL MATCH (m)-[:MADE_BY]->(man:Manufacturer)
                RETURN m.medicine_id as id,
                       m.name as name,
                       m.generic_name as generic_name,
                       m.unit_price as price,
                       collect(DISTINCT c.name) as categories,
                       collect(DISTINCT man.name) as manufacturers
                """
                
                med_result = session.run(med_query, medicine_id=medicine_id)
                med_record = med_result.single()
                
                if not med_record:
                    return {"alternatives": [], "error": "Medicine not found"}
                
                categories = med_record["categories"]
                generic_name = med_record["generic_name"]
                manufacturers = med_record["manufacturers"]
                
                # Find alternatives based on category
                alternatives = []
                
                # Priority 1: Same generic name (generic equivalents)
                if generic_name:
                    generic_query = """
                    MATCH (m:Medicine)
                    WHERE m.generic_name = $generic_name 
                    AND m.medicine_id <> $medicine_id
                    OPTIONAL MATCH (m)-[:BELONGS_TO]->(c:Category)
                    RETURN m.medicine_id as id,
                           m.name as name,
                           m.generic_name as generic_name,
                           m.unit_price as price,
                           collect(DISTINCT c.name) as categories,
                           'generic_equivalent' as recommendation_type
                    LIMIT $limit
                    """
                    
                    generic_result = session.run(
                        generic_query, 
                        generic_name=generic_name,
                        medicine_id=medicine_id,
                        limit=limit
                    )
                    
                    for record in generic_result:
                        alternatives.append({
                            "id": record["id"],
                            "name": record["name"],
                            "generic_name": record["generic_name"],
                            "price": record["price"],
                            "categories": record["categories"],
                            "recommendation_type": record["recommendation_type"],
                            "reason": f"Generic equivalent of {generic_name}"
                        })
                
                # Priority 2: Same category (therapeutic alternatives)
                if categories and len(alternatives) < limit:
                    category_query = """
                    MATCH (m:Medicine)-[:BELONGS_TO]->(c:Category)
                    WHERE c.name IN $categories 
                    AND m.medicine_id <> $medicine_id
                    AND NOT m.medicine_id IN $exclude_ids
                    OPTIONAL MATCH (m)-[:MADE_BY]->(man:Manufacturer)
                    RETURN m.medicine_id as id,
                           m.name as name,
                           m.generic_name as generic_name,
                           m.unit_price as price,
                           collect(DISTINCT c.name) as categories,
                           collect(DISTINCT man.name) as manufacturers,
                           'therapeutic_alternative' as recommendation_type
                    LIMIT $limit
                    """
                    
                    exclude_ids = [alt["id"] for alt in alternatives]
                    category_result = session.run(
                        category_query,
                        categories=categories,
                        medicine_id=medicine_id,
                        exclude_ids=exclude_ids,
                        limit=limit - len(alternatives)
                    )
                    
                    for record in category_result:
                        alternatives.append({
                            "id": record["id"],
                            "name": record["name"],
                            "generic_name": record["generic_name"],
                            "price": record["price"],
                            "categories": record["categories"],
                            "manufacturers": record["manufacturers"],
                            "recommendation_type": record["recommendation_type"],
                            "reason": f"Therapeutic alternative in same category: {', '.join(record['categories'])}"
                        })
                
                # Priority 3: Same manufacturer if still needed
                if manufacturers and len(alternatives) < limit:
                    manufacturer_query = """
                    MATCH (m:Medicine)-[:MADE_BY]->(man:Manufacturer)
                    WHERE man.name IN $manufacturers 
                    AND m.medicine_id <> $medicine_id
                    AND NOT m.medicine_id IN $exclude_ids
                    OPTIONAL MATCH (m)-[:BELONGS_TO]->(c:Category)
                    RETURN m.medicine_id as id,
                           m.name as name,
                           m.generic_name as generic_name,
                           m.unit_price as price,
                           collect(DISTINCT c.name) as categories,
                           collect(DISTINCT man.name) as manufacturers,
                           'same_manufacturer' as recommendation_type
                    LIMIT $limit
                    """
                    
                    exclude_ids = [alt["id"] for alt in alternatives]
                    manufacturer_result = session.run(
                        manufacturer_query,
                        manufacturers=manufacturers,
                        medicine_id=medicine_id,
                        exclude_ids=exclude_ids,
                        limit=limit - len(alternatives)
                    )
                    
                    for record in manufacturer_result:
                        alternatives.append({
                            "id": record["id"],
                            "name": record["name"],
                            "generic_name": record["generic_name"],
                            "price": record["price"],
                            "categories": record["categories"],
                            "manufacturers": record["manufacturers"],
                            "recommendation_type": record["recommendation_type"],
                            "reason": f"From same manufacturer: {', '.join(record['manufacturers'])}"
                        })
                
                return {
                    "original_medicine": {
                        "id": med_record["id"],
                        "name": med_record["name"],
                        "generic_name": med_record["generic_name"],
                        "price": med_record["price"],
                        "categories": categories
                    },
                    "alternatives": alternatives[:limit],
                    "total_alternatives": len(alternatives[:limit])
                }
                
        except Exception as e:
            logger.error(f"Error getting alternative medicines: {e}")
            return {"alternatives": [], "error": str(e)}
    
    def get_medicine_details(self, medicine_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a medicine from the knowledge graph.
        
        Args:
            medicine_id: ID of the medicine
            
        Returns:
            Medicine details or None if not found
        """
        if not self.driver:
            logger.error("Neo4j driver not available")
            return None
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (m:Medicine {medicine_id: $medicine_id})
                OPTIONAL MATCH (m)-[:BELONGS_TO]->(c:Category)
                OPTIONAL MATCH (m)-[:MADE_BY]->(man:Manufacturer)
                OPTIONAL MATCH (m)-[r:INTERACTS_WITH]->(other:Medicine)
                WHERE r.type = 'drug-drug'
                OPTIONAL MATCH (m)-[fr:INTERACTS_WITH]->(sub:Substance)
                WHERE fr.type = 'food-substance'
                RETURN m.medicine_id as id,
                       m.name as name,
                       m.generic_name as generic_name,
                       m.dosage_form as dosage_form,
                       m.strength as strength,
                       m.description as description,
                       m.side_effects as side_effects,
                       m.interactions as interactions,
                       m.contraindications as contraindications,
                       m.storage_instructions as storage_instructions,
                       m.dosage_schedule as dosage_schedule,
                       m.missed_dose_guidance as missed_dose_guidance,
                       m.unit_price as price,
                       collect(DISTINCT c.name) as categories,
                       collect(DISTINCT man.name) as manufacturers,
                       count(DISTINCT other) as drug_interaction_count,
                       count(DISTINCT sub) as substance_interaction_count
                """
                
                result = session.run(query, medicine_id=medicine_id)
                record = result.single()
                
                if record:
                    return {
                        "id": record["id"],
                        "name": record["name"],
                        "generic_name": record["generic_name"],
                        "dosage_form": record["dosage_form"],
                        "strength": record["strength"],
                        "description": record["description"],
                        "side_effects": record["side_effects"],
                        "interactions": record["interactions"],
                        "contraindications": record["contraindications"],
                        "storage_instructions": record["storage_instructions"],
                        "dosage_schedule": record["dosage_schedule"],
                        "missed_dose_guidance": record["missed_dose_guidance"],
                        "price": record["price"],
                        "categories": record["categories"],
                        "manufacturers": record["manufacturers"],
                        "drug_interaction_count": record["drug_interaction_count"],
                        "substance_interaction_count": record["substance_interaction_count"]
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting medicine details: {e}")
            return None
    
    def _classify_severity(self, description: str) -> str:
        """
        Classify interaction severity based on description text.
        
        Args:
            description: Interaction description text
            
        Returns:
            Severity level: 'high', 'moderate', or 'low'
        """
        description_lower = description.lower()
        
        high_severity_keywords = [
            'life threatening', 'fatal', 'severe', 'dangerous', 
            'serious', 'contraindicated', 'avoid', 'do not'
        ]
        
        moderate_severity_keywords = [
            'caution', 'monitor', 'may increase', 'may decrease',
            'should be avoided', 'reduce dose', 'adjust dose'
        ]
        
        for keyword in high_severity_keywords:
            if keyword in description_lower:
                return 'high'
        
        for keyword in moderate_severity_keywords:
            if keyword in description_lower:
                return 'moderate'
        
        return 'low'


# Singleton instance
_medicine_graph_service = None

def get_medicine_graph_service() -> MedicineGraphService:
    """Get the singleton MedicineGraphService instance."""
    global _medicine_graph_service
    if _medicine_graph_service is None:
        _medicine_graph_service = MedicineGraphService()
    return _medicine_graph_service
