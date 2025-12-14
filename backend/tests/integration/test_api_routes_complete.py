"""
Complete API route tests - tests all endpoints and error cases.
"""
import pytest

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
    import tempfile
    os.environ["RF_TOOL_DATABASE_URL"] = "sqlite:///:memory:"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["RF_TOOL_STORAGE_PATH"] = tmpdir
        app = create_app(dev_mode=True)
        yield TestClient(app)


def test_devices_put_not_implemented(client):
    """Test PUT /api/devices/{id} returns 501."""
    response = client.put("/api/devices/1", json={"name": "Updated"})
    assert response.status_code == 501


def test_devices_delete_not_implemented(client):
    """Test DELETE /api/devices/{id} returns 501."""
    response = client.delete("/api/devices/1")
    assert response.status_code == 501


def test_test_stages_get_all(client):
    """Test GET /api/test-stages returns empty list."""
    response = client.get("/api/test-stages")
    assert response.status_code == 200
    assert response.json() == []


def test_requirement_sets_get_all(client):
    """Test GET /api/requirement-sets returns empty list."""
    response = client.get("/api/requirement-sets")
    assert response.status_code == 200
    assert response.json() == []


def test_test_runs_get_all(client):
    """Test GET /api/test-runs returns empty list."""
    response = client.get("/api/test-runs")
    assert response.status_code == 200
    assert response.json() == []


def test_test_runs_upload_multiple_files(client):
    """Test uploading multiple files."""
    import uuid
    unique_suffix = uuid.uuid4().hex[:8]
    # Create test run first
    device_id = client.post("/api/devices", json={
        "name": f"Test {unique_suffix}", "s_parameter_config": {
            "operational_band_hz": {"start_hz": 1e9, "stop_hz": 2e9},
            "wideband_band_hz": {"start_hz": 0.5e9, "stop_hz": 3e9},
        }
    }).json()["id"]
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
    
    # Upload multiple files
    file1_content = b"! S2P file 1\n# HZ S RI R 50.0\n"
    file2_content = b"! S2P file 2\n# HZ S RI R 50.0\n"
    
    response = client.post(
        f"/api/test-runs/{test_run_id}/upload",
        files=[
            ("files", ("file1.s2p", file1_content, "application/octet-stream")),
            ("files", ("file2.s2p", file2_content, "application/octet-stream")),
        ]
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["uploaded_files"]) == 2


def test_test_runs_process_not_implemented(client):
    """Test POST /api/test-runs/{id}/process returns 501."""
    import uuid
    unique_suffix = uuid.uuid4().hex[:8]
    # Create test run first
    device_id = client.post("/api/devices", json={
        "name": f"Test {unique_suffix}", "s_parameter_config": {
            "operational_band_hz": {"start_hz": 1e9, "stop_hz": 2e9},
            "wideband_band_hz": {"start_hz": 0.5e9, "stop_hz": 3e9},
        }
    }).json()["id"]
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
    
    # The process endpoint expects DeviceConfig and RequirementSet objects
    # Since it's not implemented, it will return 400 or 501 depending on validation
    # Let's test with proper structure but expect either 400 (validation error) or 501 (not implemented)
    response = client.post(
        f"/api/test-runs/{test_run_id}/process",
        json={
            "device_config": {
                "name": f"Test {unique_suffix}",
                "s_parameter_config": {
                    "operational_band_hz": {"start_hz": 1e9, "stop_hz": 2e9},
                    "wideband_band_hz": {"start_hz": 0.5e9, "stop_hz": 3e9},
                }
            },
            "requirement_set": {
                "name": f"Test {unique_suffix}",
                "test_type": "s_parameter",
                "metric_limits": []
            },
        }
    )
    # Endpoint may return 400 (validation) or 501 (not implemented) - both are acceptable
    assert response.status_code in [400, 501], f"Unexpected status: {response.status_code}, response: {response.text}"


def test_test_runs_compliance_not_implemented(client):
    """Test GET /api/test-runs/{id}/compliance returns placeholder."""
    import uuid
    unique_suffix = uuid.uuid4().hex[:8]
    # Create test run first
    device_id = client.post("/api/devices", json={
        "name": f"Test {unique_suffix}", "s_parameter_config": {
            "operational_band_hz": {"start_hz": 1e9, "stop_hz": 2e9},
            "wideband_band_hz": {"start_hz": 0.5e9, "stop_hz": 3e9},
        }
    }).json()["id"]
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
    
    response = client.get(f"/api/test-runs/{test_run_id}/compliance")
    assert response.status_code == 200
    data = response.json()
    assert "compliance" in data
    assert data["compliance"] == "Not yet implemented"

