"""
Tests for main FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "app_name" in data


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data


def test_api_status():
    """Test the API status endpoint."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "upload_endpoint" in data
    assert "analysis_endpoint" in data
    assert "supported_file_types" in data
    assert "max_file_size" in data


def test_docs_endpoint():
    """Test that docs are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_cors_headers():
    """Test CORS headers are properly set."""
    # Test with Origin header to trigger CORS
    headers = {"Origin": "http://localhost:3000"}
    response = client.get("/health", headers=headers)
    assert response.status_code == 200
    # CORS headers should be present when origin is allowed
    assert "access-control-allow-origin" in response.headers or "Access-Control-Allow-Origin" in response.headers 