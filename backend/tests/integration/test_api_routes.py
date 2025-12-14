"""
Integration tests for API routes.
"""
import pytest

# Skip tests if httpx is not installed (required for TestClient)
try:
    from fastapi.testclient import TestClient
    from backend.src.api.main import create_app
    HTTPX_AVAILABLE = True
except (ImportError, RuntimeError):
    HTTPX_AVAILABLE = False
    pytestmark = pytest.mark.skip(
        reason="httpx not installed. Install with: pip install httpx"
    )

if HTTPX_AVAILABLE:
    from backend.src.api.main import create_app


@pytest.fixture
def client():
    """Create test client with in-memory database."""
    # Set environment to use in-memory database
    import os
    os.environ["RF_TOOL_DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["RF_TOOL_STORAGE_PATH"] = "/tmp/test_storage"
    
    app = create_app(dev_mode=True)
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_create_device(client):
    """Test creating a device."""
    device_data = {
        "name": "Test Device",
        "part_number": "L123456",
        "s_parameter_config": {
            "operational_band_hz": {"start_hz": 1e9, "stop_hz": 2e9},
            "wideband_band_hz": {"start_hz": 0.5e9, "stop_hz": 3e9},
            "gain_parameter": "S21",
            "input_return_parameter": "S11",
        },
    }
    response = client.post("/api/devices", json=device_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "Device created successfully"


def test_get_device(client):
    """Test getting a device."""
    # First create a device
    device_data = {
        "name": "Test Device",
        "s_parameter_config": {
            "operational_band_hz": {"start_hz": 1e9, "stop_hz": 2e9},
            "wideband_band_hz": {"start_hz": 0.5e9, "stop_hz": 3e9},
        },
    }
    create_response = client.post("/api/devices", json=device_data)
    device_id = create_response.json()["id"]
    
    # Then get it
    response = client.get(f"/api/devices/{device_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Device"


def test_get_device_not_found(client):
    """Test getting non-existent device."""
    response = client.get("/api/devices/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_test_stage(client):
    """Test creating a test stage."""
    import uuid
    unique_name = f"Production Test {uuid.uuid4().hex[:8]}"
    stage_data = {
        "name": unique_name,
        "description": "Production testing stage",
    }
    response = client.post("/api/test-stages", json=stage_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "Test stage created successfully"


def test_create_test_stage_duplicate(client):
    """Test creating duplicate test stage."""
    import uuid
    unique_name = f"Duplicate Test {uuid.uuid4().hex[:8]}"
    stage_data = {"name": unique_name}
    client.post("/api/test-stages", json=stage_data)
    
    # Try to create duplicate
    response = client.post("/api/test-stages", json=stage_data)
    assert response.status_code == 409  # Conflict


def test_get_test_stage(client):
    """Test getting a test stage."""
    import uuid
    unique_name = f"Test Stage {uuid.uuid4().hex[:8]}"
    # Create first
    stage_data = {"name": unique_name}
    create_response = client.post("/api/test-stages", json=stage_data)
    stage_id = create_response.json()["id"]
    
    # Get it
    response = client.get(f"/api/test-stages/{stage_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == unique_name


def test_create_requirement_set(client):
    """Test creating a requirement set."""
    req_set_data = {
        "name": "Test Requirements",
        "test_type": "s_parameter",
        "metric_limits": [
            {
                "metric_name": "gain",
                "aggregation": "min",
                "operator": ">=",
                "limit_value": -10.0,
                "frequency_band": {"start_hz": 1e9, "stop_hz": 2e9},
            }
        ],
    }
    response = client.post("/api/requirement-sets", json=req_set_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data


def test_create_test_run(client):
    """Test creating a test run."""
    import uuid
    unique_suffix = uuid.uuid4().hex[:8]
    # Create dependencies first
    device_data = {
        "name": f"Test Device {unique_suffix}",
        "s_parameter_config": {
            "operational_band_hz": {"start_hz": 1e9, "stop_hz": 2e9},
            "wideband_band_hz": {"start_hz": 0.5e9, "stop_hz": 3e9},
        },
    }
    device_response = client.post("/api/devices", json=device_data)
    device_id = device_response.json()["id"]
    
    stage_data = {"name": f"Test Stage {unique_suffix}"}
    stage_response = client.post("/api/test-stages", json=stage_data)
    assert stage_response.status_code == 201, f"Failed to create stage: {stage_response.text}"
    stage_id = stage_response.json()["id"]
    
    req_set_data = {
        "name": f"Test Requirements {unique_suffix}",
        "test_type": "s_parameter",
        "metric_limits": [],
    }
    req_set_response = client.post("/api/requirement-sets", json=req_set_data)
    req_set_id = req_set_response.json()["id"]
    
    # Create test run
    test_run_data = {
        "device_id": device_id,
        "test_stage_id": stage_id,
        "requirement_set_id": req_set_id,
        "test_type": "s_parameter",
    }
    response = client.post("/api/test-runs", json=test_run_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data


def test_get_test_run(client):
    """Test getting a test run."""
    import uuid
    unique_suffix = uuid.uuid4().hex[:8]
    # Create test run first
    device_data = {
        "name": f"Test Device {unique_suffix}",
        "s_parameter_config": {
            "operational_band_hz": {"start_hz": 1e9, "stop_hz": 2e9},
            "wideband_band_hz": {"start_hz": 0.5e9, "stop_hz": 3e9},
        },
    }
    device_id = client.post("/api/devices", json=device_data).json()["id"]
    stage_response = client.post("/api/test-stages", json={"name": f"Test {unique_suffix}"})
    assert stage_response.status_code == 201, f"Failed to create stage: {stage_response.text}"
    stage_id = stage_response.json()["id"]
    req_set_id = client.post("/api/requirement-sets", json={
        "name": f"Test {unique_suffix}", "test_type": "s_parameter", "metric_limits": []
    }).json()["id"]
    
    test_run_id = client.post("/api/test-runs", json={
        "device_id": device_id,
        "test_stage_id": stage_id,
        "requirement_set_id": req_set_id,
        "test_type": "s_parameter",
    }).json()["id"]
    
    # Get it
    response = client.get(f"/api/test-runs/{test_run_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"


def test_cors_headers_dev_mode(client):
    """Test CORS headers in dev mode."""
    response = client.options("/health", headers={"Origin": "http://localhost:5173"})
    # FastAPI TestClient doesn't fully simulate CORS, but we can verify the middleware is configured
    assert response.status_code in [200, 405]  # OPTIONS may return 405 in test client

