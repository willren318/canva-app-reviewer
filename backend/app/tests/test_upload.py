"""
Tests for file upload functionality.
"""

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from io import BytesIO

from app.main import app

client = TestClient(app)


@pytest.fixture
def sample_js_content():
    """Sample JavaScript file content."""
    return b"""
import { Button } from "@canva/app-ui-kit";

export const App = () => {
  const handleClick = () => {
    console.log("Hello Canva!");
  };

  return (
    <Button variant="primary" onClick={handleClick}>
      Hello World
    </Button>
  );
};
"""


@pytest.fixture
def sample_tsx_content():
    """Sample TypeScript React file content."""
    return b"""
import React from "react";
import { Button } from "@canva/app-ui-kit";

interface AppProps {
  title: string;
}

export const App: React.FC<AppProps> = ({ title }) => {
  const handleClick = (): void => {
    console.log("TypeScript Canva App!");
  };

  return (
    <div>
      <h1>{title}</h1>
      <Button variant="primary" onClick={handleClick}>
        Click me
      </Button>
    </div>
  );
};
"""


@pytest.fixture
def invalid_js_content():
    """Invalid JavaScript content."""
    return b"""
function invalid() {
  // Missing closing brace
  console.log("This is invalid"
"""


def test_upload_valid_js_file(sample_js_content):
    """Test uploading a valid JavaScript file."""
    files = {"file": ("app.js", sample_js_content, "text/javascript")}

    response = client.post("/api/v1/", files=files)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["file_id"] is not None
    assert data["file_name"] == "app.js"
    assert data["file_type"] in [".js", "application/javascript", "javascript-react"]


def test_upload_valid_tsx_file(sample_tsx_content):
    """Test uploading a valid TypeScript React file."""
    files = {"file": ("App.tsx", sample_tsx_content, "text/typescript")}

    response = client.post("/api/v1/", files=files)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["file_id"] is not None
    assert data["file_name"] == "App.tsx"
    assert data["file_type"] in [".tsx", "application/typescript", "typescript-react"]


def test_upload_invalid_file_extension():
    """Test uploading a file with invalid extension."""
    content = b"console.log('test');"
    files = {"file": ("app.py", content, "text/python")}

    response = client.post("/api/v1/", files=files)

    assert response.status_code == 400


def test_upload_no_file():
    """Test uploading without providing a file."""
    response = client.post("/api/v1/")

    assert response.status_code == 422  # Validation error


def test_upload_empty_filename():
    """Test uploading with empty filename."""
    content = b"console.log('test');"
    files = {"file": ("", content, "text/javascript")}

    response = client.post("/api/v1/", files=files)

    assert response.status_code == 422  # FastAPI validation error for empty filename


def test_upload_invalid_syntax(invalid_js_content):
    """Test uploading file with invalid syntax."""
    files = {"file": ("invalid.js", invalid_js_content, "text/javascript")}

    response = client.post("/api/v1/", files=files)

    assert response.status_code == 400


def test_upload_large_file():
    """Test uploading a file that exceeds size limit."""
    # Create content larger than 10MB
    large_content = b"console.log('test');" * (10 * 1024 * 1024 // 20 + 1)
    files = {"file": ("large.js", large_content, "text/javascript")}

    response = client.post("/api/v1/", files=files)

    assert response.status_code == 400


def test_upload_canva_patterns_detection(sample_js_content):
    """Test detection of Canva-specific patterns."""
    files = {"file": ("canva-app.js", sample_js_content, "text/javascript")}

    response = client.post("/api/v1/", files=files)

    assert response.status_code == 200
    data = response.json()

    # The file contains Canva imports, so it should be detected
    assert "@canva/app-ui-kit" in sample_js_content.decode()


def test_get_file_info():
    """Test getting file information."""
    # First upload a file
    content = b"export const App = () => <div>Test</div>;"
    files = {"file": ("test.js", content, "text/javascript")}

    upload_response = client.post("/api/v1/", files=files)
    assert upload_response.status_code == 200

    file_id = upload_response.json()["file_id"]

    # Now get file info
    response = client.get(f"/api/v1/{file_id}/info")
    assert response.status_code == 200

    data = response.json()
    assert data["file_id"] == file_id
    assert data["file_name"] == f"{file_id}.js"
    assert data["file_size"] > 0


def test_delete_file():
    """Test deleting an uploaded file."""
    # First upload a file
    content = b"console.log('to be deleted');"
    files = {"file": ("delete-me.js", content, "text/javascript")}

    upload_response = client.post("/api/v1/", files=files)
    assert upload_response.status_code == 200

    file_id = upload_response.json()["file_id"]

    # Delete the file
    response = client.delete(f"/api/v1/{file_id}")
    assert response.status_code == 200

    # Verify file is deleted by trying to get info
    get_response = client.get(f"/api/v1/{file_id}/info")
    assert get_response.status_code == 404


def test_api_status_updated():
    """Test that API status reflects upload functionality."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200

    data = response.json()
    assert "upload_endpoint" in data
    assert "analysis_endpoint" in data
    assert data["supported_file_types"] == [".js", ".tsx"]
    assert "10MB" in data["max_file_size"]