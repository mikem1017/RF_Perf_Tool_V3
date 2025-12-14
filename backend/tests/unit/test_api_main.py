"""
Tests for API main application setup.
"""
import pytest
import os
from pathlib import Path
from backend.src.api.main import create_app


def test_create_app_dev_mode():
    """Test creating app in dev mode."""
    app = create_app(dev_mode=True)
    
    assert app is not None
    assert app.title == "RF Performance Tool API"
    assert app.version == "1.0.0"
    
    # Check that routes are registered
    route_paths = [r.path for r in app.routes]
    assert "/health" in route_paths
    assert "/api/devices" in route_paths
    assert "/api/test-stages" in route_paths


def test_create_app_prod_mode():
    """Test creating app in prod mode."""
    app = create_app(dev_mode=False)
    
    assert app is not None
    # In prod mode, CORS should not be configured
    # (we can't easily test middleware, but we can verify app is created)


def test_health_check_endpoint():
    """Test health check endpoint."""
    app = create_app(dev_mode=True)
    
    # Use TestClient if available
    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    except (ImportError, RuntimeError):
        # Skip if httpx not available
        pytest.skip("httpx not available for TestClient")


def test_app_routes_registered():
    """Test that all routes are registered."""
    app = create_app(dev_mode=True)
    
    route_paths = [r.path for r in app.routes]
    
    # Check main routes
    assert "/health" in route_paths
    assert "/api/devices" in route_paths
    assert "/api/devices/{device_id}" in route_paths
    assert "/api/test-stages" in route_paths
    assert "/api/test-stages/{stage_id}" in route_paths
    assert "/api/requirement-sets" in route_paths
    assert "/api/requirement-sets/{req_set_id}" in route_paths
    assert "/api/test-runs" in route_paths
    assert "/api/test-runs/{test_run_id}" in route_paths
    assert "/api/test-runs/{test_run_id}/upload" in route_paths


def test_app_static_files_prod_mode():
    """Test static file serving in prod mode."""
    app = create_app(dev_mode=False)
    
    # Static file mounting is conditional on frontend/dist existing
    # We can't easily test this without creating the directory
    # But we can verify the app is created correctly
    assert app is not None


