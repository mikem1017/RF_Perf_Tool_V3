"""
Comprehensive API integration tests.

Tests the full API workflow: create resources, upload files, process test runs.
"""
import pytest
import tempfile
from pathlib import Path

# Skip tests if httpx is not installed
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
    import os
    os.environ["RF_TOOL_DATABASE_URL"] = "sqlite:///:memory:"
    
    # Use temporary directory for file storage
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["RF_TOOL_STORAGE_PATH"] = tmpdir
        app = create_app(dev_mode=True)
        yield TestClient(app)


def create_sample_s2p_file() -> bytes:
    """Create a sample S2P file content."""
    content = """! Sample S2P file
# HZ S RI R 50.0
!freq Re(S11) Im(S11) Re(S21) Im(S21) Re(S12) Im(S12) Re(S22) Im(S22)
1.000000000e+09    0.1    0.0    0.5    0.0    0.5    0.0    0.1    0.0
2.000000000e+09    0.1    0.0    0.4    0.0    0.4    0.0    0.1    0.0
"""
    return content.encode('utf-8')


def test_full_workflow(client):
    """Test complete workflow: create resources -> upload -> process."""
    import uuid
    unique_suffix = uuid.uuid4().hex[:8]
    # 1. Create device
    device_data = {
        "name": f"Test Device {unique_suffix}",
        "part_number": "L123456",
        "s_parameter_config": {
            "operational_band_hz": {"start_hz": 1e9, "stop_hz": 2e9},
            "wideband_band_hz": {"start_hz": 0.5e9, "stop_hz": 3e9},
            "gain_parameter": "S21",
            "input_return_parameter": "S11",
        },
    }
    device_response = client.post("/api/devices", json=device_data)
    assert device_response.status_code == 201
    device_id = device_response.json()["id"]
    
    # 2. Create test stage
    stage_response = client.post("/api/test-stages", json={"name": f"Production Test {unique_suffix}"})
    assert stage_response.status_code == 201, f"Failed to create stage: {stage_response.text}"
    stage_id = stage_response.json()["id"]
    
    # 3. Create requirement set
    req_set_data = {
        "name": f"Test Requirements {unique_suffix}",
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
    req_set_response = client.post("/api/requirement-sets", json=req_set_data)
    assert req_set_response.status_code == 201
    req_set_id = req_set_response.json()["id"]
    
    # 4. Create test run
    test_run_data = {
        "device_id": device_id,
        "test_stage_id": stage_id,
        "requirement_set_id": req_set_id,
        "test_type": "s_parameter",
    }
    test_run_response = client.post("/api/test-runs", json=test_run_data)
    assert test_run_response.status_code == 201
    test_run_id = test_run_response.json()["id"]
    
    # 5. Upload file
    file_content = create_sample_s2p_file()
    upload_response = client.post(
        f"/api/test-runs/{test_run_id}/upload",
        files={"files": ("SN1234_PRI_L567890_AMB_20240101.s2p", file_content, "application/octet-stream")}
    )
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert len(upload_data["uploaded_files"]) == 1
    
    # 6. Get test run status
    get_response = client.get(f"/api/test-runs/{test_run_id}")
    assert get_response.status_code == 200
    test_run = get_response.json()
    assert test_run["status"] == "created"
    assert test_run["device_id"] == device_id


def test_api_error_handling(client):
    """Test API error handling."""
    import uuid
    unique_suffix = uuid.uuid4().hex[:8]
    # Test 404 for non-existent resource
    response = client.get("/api/devices/999")
    assert response.status_code == 404
    
    # Test 409 for duplicate test stage
    duplicate_name = f"Duplicate Test {unique_suffix}"
    client.post("/api/test-stages", json={"name": duplicate_name})
    response = client.post("/api/test-stages", json={"name": duplicate_name})
    assert response.status_code == 409
    
    # Test 400 for invalid data
    response = client.post("/api/devices", json={"invalid": "data"})
    assert response.status_code == 400 or response.status_code == 422  # 422 for validation error


def test_api_list_endpoints(client):
    """Test list endpoints return empty arrays (placeholder)."""
    # These endpoints are placeholders that return empty arrays
    devices = client.get("/api/devices")
    assert devices.status_code == 200
    assert devices.json() == []
    
    stages = client.get("/api/test-stages")
    assert stages.status_code == 200
    assert stages.json() == []
    
    req_sets = client.get("/api/requirement-sets")
    assert req_sets.status_code == 200
    assert req_sets.json() == []
    
    test_runs = client.get("/api/test-runs")
    assert test_runs.status_code == 200
    assert test_runs.json() == []

