"""
Base analyzer class with common functionality for all analysis types.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import re

import anthropic
from app.config import settings

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """
    Base class for all analyzers providing common functionality.
    """
    
    def __init__(self):
        self.claude_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.version = "1.0.0"
    
    @abstractmethod
    def get_analysis_prompt(self, file_content: str, file_metadata: Dict[str, Any]) -> str:
        """Get the analysis prompt for this analyzer type."""
        pass
    
    @abstractmethod
    def get_analyzer_name(self) -> str:
        """Get the name of this analyzer."""
        pass
    
    def get_version(self) -> str:
        """Get analyzer version."""
        return self.version
    
    async def analyze(self, file_content: str, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run analysis using Claude AI.
        
        Args:
            file_content: The source code to analyze
            file_metadata: File metadata including size, type, etc.
            
        Returns:
            Analysis results with score, issues, and recommendations
        """
        try:
            logger.info(f"Starting {self.get_analyzer_name()} analysis")
            
            # Get analysis prompt
            prompt = self.get_analysis_prompt(file_content, file_metadata)
            
            # Call Claude API
            response = await self._call_claude(prompt)
            
            # Parse and validate response
            parsed_result = self._parse_claude_response(response)
            
            # Calculate score based on issues
            score = self._calculate_score(parsed_result.get("issues", []))
            
            return {
                "score": score,
                "issues": parsed_result.get("issues", []),
                "recommendations": parsed_result.get("recommendations", []),
                "metadata": {
                    "analyzer": self.get_analyzer_name(),
                    "version": self.version,
                    "claude_model": settings.claude_model,
                    "total_issues": len(parsed_result.get("issues", [])),
                    "issue_breakdown": self._get_issue_breakdown(parsed_result.get("issues", []))
                }
            }
            
        except Exception as e:
            logger.error(f"{self.get_analyzer_name()} analysis failed: {str(e)}")
            raise
    
    async def _call_claude(self, prompt: str) -> str:
        """Call Claude API with the analysis prompt."""
        try:
            message = self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=4000,
                temperature=0.1,  # Low temperature for consistent analysis
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            logger.error(f"Claude API call failed: {str(e)}")
            raise
    
    def _parse_claude_response(self, response: str) -> Dict[str, Any]:
        """Parse Claude's JSON response."""
        try:
            # Extract JSON from response (Claude sometimes adds explanation before/after)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response
            
            parsed = json.loads(json_str)
            
            # Validate required fields
            if "issues" not in parsed:
                parsed["issues"] = []
            if "recommendations" not in parsed:
                parsed["recommendations"] = []
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {str(e)}")
            logger.error(f"Response was: {response}")
            # Return fallback structure
            return {
                "issues": [],
                "recommendations": [
                    {
                        "title": "Analysis Parsing Error",
                        "description": "The analysis could not be properly parsed. Please try again.",
                        "priority": "high"
                    }
                ]
            }
    
    def _calculate_score(self, issues: List[Dict[str, Any]]) -> int:
        """
        Calculate score based on issues found.
        Starts at 100 and deducts points based on severity and count.
        """
        base_score = 100
        deductions = 0
        
        severity_weights = {
            "critical": 20,  # -20 points per critical issue
            "high": 10,      # -10 points per high issue  
            "medium": 5,     # -5 points per medium issue
            "low": 2         # -2 points per low issue
        }
        
        for issue in issues:
            severity = issue.get("severity", "medium").lower()
            deduction = severity_weights.get(severity, 5)  # Default to medium if unknown
            deductions += deduction
        
        # Apply diminishing returns for multiple issues of same severity
        if deductions > 50:
            deductions = 50 + (deductions - 50) * 0.5
        
        final_score = max(0, base_score - deductions)
        return round(final_score)
    
    def _get_issue_breakdown(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get breakdown of issues by severity."""
        breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for issue in issues:
            severity = issue.get("severity", "medium").lower()
            if severity in breakdown:
                breakdown[severity] += 1
        
        return breakdown
    
    def _get_response_format_instructions(self) -> str:
        """Get instructions for the expected response format."""
        return """
Please respond with a JSON object in the following format:
{
    "issues": [
        {
            "severity": "critical|high|medium|low",
            "title": "Brief issue title",
            "description": "Detailed description of the issue",
            "line_number": number or null,
            "code_snippet": "relevant code or null",
            "recommendation": "Specific fix recommendation"
        }
    ],
    "recommendations": [
        "High-level recommendation 1",
        "High-level recommendation 2"
    ]
}

Important: 
- Only include actual issues found in the code
- Be specific about line numbers when possible
- Provide actionable recommendations
- Focus on the most important issues first
"""

    def _build_base_prompt(self, file_content: str, file_metadata: Dict[str, Any]) -> str:
        """Build the base prompt with file information."""
        file_name = file_metadata.get("file_name", "unknown")
        file_size = file_metadata.get("file_size", 0)
        file_type = file_metadata.get("file_type", "unknown")
        
        return f"""
You are analyzing a Canva app file for quality, security, and best practices.

**File Information:**
- File Name: {file_name}
- File Size: {file_size} bytes
- File Type: {file_type}

**File Content:**
```{file_type}
{file_content}
```

**Context:**
This is a file from a Canva app, which runs in a sandboxed environment within Canva's design platform. Canva apps allow users to extend Canva's functionality and should follow security best practices, maintain high code quality, and provide excellent user experience.
""" 