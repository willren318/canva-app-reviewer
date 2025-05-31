"""
Analysis orchestrator that coordinates multiple analyzers and aggregates results.
Manages parallel analysis execution and result aggregation.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models.response import AnalysisResult
from .analyzers.security_analyzer import SecurityAnalyzer
from .analyzers.code_quality_analyzer import CodeQualityAnalyzer
from .analyzers.ui_ux_analyzer import UIUXAnalyzer

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """
    Orchestrates multiple analyzers to perform comprehensive analysis.
    Runs analyzers in parallel and aggregates their results.
    """
    
    # Scoring weights for different analysis categories
    SCORING_WEIGHTS = {
        "security": 0.30,      # 30% weight
        "code_quality": 0.30,  # 30% weight
        "ui_ux": 0.40         # 40% weight
    }
    
    def __init__(self):
        """Initialize the orchestrator with all analyzers."""
        self.security_analyzer = SecurityAnalyzer()
        self.code_quality_analyzer = CodeQualityAnalyzer()
        self.ui_ux_analyzer = UIUXAnalyzer()
        
        self.analyzers = {
            "security": self.security_analyzer,
            "code_quality": self.code_quality_analyzer,
            "ui_ux": self.ui_ux_analyzer
        }
    
    async def analyze_file(self, file_path: str, file_content: str, 
                          file_metadata: Dict[str, Any]) -> AnalysisResult:
        """
        Perform comprehensive analysis using all analyzers in parallel.
        
        Args:
            file_path: Path to the analyzed file
            file_content: Content of the file to analyze
            file_metadata: Metadata about the file (name, size, etc.)
            
        Returns:
            AnalysisResult: Aggregated analysis results with overall score
        """
        start_time = datetime.utcnow()
        
        logger.info(f"Starting comprehensive analysis for file: {file_metadata.get('file_name', 'unknown')}")
        
        try:
            # Run all analyzers in parallel
            analysis_tasks = [
                self._run_analyzer("security", file_content, file_metadata),
                self._run_analyzer("code_quality", file_content, file_metadata),
                self._run_analyzer("ui_ux", file_content, file_metadata)
            ]
            
            # Wait for all analyses to complete
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Process results and handle any failures
            analysis_results = {}
            for i, (category, result) in enumerate(zip(["security", "code_quality", "ui_ux"], results)):
                if isinstance(result, Exception):
                    logger.error(f"Analysis failed for {category}: {str(result)}")
                    # Create a fallback result for failed analysis
                    analysis_results[category] = self._create_fallback_result(category, str(result))
                else:
                    analysis_results[category] = result
            
            # Aggregate results
            aggregated_result = self._aggregate_results(
                analysis_results, file_path, file_metadata, start_time
            )
            
            end_time = datetime.utcnow()
            analysis_duration = (end_time - start_time).total_seconds()
            
            logger.info(
                f"Analysis completed for {file_metadata.get('file_name')} in {analysis_duration:.2f}s. "
                f"Overall score: {aggregated_result.overall_score}"
            )
            
            return aggregated_result
            
        except Exception as e:
            logger.error(f"Critical error during analysis orchestration: {str(e)}")
            # Return a minimal result indicating failure
            return self._create_error_result(file_path, file_metadata, str(e), start_time)
    
    async def _run_analyzer(self, category: str, file_content: str, 
                           file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single analyzer and return its results."""
        analyzer = self.analyzers[category]
        
        logger.debug(f"Starting {category} analysis")
        start_time = datetime.utcnow()
        
        try:
            result = await analyzer.analyze(file_content, file_metadata)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.debug(f"{category} analysis completed in {duration:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in {category} analyzer: {str(e)}")
            raise e
    
    def _aggregate_results(self, analysis_results: Dict[str, Dict[str, Any]], 
                          file_path: str, file_metadata: Dict[str, Any],
                          start_time: datetime) -> AnalysisResult:
        """Aggregate results from all analyzers into a single result."""
        
        # Calculate overall score using weighted average
        overall_score = self._calculate_overall_score(analysis_results)
        
        # Combine all issues from all analyzers with deduplication
        all_issues = []
        seen_issues = set()  # Track issues to prevent duplicates
        
        for category, result in analysis_results.items():
            issues = result.get("issues", [])
            # Add category information to each issue and deduplicate
            for issue in issues:
                issue["category"] = category
                
                # Create a unique identifier for this issue based on key characteristics
                issue_key = self._create_issue_key(issue)
                
                if issue_key not in seen_issues:
                    seen_issues.add(issue_key)
                    all_issues.append(issue)
                else:
                    # Issue already exists, merge category information
                    existing_issue = next(
                        (existing for existing in all_issues 
                         if self._create_issue_key(existing) == issue_key), 
                        None
                    )
                    if existing_issue:
                        # Add this category to the existing issue's categories
                        if "categories" not in existing_issue:
                            existing_issue["categories"] = [existing_issue["category"]]
                        if category not in existing_issue["categories"]:
                            existing_issue["categories"].append(category)
        
        # Sort issues by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 3))
        
        # Generate overall recommendations
        recommendations = self._generate_overall_recommendations(analysis_results, overall_score)
        
        # Create detailed score breakdown
        score_breakdown = {
            category: {
                "score": result.get("score", 0),
                "weight": self.SCORING_WEIGHTS[category],
                "weighted_score": result.get("score", 0) * self.SCORING_WEIGHTS[category],
                "issue_count": len(result.get("issues", [])),
                "severity_breakdown": self._get_severity_breakdown(result.get("issues", []))
            }
            for category, result in analysis_results.items()
        }
        
        # Calculate analysis statistics using deduplicated issues
        total_issues = len(all_issues)
        critical_issues = len([i for i in all_issues if i.get("severity") == "critical"])
        high_issues = len([i for i in all_issues if i.get("severity") == "high"])
        
        end_time = datetime.utcnow()
        analysis_duration = (end_time - start_time).total_seconds()
        
        return AnalysisResult(
            file_path=file_path,
            file_name=file_metadata.get("file_name", "unknown"),
            file_size=file_metadata.get("file_size", 0),
            analysis_timestamp=start_time.isoformat(),
            analysis_duration=round(analysis_duration, 2),
            overall_score=overall_score,
            score_breakdown=score_breakdown,
            total_issues=total_issues,
            critical_issues=critical_issues,
            high_issues=high_issues,
            issues=all_issues,
            recommendations=recommendations,
            summary=self._generate_summary(overall_score, total_issues, critical_issues, high_issues)
        )
    
    def _calculate_overall_score(self, analysis_results: Dict[str, Dict[str, Any]]) -> int:
        """Calculate weighted overall score from individual analyzer scores."""
        total_weighted_score = 0
        
        for category, weight in self.SCORING_WEIGHTS.items():
            result = analysis_results.get(category, {})
            score = result.get("score", 0)
            weighted_score = score * weight
            total_weighted_score += weighted_score
        
        return round(total_weighted_score)
    
    def _generate_overall_recommendations(self, analysis_results: Dict[str, Dict[str, Any]], 
                                        overall_score: int) -> List[str]:
        """Generate high-level recommendations based on all analysis results."""
        recommendations = []
        
        # Priority recommendations based on overall score
        if overall_score < 50:
            recommendations.append("🚨 URGENT: This code has critical issues that need immediate attention before deployment.")
        elif overall_score < 70:
            recommendations.append("⚠️ IMPORTANT: Address high-priority issues to improve code quality and security.")
        elif overall_score < 85:
            recommendations.append("✅ GOOD: Code is generally solid with some areas for improvement.")
        else:
            recommendations.append("🎉 EXCELLENT: High-quality code with minimal issues.")
        
        # Category-specific recommendations with better formatting
        for category, result in analysis_results.items():
            score = result.get("score", 0)
            issues = result.get("issues", [])
            critical_issues = [i for i in issues if i.get("severity") == "critical"]
            
            if category == "security":
                category_name = "Security"
                category_emoji = "🔒"
            elif category == "code_quality":
                category_name = "Code Quality"
                category_emoji = "⚙️"
            else:  # ui_ux
                category_name = "UI UX"
                category_emoji = "🎨"
            
            if critical_issues:
                critical_count = len(critical_issues)
                critical_text = f"{critical_count} critical issue" + ("s" if critical_count != 1 else "")
                recommendations.append(f"{category_emoji} {category_name}: {critical_text} need immediate fixes.")
            elif score < 60:
                recommendations.append(f"{category_emoji} {category_name}: Focus on addressing major concerns to improve score.")
            elif score >= 90:
                recommendations.append(f"{category_emoji} {category_name}: Excellent standards maintained.")
            else:
                # Score is 60-89 with no critical issues
                recommendations.append(f"{category_emoji} {category_name}: Good foundation with room for minor improvements.")
        
        # Add actionable next steps with better formatting
        all_issues = []
        for result in analysis_results.values():
            all_issues.extend(result.get("issues", []))
        
        if all_issues:
            top_issues = sorted(all_issues, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("severity", "low"), 3))[:3]
            recommendations.append("📋 Next Steps: Start by addressing the top 3 highest-priority issues:")
            for i, issue in enumerate(top_issues, 1):
                severity = issue.get('severity', 'unknown')
                title = issue.get('title', 'Unknown issue')
                recommendations.append(f"   {i}. {title} ({severity} severity)")
        
        return recommendations
    
    def _get_severity_breakdown(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get count of issues by severity level."""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for issue in issues:
            severity = issue.get("severity", "low")
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return severity_counts
    
    def _generate_summary(self, overall_score: int, total_issues: int, 
                         critical_issues: int, high_issues: int) -> str:
        """Generate a concise summary of the analysis results."""
        if overall_score >= 90:
            readiness_desc = "excellent Canva app readiness"
            status_emoji = "🎉"
        elif overall_score >= 80:
            readiness_desc = "good Canva app readiness"
            status_emoji = "✅"
        elif overall_score >= 60:
            readiness_desc = "moderate Canva app readiness"
            status_emoji = "⚠️"
        else:
            readiness_desc = "limited Canva app readiness"
            status_emoji = "🔍"
        
        # Fix grammar for issues count
        issue_text = f"{total_issues} issue" + ("s" if total_issues != 1 else "")
        
        priority_text = ""
        if critical_issues > 0:
            critical_text = f"{critical_issues} critical issue" + ("s" if critical_issues != 1 else "")
            priority_text = f" including {critical_text} requiring immediate attention"
        elif high_issues > 0:
            high_text = f"{high_issues} high-priority issue" + ("s" if high_issues != 1 else "")
            priority_text = f" including {high_text} to address"
        
        return (f"{status_emoji} Analysis complete: {readiness_desc} with a score of {overall_score}/100. "
                f"Found {issue_text}{priority_text}.")
    
    def _create_fallback_result(self, category: str, error_message: str) -> Dict[str, Any]:
        """Create a fallback result when an analyzer fails."""
        return {
            "score": 0,
            "issues": [{
                "severity": "critical",
                "title": f"{category.replace('_', ' ').title()} Analysis Failed",
                "description": f"The {category} analyzer encountered an error: {error_message}",
                "line_number": None,
                "code_snippet": None,
                "recommendation": "Please check the file format and try again. Contact support if the issue persists."
            }],
            "recommendations": [f"Re-run {category} analysis after fixing file issues."],
            "analyzer_name": f"{category.replace('_', ' ').title()} Analyzer",
            "error": error_message
        }
    
    def _create_error_result(self, file_path: str, file_metadata: Dict[str, Any], 
                           error_message: str, start_time: datetime) -> AnalysisResult:
        """Create an error result when the entire analysis fails."""
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        return AnalysisResult(
            file_path=file_path,
            file_name=file_metadata.get("file_name", "unknown"),
            file_size=file_metadata.get("file_size", 0),
            analysis_timestamp=start_time.isoformat(),
            analysis_duration=round(duration, 2),
            overall_score=0,
            score_breakdown={},
            total_issues=1,
            critical_issues=1,
            high_issues=0,
            issues=[{
                "severity": "critical",
                "title": "Analysis System Error",
                "description": f"The analysis system encountered a critical error: {error_message}",
                "line_number": None,
                "code_snippet": None,
                "recommendation": "Please try uploading the file again or contact support if the issue persists.",
                "category": "system"
            }],
            recommendations=["Re-upload the file and try analysis again."],
            summary=f"Analysis failed due to system error: {error_message}"
        )
    
    def _create_issue_key(self, issue: Dict[str, Any]) -> str:
        """
        Create a unique key for an issue to identify duplicates.
        Based on title, line number, and code snippet.
        """
        title = issue.get("title", "")
        if title is None:
            title = ""
        title = title.lower().strip()
        
        line_number = issue.get("line_number")
        
        code_snippet = issue.get("code_snippet", "")
        if code_snippet is None:
            code_snippet = ""
        code_snippet = code_snippet.strip()
        
        # Normalize title to catch variations
        title_normalized = title.replace("via", "").replace("using", "").replace(" - ", " ").strip()
        
        # Create a composite key
        key_parts = [title_normalized]
        
        if line_number is not None:
            key_parts.append(f"line:{line_number}")
            
        if code_snippet:
            # Use first 50 characters of code snippet
            key_parts.append(f"code:{code_snippet[:50]}")
        
        return "|".join(key_parts) 