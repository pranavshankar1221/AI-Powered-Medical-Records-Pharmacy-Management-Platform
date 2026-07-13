"""
Medicine Knowledge Graph API Routes
Provides endpoints for drug interaction checking and alternative medicine recommendations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import logging

from services.medicine_graph_service import get_medicine_graph_service

logger = logging.getLogger("mediqr.api.medicine_graph")

router = APIRouter(prefix="/api/medicine-graph", tags=["Medicine Knowledge Graph"])


# Request/Response Models
class DrugInteractionRequest(BaseModel):
    medicine_ids: List[str]


class AlternativeMedicineRequest(BaseModel):
    medicine_id: str
    limit: Optional[int] = 5


class MedicineDetailsRequest(BaseModel):
    medicine_id: str


@router.post("/check-drug-interactions")
async def check_drug_interactions(request: DrugInteractionRequest):
    """
    Check for drug-drug interactions among a list of medicines.
    
    Args:
        request: Contains list of medicine IDs to check
        
    Returns:
        Interaction details including severity classification
    """
    try:
        service = get_medicine_graph_service()
        result = service.check_drug_interactions(request.medicine_ids)
        
        if "error" in result:
            raise HTTPException(status_code=503, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in check_drug_interactions endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-food-interactions")
async def check_food_interactions(request: DrugInteractionRequest):
    """
    Check for food/substance interactions for given medicines.
    
    Args:
        request: Contains list of medicine IDs to check
        
    Returns:
        Food/substance interaction details
    """
    try:
        service = get_medicine_graph_service()
        result = service.check_food_substance_interactions(request.medicine_ids)
        
        if "error" in result:
            raise HTTPException(status_code=503, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in check_food_interactions endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get-alternatives")
async def get_alternative_medicines(request: AlternativeMedicineRequest):
    """
    Get alternative medicine recommendations for a given medicine.
    
    Alternatives are prioritized by:
    1. Generic equivalents (same generic name)
    2. Therapeutic alternatives (same category)
    3. Same manufacturer
    
    Args:
        request: Contains medicine_id and optional limit
        
    Returns:
        List of alternative medicines with recommendation reasons
    """
    try:
        service = get_medicine_graph_service()
        result = service.get_alternative_medicines(
            request.medicine_id, 
            request.limit
        )
        
        if "error" in result:
            raise HTTPException(status_code=503, detail=result["error"])
        
        if not result.get("alternatives") and "error" not in result:
            raise HTTPException(status_code=404, detail="No alternatives found or medicine not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_alternative_medicines endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/medicine-details")
async def get_medicine_details(request: MedicineDetailsRequest):
    """
    Get detailed information about a medicine from the knowledge graph.
    
    Args:
        request: Contains medicine_id
        
    Returns:
        Complete medicine details including categories, manufacturers, and interaction counts
    """
    try:
        service = get_medicine_graph_service()
        result = service.get_medicine_details(request.medicine_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="Medicine not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_medicine_details endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for medicine graph service."""
    try:
        service = get_medicine_graph_service()
        if service.driver:
            # Verify connectivity
            service.driver.verify_connectivity()
            return {
                "status": "healthy",
                "neo4j_connected": True,
                "message": "Medicine Knowledge Graph service is operational"
            }
        else:
            return {
                "status": "unhealthy",
                "neo4j_connected": False,
                "message": "Neo4j driver not available"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "neo4j_connected": False,
            "message": f"Health check failed: {str(e)}"
        }
