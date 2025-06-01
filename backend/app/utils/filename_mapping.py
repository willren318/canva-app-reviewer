"""
Simple filename mapping utility to preserve original filenames.
Much simpler than a complex metadata storage system.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Simple in-memory mapping of file_id -> original_filename
_filename_mapping: Dict[str, str] = {}


def store_original_filename(file_id: str, original_filename: str) -> None:
    """
    Store the mapping of file_id to original filename.
    
    Args:
        file_id: Unique file identifier
        original_filename: Original filename from upload
    """
    _filename_mapping[file_id] = original_filename
    logger.debug(f"Stored filename mapping: {file_id} -> {original_filename}")


def get_original_filename(file_id: str) -> Optional[str]:
    """
    Get the original filename for a file_id.
    
    Args:
        file_id: Unique file identifier
        
    Returns:
        Original filename or None if not found
    """
    filename = _filename_mapping.get(file_id)
    if filename:
        logger.debug(f"Retrieved filename mapping: {file_id} -> {filename}")
    else:
        logger.warning(f"No filename mapping found for file_id: {file_id}")
    return filename


def remove_filename_mapping(file_id: str) -> bool:
    """
    Remove the filename mapping for a file_id.
    
    Args:
        file_id: Unique file identifier
        
    Returns:
        True if mapping was removed, False if not found
    """
    if file_id in _filename_mapping:
        original_filename = _filename_mapping.pop(file_id)
        logger.debug(f"Removed filename mapping: {file_id} -> {original_filename}")
        return True
    else:
        logger.warning(f"No filename mapping to remove for file_id: {file_id}")
        return False


def get_all_mappings() -> Dict[str, str]:
    """Get all current filename mappings (for debugging)."""
    return _filename_mapping.copy()


def clear_all_mappings() -> int:
    """
    Clear all filename mappings.
    
    Returns:
        Number of mappings cleared
    """
    count = len(_filename_mapping)
    _filename_mapping.clear()
    logger.info(f"Cleared {count} filename mappings")
    return count 