"""
Phase 1 integration test - verifies all components work together.

This test exercises the full Phase 1 pipeline without any storage or API dependencies.
"""
import pytest
from pathlib import Path
import numpy as np
from backend.src.storage.mock_storage import MockStorageFactory
from backend.src.services.test_run_service import TestRunService
from backend.src.plugins.s_parameter.parser import parse_filename_metadata
from backend.src.plugins.s_parameter.loader import load_s_parameter_file
from backend.src.plugins.s_parameter.metrics import (
    compute_gain_db,
    compute_vswr,
    compute_return_loss_db,
)
from backend.src.plugins.s_parameter.compliance import evaluate_compliance
from backend.src.core.schemas.device import DeviceConfig, SParameterConfig, FrequencyBand
from backend.src.core.schemas.requirement_set import RequirementSet, MetricLimit


def create_realistic_s2p_file(temp_dir: Path, filename: str) -> Path:
    """Create a realistic S2P file for integration testing."""
    file_path = temp_dir / filename
    content = """! Touchstone file generated for testing
# HZ S RI R 50.0
!freq Re(S11) Im(S11) Re(S21) Im(S21) Re(S12) Im(S12) Re(S22) Im(S22)
1.000000000e+09    0.1    0.0    0.5    0.0    0.5    0.0    0.1    0.0
1.500000000e+09    0.1    0.0    0.48   0.0    0.48   0.0    0.1    0.0
2.000000000e+09    0.1    0.0    0.45   0.0    0.45   0.0    0.1    0.0
"""
    file_path.write_text(content)
    return file_path


def test_phase1_full_pipeline_integration(temp_dir):
    """
    Integration test: Full Phase 1 pipeline from filename to compliance.
    
    This test verifies that all Phase 1 components work together:
    1. Filename parsing
    2. File loading
    3. Metrics computation
    4. Compliance evaluation
    5. Service orchestration
    """
    # Setup
    factory = MockStorageFactory(temp_dir)
    db = factory.create_database()
    file_storage = factory.create_file_storage()
    service = TestRunService(db, file_storage)
    
    # Create test run
    test_run_id = db.create_test_run({
        "device_id": 1,
        "test_stage_id": 1,
        "requirement_set_id": 1,
        "test_type": "s_parameter",
    })
    
    # Create test file with metadata in filename
    filename = "SN1234_PRI_L567890_AMB_20240101.s2p"
    file_path = create_realistic_s2p_file(temp_dir, filename)
    
    # Create device config
    device_config = DeviceConfig(
        name="Test Device",
        s_parameter_config=SParameterConfig(
            operational_band_hz=FrequencyBand(start_hz=1e9, stop_hz=2e9),
            wideband_band_hz=FrequencyBand(start_hz=0.5e9, stop_hz=3e9),
            gain_parameter="S21",
            input_return_parameter="S11",
        ),
    )
    
    # Create requirement set
    requirement_set = RequirementSet(
        name="Test Requirements",
        test_type="s_parameter",
        metric_limits=[
            MetricLimit(
                metric_name="gain",
                aggregation="min",
                operator=">=",
                limit_value=-10.0,  # Should pass (gain will be ~-6 dB)
                frequency_band=FrequencyBand(start_hz=1e9, stop_hz=2e9),
                description="Minimum gain",
            ),
            MetricLimit(
                metric_name="vswr",
                aggregation="max",
                operator="<=",
                limit_value=2.0,  # Should pass (VSWR will be ~1.22)
                frequency_band=FrequencyBand(start_hz=1e9, stop_hz=2e9),
                description="Maximum VSWR",
            ),
        ],
    )
    
    # Execute full pipeline
    service.process_test_run(
        test_run_id,
        [file_path],
        device_config,
        requirement_set,
    )
    
    # Verify results
    test_run = db.get_test_run(test_run_id)
    assert test_run["status"] == "completed"
    
    # Verify file was processed
    files = db.test_run_files[test_run_id]
    assert len(files) == 1
    file_id = list(files.keys())[0]
    file_data = files[file_id]
    
    # Verify metadata was parsed
    effective_metadata = file_data["effective_metadata"]
    assert effective_metadata["serial_number"] == "SN1234"
    assert effective_metadata["path"] == "PRI"
    assert effective_metadata["part_number"] == "L567890"
    assert effective_metadata["temperature"] == "AMB"
    
    # Verify metrics were computed and stored
    assert test_run_id in db.metrics
    assert file_id in db.metrics[test_run_id]
    metrics_data = db.metrics[test_run_id][file_id]
    assert "metrics" in metrics_data
    assert "gain" in metrics_data["metrics"]
    assert "vswr" in metrics_data["metrics"]
    
    # Verify compliance was evaluated and stored
    assert test_run_id in db.compliance
    assert file_id in db.compliance[test_run_id]
    compliance_data = db.compliance[test_run_id][file_id]
    assert compliance_data["overall_pass"] is True
    assert len(compliance_data["requirements"]) == 2
    assert all(r["passed"] for r in compliance_data["requirements"])


