"""
File utility functions for handling uploads and validation.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any

from fastapi import UploadFile

from app.config import settings

logger = logging.getLogger(__name__)


async def validate_file(file: UploadFile) -> Dict[str, Any]:
    """
    Validate uploaded file for size, extension, and basic properties.
    
    Args:
        file: The uploaded file
        
    Returns:
        Dict with validation results
    """
    try:
        # Check if file exists
        if not file:
            return {
                "valid": False,
                "error": "No file provided"
            }
        
        # Check filename
        if not file.filename:
            return {
                "valid": False,
                "error": "No filename provided"
            }
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.allowed_extensions:
            return {
                "valid": False,
                "error": f"File type {file_ext} not allowed. Allowed types: {', '.join(settings.allowed_extensions)}"
            }
        
        # Check file size
        if file.size and file.size > settings.max_upload_size:
            size_mb = settings.max_upload_size / (1024 * 1024)
            return {
                "valid": False,
                "error": f"File size exceeds {size_mb}MB limit"
            }
        
        # Basic content type check
        if file.content_type:
            allowed_content_types = [
                "text/javascript",
                "application/javascript",
                "text/typescript",
                "application/typescript",
                "text/plain",  # Sometimes browsers send this for .js/.tsx files
                "application/octet-stream"  # Fallback
            ]
            
            if file.content_type not in allowed_content_types:
                logger.warning(f"Unexpected content type: {file.content_type} for file {file.filename}")
                # Don't reject based on content type alone, as browsers can be inconsistent
        
        return {
            "valid": True,
            "file_extension": file_ext,
            "file_size": file.size,
            "content_type": file.content_type
        }
        
    except Exception as e:
        logger.error(f"File validation error: {str(e)}")
        return {
            "valid": False,
            "error": f"Validation error: {str(e)}"
        }


async def save_upload_file(file: UploadFile, file_id: str, upload_path: Path) -> Path:
    """
    Save uploaded file to disk with unique filename.
    
    Args:
        file: The uploaded file
        file_id: Unique identifier for the file
        upload_path: Directory to save the file
        
    Returns:
        Path to the saved file
    """
    try:
        # Determine file extension
        original_ext = Path(file.filename).suffix.lower()
        
        # Create filename with file_id
        filename = f"{file_id}{original_ext}"
        file_path = upload_path / filename
        
        # Read and write file content
        content = await file.read()
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Reset file position for potential re-reading
        await file.seek(0)
        
        logger.info(f"File saved: {file.filename} -> {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Failed to save file: {str(e)}")
        raise


def cleanup_old_files(upload_path: Path, max_age_hours: int = 24):
    """
    Clean up old uploaded files.
    
    Args:
        upload_path: Directory containing uploaded files
        max_age_hours: Maximum age of files to keep (in hours)
    """
    try:
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for file_path in upload_path.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    logger.info(f"Cleaned up old file: {file_path}")
                    
    except Exception as e:
        logger.error(f"File cleanup error: {str(e)}")


def get_file_stats(file_path: Path) -> Dict[str, Any]:
    """
    Get file statistics.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dict with file statistics
    """
    try:
        if not file_path.exists():
            return {"exists": False}
        
        stat = file_path.stat()
        
        return {
            "exists": True,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "extension": file_path.suffix.lower(),
            "name": file_path.name
        }
        
    except Exception as e:
        logger.error(f"Failed to get file stats: {str(e)}")
        return {"exists": False, "error": str(e)} 