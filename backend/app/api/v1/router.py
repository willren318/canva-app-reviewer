"""
Main API router for version 1 endpoints.
"""

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...models.response import APIStatusResponse
from .upload import router as upload_router
from .analyze import router as analyze_router

logger = logging.getLogger(__name__)

# Create main API router
router = APIRouter()

# Include sub-routers
router.include_router(upload_router, tags=["upload"])
router.include_router(analyze_router, tags=["analysis"])


@router.get("/status", response_model=APIStatusResponse)
async def get_api_status():
    """
    Get the current status of the API and its endpoints.
    
    Returns:
        APIStatusResponse: Current API status and capabilities
    """
    try:
        return APIStatusResponse(
            message="Canva App Reviewer API v1 is running",
            version="1.0.0",
            upload_endpoint="Available - supports .js and .tsx files",
            analysis_endpoint="Available - comprehensive 3-category analysis",
            supported_file_types=[".js", ".tsx"],
            max_file_size="10MB"
        )
    except Exception as e:
        logger.error(f"Error getting API status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "message": "API status check failed",
                "error": str(e)
            }
        ) 