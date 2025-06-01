"""
Analysis endpoints for Canva app file analysis.
Provides endpoints for running comprehensive analysis on uploaded files.
"""

import os
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio

from ...models.response import AnalysisResponse, AnalysisStatusResponse, ErrorResponse
from ...core.analysis_orchestrator import AnalysisOrchestrator
from ...core.file_handler import FileHandler
from ...config import settings
from ...utils.filename_mapping import get_original_filename

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
        # Check if file exists - try all supported extensions
        upload_path = Path(settings.upload_dir)
        actual_file_path = None
        
        for ext in settings.supported_file_types:
            potential_path = upload_path / f"{file_id}{ext}"
            if potential_path.exists():
                actual_file_path = potential_path
                break
        
        if not actual_file_path:
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
    # Track progress state to prevent decreasing progress
    progress_state = {
        "max_progress": 0,
        "analyzers_completed": 0,
        "total_analyzers": 3,
        "current_stage": "initializing"
    }
    
    def update_progress(progress: int, message: str):
        """Progress callback that ensures progress never decreases."""
        # Only update if progress is higher than current max, or if it's a special stage
        if progress > progress_state["max_progress"] or progress in [92, 95, 100]:
            progress_state["max_progress"] = progress
            
            analysis_status_store[file_id].update({
                "progress": progress,
                "message": message
            })
            logger.info(f"Analysis progress for {file_id}: {progress}% - {message}")
        else:
            # Don't update progress, but log the attempt
            logger.debug(f"Skipped progress update for {file_id}: {progress}% (current: {progress_state['max_progress']}%) - {message}")

    def update_analyzer_completion(analyzer_name: str):
        """Track individual analyzer completion for better progress calculation."""
        progress_state["analyzers_completed"] += 1
        completed = progress_state["analyzers_completed"]
        total = progress_state["total_analyzers"]
        
        # Calculate progress based on completed analyzers: 10% + (completed/total * 80%)
        # This gives us: 10% start + 80% for analysis (26.7% per analyzer) + 10% for aggregation
        base_progress = 10
        analysis_progress = int((completed / total) * 80)
        calculated_progress = base_progress + analysis_progress
        
        # Use calculated progress instead of fixed ranges
        message = f"{analyzer_name} analysis completed ({completed}/{total} analyzers done)"
        
        if calculated_progress > progress_state["max_progress"]:
            progress_state["max_progress"] = calculated_progress
            analysis_status_store[file_id].update({
                "progress": calculated_progress,
                "message": message
            })
            logger.info(f"Analysis progress for {file_id}: {calculated_progress}% - {message}")

    try:
        logger.info(f"Starting background analysis for file {file_id}")
        
        # Update status to running (5% progress)
        progress_state["max_progress"] = 5
        analysis_status_store[file_id].update({
            "status": "running",
            "progress": 5,
            "message": "Initializing analysis..."
        })
        
        # Get original filename from metadata store
        original_filename = get_original_filename(file_id)
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Get file metadata with original filename
        file_stat = os.stat(file_path)
        file_metadata = {
            "file_name": original_filename if original_filename else Path(file_path).name,
            "file_extension": Path(file_path).suffix,
            "file_size": file_stat.st_size,
            "file_type": Path(file_path).suffix,
            "file_id": file_id,
            "original_filename": original_filename if original_filename else Path(file_path).name,
            "upload_timestamp": None
        }
        
        # Log the filename being used
        logger.info(f"Analyzing file: {file_metadata['file_name']} (ID: {file_id})")
        
        # Update to starting parallel analysis
        progress_state["max_progress"] = 10
        analysis_status_store[file_id].update({
            "progress": 10,
            "message": "Starting Security, Code Quality, and UI/UX analysis..."
        })
        
        # Initialize orchestrator and run analysis with modified progress callback
        orchestrator = AnalysisOrchestrator()
        
        # Create a custom progress callback that handles parallel execution better
        def parallel_progress_callback(progress: int, message: str):
            # Map different types of progress updates
            if "completed" in message.lower():
                # This is an analyzer completion - use our completion tracking
                if "security" in message.lower():
                    update_analyzer_completion("Security")
                elif "code quality" in message.lower():
                    update_analyzer_completion("Code Quality") 
                elif "ui/ux" in message.lower() or "ui ux" in message.lower():
                    update_analyzer_completion("UI/UX")
            elif progress >= 92:
                # Aggregation and final stages - always update
                update_progress(progress, message)
            elif progress <= 15:
                # Initial stages - always update
                update_progress(progress, message)
            else:
                # Individual analyzer start messages - update status message but not progress
                current_progress = progress_state["max_progress"]
                analysis_status_store[file_id].update({
                    "progress": current_progress,  # Keep current progress
                    "message": message  # Update message
                })
                logger.debug(f"Updated message for {file_id}: {message} (progress stays at {current_progress}%)")
        
        # Run the comprehensive analysis with improved progress tracking
        analysis_result = await orchestrator.analyze_file(
            file_path=file_path,
            file_content=file_content,
            file_metadata=file_metadata,
            progress_callback=parallel_progress_callback
        )
        
        # Final aggregation and completion stages
        update_progress(92, "Aggregating analysis results...")
        await asyncio.sleep(0.1)  # Small delay for UI responsiveness
        
        update_progress(95, "Calculating final scores...")
        await asyncio.sleep(0.1)
        
        # Update status to completed
        analysis_status_store[file_id].update({
            "status": "completed",
            "progress": 100,
            "message": "Analysis completed successfully",
            "result": analysis_result
        })
        
        logger.info(f"Analysis completed for file {file_metadata['file_name']} (ID: {file_id}) with score {analysis_result.overall_score}")
        
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