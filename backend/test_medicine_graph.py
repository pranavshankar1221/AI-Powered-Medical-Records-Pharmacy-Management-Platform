"""
Test script for Medicine Knowledge Graph Integration
Tests drug interaction checking and alternative medicine recommendations.
"""

import sys
from pathlib import Path

# Add backend and ai_module directories to sys.path
BACKEND_DIR = Path(__file__).resolve().parent
AI_MODULE_DIR = BACKEND_DIR.parent / "ai_module"
sys.path.insert(0, str(AI_MODULE_DIR))
sys.path.insert(1, str(BACKEND_DIR))

import config
from database.neo4j_db import get_neo4j_driver, init_neo4j_db
from services.medicine_graph_service import get_medicine_graph_service


def test_neo4j_connection():
    """Test Neo4j database connection."""
    print("=" * 60)
    print("[TEST 1] Neo4j Connection")
    print("=" * 60)
    
    driver = get_neo4j_driver()
    if driver:
        try:
            driver.verify_connectivity()
            print("✅ Neo4j connection successful")
            return True
        except Exception as e:
            print(f"❌ Neo4j connection failed: {e}")
            return False
    else:
        print("❌ Neo4j driver not available")
        return False


def test_database_seeding():
    """Test database initialization and seeding."""
    print("\n" + "=" * 60)
    print("[TEST 2] Database Seeding")
    print("=" * 60)
    
    success = init_neo4j_db()
    if success:
        print("✅ Database initialized and seeded successfully")
        
        # Check node counts
        driver = get_neo4j_driver()
        with driver.session() as session:
            med_count = session.run("MATCH (m:Medicine) RETURN count(m) as count").single()["count"]
            print(f"   - Medicines in database: {med_count}")
        
        return True
    else:
        print("❌ Database initialization failed")
        return False


def test_drug_interactions():
    """Test drug-drug interaction checking."""
    print("\n" + "=" * 60)
    print("[TEST 3] Drug-Drug Interaction Checker")
    print("=" * 60)
    
    service = get_medicine_graph_service()
    
    # Test with sample medicine IDs (these should exist in your database)
    test_medicines = ["MED_001", "MED_002"]
    
    print(f"Testing interactions between medicines: {test_medicines}")
    result = service.check_drug_interactions(test_medicines)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"Has interactions: {result['has_interactions']}")
    print(f"Total interactions found: {result['total_interactions']}")
    
    if result['has_interactions']:
        print("\nInteractions found:")
        for idx, interaction in enumerate(result['interactions'], 1):
            print(f"\n  {idx}. {interaction['medicine_1']['name']} ↔ {interaction['medicine_2']['name']}")
            print(f"     Severity: {interaction['severity']}")
            print(f"     Description: {interaction['description'][:100]}...")
        
        print(f"\nSeverity breakdown: {result['severity_counts']}")
    
    print("✅ Drug interaction check completed")
    return True


def test_food_interactions():
    """Test food/substance interaction checking."""
    print("\n" + "=" * 60)
    print("[TEST 4] Food/Substance Interaction Checker")
    print("=" * 60)
    
    service = get_medicine_graph_service()
    
    # Test with sample medicine IDs
    test_medicines = ["MED_001", "MED_002"]
    
    print(f"Testing food interactions for medicines: {test_medicines}")
    result = service.check_food_substance_interactions(test_medicines)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"Has interactions: {result['has_interactions']}")
    print(f"Total interactions found: {result['total_interactions']}")
    
    if result['has_interactions']:
        print("\nInteractions found:")
        for idx, interaction in enumerate(result['interactions'], 1):
            print(f"\n  {idx}. {interaction['medicine']['name']} ↔ {interaction['substance']}")
            print(f"     Severity: {interaction['severity']}")
            print(f"     Description: {interaction['description'][:100]}...")
    
    print("✅ Food interaction check completed")
    return True


def test_alternative_medicines():
    """Test alternative medicine recommendations."""
    print("\n" + "=" * 60)
    print("[TEST 5] Alternative Medicine Recommendations")
    print("=" * 60)
    
    service = get_medicine_graph_service()
    
    # Test with a sample medicine ID
    test_medicine = "MED_001"
    
    print(f"Finding alternatives for medicine: {test_medicine}")
    result = service.get_alternative_medicines(test_medicine, limit=5)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    if "original_medicine" in result:
        print(f"\nOriginal medicine:")
        print(f"  - Name: {result['original_medicine']['name']}")
        print(f"  - Generic: {result['original_medicine']['generic_name']}")
        print(f"  - Categories: {', '.join(result['original_medicine']['categories'])}")
    
    print(f"\nAlternatives found: {result['total_alternatives']}")
    
    if result['alternatives']:
        print("\nRecommended alternatives:")
        for idx, alt in enumerate(result['alternatives'], 1):
            print(f"\n  {idx}. {alt['name']}")
            print(f"     Type: {alt['recommendation_type']}")
            print(f"     Reason: {alt['reason']}")
            print(f"     Price: ${alt['price']}")
    
    print("✅ Alternative medicine recommendation completed")
    return True


def test_medicine_details():
    """Test medicine details retrieval."""
    print("\n" + "=" * 60)
    print("[TEST 6] Medicine Details Retrieval")
    print("=" * 60)
    
    service = get_medicine_graph_service()
    
    # Test with a sample medicine ID
    test_medicine = "MED_001"
    
    print(f"Retrieving details for medicine: {test_medicine}")
    result = service.get_medicine_details(test_medicine)
    
    if result is None:
        print("❌ Medicine not found")
        return False
    
    print(f"\nMedicine Details:")
    print(f"  - ID: {result['id']}")
    print(f"  - Name: {result['name']}")
    print(f"  - Generic Name: {result['generic_name']}")
    print(f"  - Dosage Form: {result['dosage_form']}")
    print(f"  - Strength: {result['strength']}")
    print(f"  - Price: ${result['price']}")
    print(f"  - Categories: {', '.join(result['categories'])}")
    print(f"  - Manufacturers: {', '.join(result['manufacturers'])}")
    print(f"  - Drug Interaction Count: {result['drug_interaction_count']}")
    print(f"  - Substance Interaction Count: {result['substance_interaction_count']}")
    
    print("✅ Medicine details retrieval completed")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MEDIQR Medicine Knowledge Graph Integration Test Suite")
    print("=" * 60)
    
    tests = [
        test_neo4j_connection,
        test_database_seeding,
        test_drug_interactions,
        test_food_interactions,
        test_alternative_medicines,
        test_medicine_details
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
    else:
        print(f"❌ {total - passed} test(s) failed")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
