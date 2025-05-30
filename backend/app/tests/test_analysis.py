"""
Tests for the analysis functionality including orchestrator and individual analyzers.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.analysis_orchestrator import AnalysisOrchestrator
from app.core.analyzers.security_analyzer import SecurityAnalyzer
from app.core.analyzers.code_quality_analyzer import CodeQualityAnalyzer
from app.core.analyzers.ui_ux_analyzer import UIUXAnalyzer

client = TestClient(app)


@pytest.fixture
def sample_react_component():
    """Sample React component for testing."""
    return """
import React, { useState, useEffect } from 'react';

const UserProfile = ({ userId }) => {
    const [userData, setUserData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchUserData(userId);
    }, [userId]);

    const fetchUserData = async (id) => {
        try {
            const response = await fetch(`/api/users/${id}`);
            const data = await response.json();
            setUserData(data);
        } catch (error) {
            console.error('Error fetching user data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleUserUpdate = (newData) => {
        // Potential XSS vulnerability - no validation
        document.getElementById('user-display').innerHTML = newData.bio;
    };

    if (loading) return <div>Loading...</div>;

    return (
        <div>
            <h1>{userData?.name}</h1>
            <p>{userData?.email}</p>
            <div id="user-display"></div>
            <button onClick={() => handleUserUpdate(userData)}>
                Update Profile
            </button>
        </div>
    );
};

export default UserProfile;
"""


@pytest.fixture
def file_metadata():
    """Sample file metadata for testing."""
    return {
        "file_name": "UserProfile.tsx",
        "file_size": 1234,
        "file_type": ".tsx"
    }


class TestAnalysisOrchestrator:
    """Tests for the AnalysisOrchestrator class."""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test that the orchestrator initializes all analyzers correctly."""
        orchestrator = AnalysisOrchestrator()
        
        assert orchestrator.security_analyzer is not None
        assert orchestrator.code_quality_analyzer is not None
        assert orchestrator.ui_ux_analyzer is not None
        assert len(orchestrator.analyzers) == 3
        assert "security" in orchestrator.analyzers
        assert "code_quality" in orchestrator.analyzers
        assert "ui_ux" in orchestrator.analyzers

    @pytest.mark.asyncio
    @patch('app.core.analyzers.base_analyzer.anthropic.Anthropic')
    async def test_orchestrator_analyze_file_success(self, mock_anthropic_class, sample_react_component, file_metadata):
        """Test successful file analysis through orchestrator."""
        # Mock the anthropic client
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock successful analysis response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = """
        {
            "issues": [
                {
                    "severity": "medium",
                    "title": "Test Issue",
                    "description": "This is a test issue",
                    "recommendation": "Fix this issue"
                }
            ],
            "recommendations": ["Overall recommendation"]
        }
        """
        mock_client.messages.create.return_value = mock_response
        
        orchestrator = AnalysisOrchestrator()
        result = await orchestrator.analyze_file(
            file_path="/test/UserProfile.tsx",
            file_content=sample_react_component,
            file_metadata=file_metadata
        )
        
        # Verify result structure
        assert result.file_name == "UserProfile.tsx"
        assert result.file_size == 1234
        assert result.overall_score >= 0
        assert result.overall_score <= 100
        assert result.total_issues >= 0
        assert len(result.issues) >= 0
        assert len(result.recommendations) > 0
        assert result.summary is not None

    @pytest.mark.asyncio
    @patch('app.core.analyzers.base_analyzer.anthropic.Anthropic')
    async def test_orchestrator_handles_analyzer_failure(self, mock_anthropic_class, sample_react_component, file_metadata):
        """Test orchestrator handling when one analyzer fails."""
        # Mock the anthropic client
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        # First call fails, subsequent calls succeed
        mock_response_success = MagicMock()
        mock_response_success.content = [MagicMock()]
        mock_response_success.content[0].text = """
        {
            "issues": [],
            "recommendations": ["No issues found"]
        }
        """
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("API Error")
            return mock_response_success
        
        mock_client.messages.create.side_effect = side_effect
        
        orchestrator = AnalysisOrchestrator()
        result = await orchestrator.analyze_file(
            file_path="/test/UserProfile.tsx",
            file_content=sample_react_component,
            file_metadata=file_metadata
        )
        
        # Should still return a result with fallback data
        assert result is not None
        assert result.overall_score >= 0
        
        # Should have completed successfully despite one analyzer failing
        assert len(result.issues) >= 0

    def test_scoring_weights(self):
        """Test that scoring weights are properly configured."""
        orchestrator = AnalysisOrchestrator()
        
        weights = orchestrator.SCORING_WEIGHTS
        assert weights["security"] == 0.30
        assert weights["code_quality"] == 0.30
        assert weights["ui_ux"] == 0.40
        
        # Weights should sum to 1.0
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001

    def test_calculate_overall_score(self):
        """Test overall score calculation with weighted averages."""
        orchestrator = AnalysisOrchestrator()
        
        analysis_results = {
            "security": {"score": 80},
            "code_quality": {"score": 90},
            "ui_ux": {"score": 70}
        }
        
        overall_score = orchestrator._calculate_overall_score(analysis_results)
        
        # Expected: 80*0.30 + 90*0.30 + 70*0.40 = 24 + 27 + 28 = 79
        assert overall_score == 79


class TestIndividualAnalyzers:
    """Tests for individual analyzer classes."""

    def test_security_analyzer_prompt_generation(self, sample_react_component, file_metadata):
        """Test that security analyzer generates appropriate prompts."""
        analyzer = SecurityAnalyzer()
        prompt = analyzer.get_analysis_prompt(sample_react_component, file_metadata)
        
        assert "security" in prompt.lower()
        assert "xss" in prompt.lower()
        assert "dangerouslySetInnerHTML" in prompt
        assert "UserProfile.tsx" in prompt
        assert sample_react_component in prompt

    def test_code_quality_analyzer_prompt_generation(self, sample_react_component, file_metadata):
        """Test that code quality analyzer generates appropriate prompts."""
        analyzer = CodeQualityAnalyzer()
        prompt = analyzer.get_analysis_prompt(sample_react_component, file_metadata)
        
        assert "code quality" in prompt.lower()
        assert "performance" in prompt.lower()
        assert "maintainability" in prompt.lower()
        assert "UserProfile.tsx" in prompt
        assert sample_react_component in prompt

    def test_ui_ux_analyzer_prompt_generation(self, sample_react_component, file_metadata):
        """Test that UI/UX analyzer generates appropriate prompts."""
        analyzer = UIUXAnalyzer()
        prompt = analyzer.get_analysis_prompt(sample_react_component, file_metadata)
        
        assert "accessibility" in prompt.lower()
        assert "user experience" in prompt.lower()
        assert "wcag" in prompt.lower()
        assert "UserProfile.tsx" in prompt
        assert sample_react_component in prompt

    def test_analyzer_names(self):
        """Test that analyzers return correct names."""
        security_analyzer = SecurityAnalyzer()
        code_quality_analyzer = CodeQualityAnalyzer()
        ui_ux_analyzer = UIUXAnalyzer()
        
        assert security_analyzer.get_analyzer_name() == "Security Analyzer"
        assert code_quality_analyzer.get_analyzer_name() == "Code Quality Analyzer"
        assert ui_ux_analyzer.get_analyzer_name() == "UI & UX Analyzer"


class TestAnalysisEndpoints:
    """Tests for analysis API endpoints."""

    def test_start_analysis_invalid_file_id(self):
        """Test starting analysis with invalid file ID."""
        response = client.post("/api/v1/analyze/nonexistent-file-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_analysis_status_not_found(self):
        """Test getting status for non-existent analysis."""
        response = client.get("/api/v1/analyze/nonexistent-file-id/status")
        
        assert response.status_code == 404
        assert "no analysis found" in response.json()["detail"].lower()

    def test_get_analysis_result_not_found(self):
        """Test getting results for non-existent analysis."""
        response = client.get("/api/v1/analyze/nonexistent-file-id/result")
        
        assert response.status_code == 404
        assert "no analysis found" in response.json()["detail"].lower()

    def test_cancel_analysis_not_found(self):
        """Test cancelling non-existent analysis."""
        response = client.delete("/api/v1/analyze/nonexistent-file-id")
        
        assert response.status_code == 404
        assert "no analysis found" in response.json()["detail"].lower()

    def test_api_status_includes_analysis(self):
        """Test that API status reflects analysis capabilities."""
        response = client.get("/api/v1/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "analysis_endpoint" in data
        assert "comprehensive" in data["analysis_endpoint"].lower()
        assert data["analysis_endpoint"] != "Coming in Phase 3"  # Should be available now


class TestAnalysisIntegration:
    """Integration tests for the complete analysis workflow."""

    @pytest.mark.asyncio
    async def test_analysis_workflow_components(self):
        """Test that all analysis components work together."""
        # This test verifies the integration without making actual API calls
        orchestrator = AnalysisOrchestrator()
        
        # Verify all components are properly connected
        assert hasattr(orchestrator, 'security_analyzer')
        assert hasattr(orchestrator, 'code_quality_analyzer')
        assert hasattr(orchestrator, 'ui_ux_analyzer')
        
        # Verify analyzers can generate prompts
        file_content = "const test = 'hello';"
        file_metadata = {"file_name": "test.js", "file_size": 20, "file_type": ".js"}
        
        for analyzer in orchestrator.analyzers.values():
            prompt = analyzer.get_analysis_prompt(file_content, file_metadata)
            assert prompt is not None
            assert len(prompt) > 0
            assert file_content in prompt

    def test_response_model_validation(self):
        """Test that response models validate correctly."""
        from app.models.response import AnalysisResult, AnalysisIssue, CategoryScoreBreakdown
        
        # Test AnalysisIssue validation
        issue = AnalysisIssue(
            severity="high",
            title="Test Issue",
            description="Test description",
            recommendation="Test recommendation"
        )
        assert issue.severity == "high"
        assert issue.title == "Test Issue"
        
        # Test CategoryScoreBreakdown validation
        breakdown = CategoryScoreBreakdown(
            score=85,
            weight=0.3,
            weighted_score=25.5,
            issue_count=2,
            severity_breakdown={"high": 1, "medium": 1, "low": 0, "critical": 0}
        )
        assert breakdown.score == 85
        assert breakdown.weight == 0.3
        
        # Test AnalysisResult validation
        result = AnalysisResult(
            file_path="/test/file.js",
            file_name="file.js",
            file_size=100,
            analysis_timestamp="2023-01-01T00:00:00",
            analysis_duration=5.5,
            overall_score=85,
            score_breakdown={"security": breakdown},
            total_issues=1,
            critical_issues=0,
            high_issues=1,
            issues=[issue],
            recommendations=["Test recommendation"],
            summary="Test summary"
        )
        assert result.overall_score == 85
        assert len(result.issues) == 1
        assert result.file_name == "file.js" 