"""
Response models for the Canva App Reviewer API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="ISO timestamp")
    version: str = Field(..., description="API version")


class APIStatusResponse(BaseModel):
    """Response model for API status endpoint."""
    message: str = Field(..., description="Status message")
    version: str = Field(..., description="API version")
    upload_endpoint: str = Field(..., description="File upload endpoint status")
    analysis_endpoint: str = Field(..., description="Analysis endpoint status")
    supported_file_types: List[str] = Field(..., description="Supported file extensions")
    max_file_size: str = Field(..., description="Maximum file size limit")


class FileUploadResponse(BaseModel):
    """Response model for file upload endpoint."""
    success: bool = Field(..., description="Upload success status")
    message: str = Field(..., description="Upload status message")
    file_id: str = Field(..., description="Unique identifier for the uploaded file")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="File type/extension")
    upload_timestamp: str = Field(..., description="ISO timestamp of upload")


class FileInfoResponse(BaseModel):
    """Response model for file information endpoint."""
    file_id: str = Field(..., description="Unique file identifier")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="File type/extension")
    upload_timestamp: str = Field(..., description="ISO timestamp of upload")
    status: str = Field(..., description="File processing status")


class ErrorResponse(BaseModel):
    """Response model for error cases."""
    success: bool = Field(default=False, description="Request success status")
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")


# Analysis-specific response models

class AnalysisIssue(BaseModel):
    """Model for individual analysis issues."""
    severity: str = Field(..., description="Issue severity: critical, high, medium, low")
    title: str = Field(..., description="Brief issue title")
    description: str = Field(..., description="Detailed issue description")
    line_number: Optional[int] = Field(None, description="Line number where issue occurs")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")
    recommendation: str = Field(..., description="Suggested fix or improvement")
    category: Optional[str] = Field(None, description="Analysis category: security, code_quality, ui_ux")


class CategoryScoreBreakdown(BaseModel):
    """Model for individual category score breakdown."""
    score: int = Field(..., description="Category score (0-100)")
    weight: float = Field(..., description="Weight of this category in overall score")
    weighted_score: float = Field(..., description="Score * weight")
    issue_count: int = Field(..., description="Total number of issues in this category")
    severity_breakdown: Dict[str, int] = Field(..., description="Count of issues by severity")


class AnalysisResult(BaseModel):
    """Complete analysis result model."""
    file_path: str = Field(..., description="Path to the analyzed file")
    file_name: str = Field(..., description="Name of the analyzed file")
    file_size: int = Field(..., description="File size in bytes")
    analysis_timestamp: str = Field(..., description="ISO timestamp when analysis started")
    analysis_duration: float = Field(..., description="Analysis duration in seconds")
    
    # Overall scoring
    overall_score: int = Field(..., description="Overall quality score (0-100)")
    score_breakdown: Dict[str, CategoryScoreBreakdown] = Field(..., description="Detailed score breakdown by category")
    
    # Issue summary
    total_issues: int = Field(..., description="Total number of issues found")
    critical_issues: int = Field(..., description="Number of critical issues")
    high_issues: int = Field(..., description="Number of high-priority issues")
    
    # Detailed results
    issues: List[AnalysisIssue] = Field(..., description="List of all issues found")
    recommendations: List[str] = Field(..., description="High-level recommendations")
    summary: str = Field(..., description="Human-readable analysis summary")


class AnalysisResponse(BaseModel):
    """Response model for analysis endpoint."""
    success: bool = Field(..., description="Analysis success status")
    message: str = Field(..., description="Analysis status message")
    analysis_result: Optional[AnalysisResult] = Field(None, description="Detailed analysis results")
    error: Optional[str] = Field(None, description="Error message if analysis failed")


class AnalysisStatusResponse(BaseModel):
    """Response model for analysis status check."""
    file_id: str = Field(..., description="File identifier")
    status: str = Field(..., description="Analysis status: pending, running, completed, failed")
    progress: Optional[int] = Field(None, description="Analysis progress percentage")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    message: str = Field(..., description="Status message") 