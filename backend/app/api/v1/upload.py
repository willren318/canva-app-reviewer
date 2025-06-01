"""
File upload endpoints for Canva app files.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.response import FileUploadResponse, FileInfoResponse, ErrorResponse
from app.core.file_handler import FileHandler
from app.utils.file_utils import validate_file, save_upload_file
from app.utils.filename_mapping import store_original_filename, get_original_filename, remove_filename_mapping

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="Canva app file (.js, .jsx, or .tsx)")
) -> FileUploadResponse:
    """
    Upload a Canva app file for analysis.
    
    Accepts .js, .jsx, and .tsx files up to 10MB.
    
    **Visual Analysis Support:**
    - .js files: Full analysis with screenshot capture, visual review, and code analysis
    - .jsx/.tsx files: Code-only analysis (no screenshots due to transpilation requirements)
    
    Returns a file ID for tracking the analysis.
    """
    try:
        # Validate file
        validation_result = await validate_file(file)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=validation_result["error"]
            )
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Create upload directory if it doesn't exist
        upload_path = Path(settings.upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Save file to disk
        file_path = await save_upload_file(file, file_id, upload_path)
        
        # Store simple filename mapping
        store_original_filename(file_id, file.filename)
        
        # Create file handler instance
        file_handler = FileHandler(file_path, file_id)
        
        # Validate file content (syntax check)
        content_validation = await file_handler.validate_content()
        if not content_validation["valid"]:
            # Clean up the uploaded file and filename mapping
            file_path.unlink(missing_ok=True)
            remove_filename_mapping(file_id)
            raise HTTPException(
                status_code=400,
                detail=f"File content validation failed: {content_validation['error']}"
            )
        
        logger.info(f"File uploaded successfully: {file.filename} -> {file_id}")
        
        return FileUploadResponse(
            success=True,
            message="File uploaded successfully",
            file_id=file_id,
            file_name=file.filename,  # Use original filename in response
            file_size=file.size,
            file_type=content_validation.get("file_type", "unknown"),
            upload_timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/{file_id}/info", response_model=FileInfoResponse)
async def get_file_info(file_id: str) -> FileInfoResponse:
    """Get information about an uploaded file."""
    try:
        # Check if file exists - try all supported extensions
        upload_path = Path(settings.upload_dir)
        file_path = None
        
        for ext in settings.supported_file_types:
            potential_path = upload_path / f"{file_id}{ext}"
            if potential_path.exists():
                file_path = potential_path
                break
        
        if not file_path or not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        # Get file stats
        stat = file_path.stat()
        
        # Get original filename from filename mapping
        original_filename = get_original_filename(file_id)
        
        # Use original filename if available, otherwise fall back to internal filename
        display_filename = original_filename if original_filename else file_path.name
        upload_timestamp = datetime.fromtimestamp(stat.st_ctime).isoformat()
        
        return FileInfoResponse(
            file_id=file_id,
            file_name=display_filename,
            file_size=stat.st_size,
            file_type=file_path.suffix,
            upload_timestamp=upload_timestamp,
            status="uploaded"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file info: {str(e)}"
        )


@router.delete("/{file_id}")
async def delete_file(file_id: str) -> JSONResponse:
    """Delete an uploaded file and its filename mapping."""
    try:
        upload_path = Path(settings.upload_dir)
        file_deleted = False
        
        # Try all supported extensions
        for ext in settings.supported_file_types:
            file_path = upload_path / f"{file_id}{ext}"
            if file_path.exists():
                file_path.unlink()
                file_deleted = True
                logger.info(f"File deleted: {file_id}{ext}")
                break
        
        # Clean up filename mapping
        remove_filename_mapping(file_id)
        
        if file_deleted:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "File and filename mapping deleted successfully",
                    "file_id": file_id,
                    "file_deleted": file_deleted
                }
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {str(e)}"
        ) 