import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/healthz")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert "websearch" in data
    assert "filesearch" in data
    assert "computer" in data
    assert "airtable" in data
    assert "mcp" in data


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "running"
    assert data["docs"] == "/docs"
    assert data["health"] == "/healthz"


def test_run_endpoint_basic():
    """Test run endpoint with basic task"""
    response = client.post(
        "/run",
        json={"task": "What is Python?"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "result" in data
    assert "steps" in data
    assert "mode_flags" in data
    assert isinstance(data["steps"], list)
    assert isinstance(data["mode_flags"], dict)


def test_run_endpoint_invalid():
    """Test run endpoint with invalid request"""
    response = client.post("/run", json={})
    assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    # Run tests
    print("Running smoke tests...")
    test_health_endpoint()
    print("✓ Health endpoint works")
    
    test_root_endpoint()
    print("✓ Root endpoint works")
    
    test_run_endpoint_basic()
    print("✓ Run endpoint works")
    
    test_run_endpoint_invalid()
    print("✓ Validation works")
    
    print("\nAll tests passed!")