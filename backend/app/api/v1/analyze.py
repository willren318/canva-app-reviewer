"""
Analysis endpoints for Canva app file analysis.
Provides endpoints for running comprehensive analysis on uploaded files.
"""

import os
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from ...models.response import AnalysisResponse, AnalysisStatusResponse, ErrorResponse
from ...core.analysis_orchestrator import AnalysisOrchestrator
from ...core.file_handler import FileHandler
from ...config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Store for tracking analysis status (in production, use Redis or database)
analysis_status_store = {}


@router.post("/analyze/{file_id}", response_model=AnalysisResponse)
async def analyze_file(file_id: str, background_tasks: BackgroundTasks):
    """
    Start comprehensive analysis of an uploaded file.
    
    Args:
        file_id: Unique identifier of the uploaded file
        background_tasks: FastAPI background tasks for async processing
        
    Returns:
        AnalysisResponse: Analysis initiation confirmation and results
    """
    try:
        # Check if file exists
        file_path = Path(settings.upload_dir) / f"{file_id}.js"
        tsx_file_path = Path(settings.upload_dir) / f"{file_id}.tsx"
        
        actual_file_path = None
        if file_path.exists():
            actual_file_path = file_path
        elif tsx_file_path.exists():
            actual_file_path = tsx_file_path
        else:
            raise HTTPException(
                status_code=404,
                detail=f"File with ID {file_id} not found"
            )
        
        # Check if analysis is already running
        if file_id in analysis_status_store:
            current_status = analysis_status_store[file_id]["status"]
            if current_status in ["pending", "running"]:
                return AnalysisResponse(
                    success=False,
                    message="Analysis is already in progress for this file",
                    error="Analysis already running"
                )
        
        # Mark analysis as pending
        analysis_status_store[file_id] = {
            "status": "pending",
            "progress": 0,
            "message": "Analysis queued for processing"
        }
        
        # Start analysis in background
        background_tasks.add_task(
            run_analysis_background,
            file_id,
            str(actual_file_path)
        )
        
        return AnalysisResponse(
            success=True,
            message=f"Analysis started for file {file_id}. Use GET /api/v1/analyze/{file_id}/status to check progress.",
            analysis_result=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting analysis for file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start analysis: {str(e)}"
        )


@router.get("/analyze/{file_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(file_id: str):
    """
    Get the current status of file analysis.
    
    Args:
        file_id: Unique identifier of the file being analyzed
        
    Returns:
        AnalysisStatusResponse: Current analysis status and progress
    """
    try:
        if file_id not in analysis_status_store:
            raise HTTPException(
                status_code=404,
                detail=f"No analysis found for file {file_id}"
            )
        
        status_info = analysis_status_store[file_id]
        
        return AnalysisStatusResponse(
            file_id=file_id,
            status=status_info["status"],
            progress=status_info.get("progress", 0),
            estimated_completion=status_info.get("estimated_completion"),
            message=status_info.get("message", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis status for file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analysis status: {str(e)}"
        )


@router.get("/analyze/{file_id}/result", response_model=AnalysisResponse)
async def get_analysis_result(file_id: str):
    """
    Get the completed analysis results for a file.
    
    Args:
        file_id: Unique identifier of the analyzed file
        
    Returns:
        AnalysisResponse: Complete analysis results if available
    """
    try:
        if file_id not in analysis_status_store:
            raise HTTPException(
                status_code=404,
                detail=f"No analysis found for file {file_id}"
            )
        
        status_info = analysis_status_store[file_id]
        
        if status_info["status"] != "completed":
            return AnalysisResponse(
                success=False,
                message=f"Analysis not completed. Current status: {status_info['status']}",
                analysis_result=None
            )
        
        # Return the stored analysis result
        analysis_result = status_info.get("result")
        if not analysis_result:
            raise HTTPException(
                status_code=500,
                detail="Analysis marked as completed but no results found"
            )
        
        return AnalysisResponse(
            success=True,
            message="Analysis completed successfully",
            analysis_result=analysis_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis result for file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analysis result: {str(e)}"
        )


async def run_analysis_background(file_id: str, file_path: str):
    """
    Background task to run the comprehensive analysis.
    
    Args:
        file_id: Unique identifier of the file
        file_path: Path to the file to analyze
    """
    try:
        logger.info(f"Starting background analysis for file {file_id}")
        
        # Update status to running
        analysis_status_store[file_id].update({
            "status": "running",
            "progress": 10,
            "message": "Analysis in progress..."
        })
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Get file metadata
        file_stat = os.stat(file_path)
        file_metadata = {
            "file_name": Path(file_path).name,
            "file_size": file_stat.st_size,
            "file_type": Path(file_path).suffix
        }
        
        # Update progress
        analysis_status_store[file_id].update({
            "progress": 30,
            "message": "Running security analysis..."
        })
        
        # Initialize orchestrator and run analysis
        orchestrator = AnalysisOrchestrator()
        
        # Update progress
        analysis_status_store[file_id].update({
            "progress": 50,
            "message": "Running code quality analysis..."
        })
        
        # Run the comprehensive analysis
        analysis_result = await orchestrator.analyze_file(
            file_path=file_path,
            file_content=file_content,
            file_metadata=file_metadata
        )
        
        # Update status to completed
        analysis_status_store[file_id].update({
            "status": "completed",
            "progress": 100,
            "message": "Analysis completed successfully",
            "result": analysis_result
        })
        
        logger.info(f"Analysis completed for file {file_id} with score {analysis_result.overall_score}")
        
    except Exception as e:
        logger.error(f"Background analysis failed for file {file_id}: {str(e)}")
        
        # Update status to failed
        analysis_status_store[file_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Analysis failed: {str(e)}",
            "error": str(e)
        })


@router.delete("/analyze/{file_id}")
async def cancel_analysis(file_id: str):
    """
    Cancel an ongoing analysis or remove analysis results.
    
    Args:
        file_id: Unique identifier of the file
        
    Returns:
        Success confirmation
    """
    try:
        if file_id not in analysis_status_store:
            raise HTTPException(
                status_code=404,
                detail=f"No analysis found for file {file_id}"
            )
        
        # Remove from status store
        del analysis_status_store[file_id]
        
        return {"success": True, "message": f"Analysis data for file {file_id} has been removed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling analysis for file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel analysis: {str(e)}"
        ) 