def test_phase1_components_individually(temp_dir):
    """Test that each Phase 1 component works independently."""
    # 1. Filename parsing
    filename = "SN1234_PRI_L567890_AMB_20240101.s2p"
    parsed = parse_filename_metadata(filename)
    assert parsed.serial_number == "SN1234"
    assert parsed.path == "PRI"
    
    # 2. File loading
    file_path = create_realistic_s2p_file(temp_dir, filename)
    network = load_s_parameter_file(file_path)
    assert network.nports == 2
    assert len(network.f) == 3
    
    # 3. Metrics computation
    gain = compute_gain_db(network, "S21")
    vswr = compute_vswr(network, "S11")
    return_loss = compute_return_loss_db(network, "S11")
    
    assert len(gain) == 3
    assert len(vswr) == 3
    assert len(return_loss) == 3
    
    # 4. Compliance evaluation
    metrics = {
        "gain": gain,
        "vswr": vswr,
    }
    requirement_set = RequirementSet(
        name="Test",
        test_type="s_parameter",
        metric_limits=[
            MetricLimit(
                metric_name="gain",
                aggregation="min",
                operator=">=",
                limit_value=-10.0,
                frequency_band=FrequencyBand(start_hz=1e9, stop_hz=2e9),
            ),
        ],
    )
    compliance = evaluate_compliance(metrics, network.f, requirement_set)
    assert compliance.overall_pass is True


def test_phase1_error_propagation(temp_dir):
    """Test that errors propagate correctly through the pipeline."""
    factory = MockStorageFactory(temp_dir)
    db = factory.create_database()
    file_storage = factory.create_file_storage()
    service = TestRunService(db, file_storage)
    
    test_run_id = db.create_test_run({
        "device_id": 1,
        "test_stage_id": 1,
        "requirement_set_id": 1,
        "test_type": "s_parameter",
    })
    
    # Use non-existent file
    invalid_path = temp_dir / "nonexistent.s2p"
    device_config = DeviceConfig(
        name="Test",
        s_parameter_config=SParameterConfig(
            operational_band_hz=FrequencyBand(start_hz=1e9, stop_hz=2e9),
            wideband_band_hz=FrequencyBand(start_hz=0.5e9, stop_hz=3e9),
        ),
    )
    requirement_set = RequirementSet(
        name="Test",
        test_type="s_parameter",
        metric_limits=[],
    )
    
    with pytest.raises(FileNotFoundError):
        service.process_test_run(
            test_run_id,
            [invalid_path],
            device_config,
            requirement_set,
        )
    
    # Verify error was captured
    test_run = db.get_test_run(test_run_id)
    assert test_run["status"] == "failed"
    assert "error_message" in test_run

