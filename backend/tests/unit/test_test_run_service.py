"""
Tests for test run service.
"""
import pytest
from pathlib import Path
import numpy as np
import skrf as rf
from backend.src.services.test_run_service import TestRunService
from backend.src.storage.mock_storage import MockDatabase, MockFileStorage, MockStorageFactory
from backend.src.core.schemas.device import DeviceConfig, SParameterConfig, FrequencyBand
from backend.src.core.schemas.requirement_set import RequirementSet, MetricLimit, PassPolicy


def create_test_device_config() -> DeviceConfig:
    """Create a test device configuration."""
    return DeviceConfig(
        name="Test Device",
        s_parameter_config=SParameterConfig(
            operational_band_hz=FrequencyBand(start_hz=1e9, stop_hz=2e9),
            wideband_band_hz=FrequencyBand(start_hz=0.5e9, stop_hz=3e9),
            gain_parameter="S21",
            input_return_parameter="S11",
        ),
    )


def create_test_requirement_set() -> RequirementSet:
    """Create a test requirement set."""
    return RequirementSet(
        name="Test Requirements",
        test_type="s_parameter",
        metric_limits=[
            MetricLimit(
                metric_name="gain",
                aggregation="min",
                operator=">=",
                limit_value=-10.0,
                frequency_band=FrequencyBand(start_hz=1e9, stop_hz=2e9),
                description="Minimum gain",
            ),
        ],
    )


def create_test_s2p_file(temp_dir: Path) -> Path:
    """Create a test S2P file."""
    file_path = temp_dir / "test.s2p"
    content = """! Test S2P file
# HZ S RI R 50.0
!freq Re(S11) Im(S11) Re(S21) Im(S21) Re(S12) Im(S12) Re(S22) Im(S22)
1.000000000e+09    0.1    0.0    0.5    0.0    0.5    0.0    0.1    0.0
2.000000000e+09    0.1    0.0    0.5    0.0    0.5    0.0    0.1    0.0
"""
    file_path.write_text(content)
    return file_path


def test_service_initialization():
    """Test service initialization with dependencies."""
    db = MockDatabase()
    file_storage = MockFileStorage()
    service = TestRunService(db, file_storage)
    
    assert service.db is db
    assert service.file_storage is file_storage


def test_process_test_run_full_pipeline(temp_dir):
    """Test full pipeline with mocked storage."""
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
    
    # Create test file
    file_path = create_test_s2p_file(temp_dir)
    
    # Process test run
    device_config = create_test_device_config()
    requirement_set = create_test_requirement_set()
    
    service.process_test_run(
        test_run_id,
        [file_path],
        device_config,
        requirement_set,
    )
    
    # Verify test run status
    test_run = db.get_test_run(test_run_id)
    assert test_run["status"] == "completed"
    
    # Verify file was stored
    files = db.test_run_files[test_run_id]
    assert len(files) == 1
    file_id = list(files.keys())[0]
    
    # Verify metrics were stored
    assert test_run_id in db.metrics
    assert file_id in db.metrics[test_run_id]
    
    # Verify compliance was stored
    assert test_run_id in db.compliance
    assert file_id in db.compliance[test_run_id]


def test_process_test_run_error_handling(temp_dir):
    """Test error handling in pipeline."""
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
    
    # Use invalid file path
    invalid_path = temp_dir / "nonexistent.s2p"
    device_config = create_test_device_config()
    requirement_set = create_test_requirement_set()
    
    with pytest.raises(Exception):  # Should raise FileNotFoundError
        service.process_test_run(
            test_run_id,
            [invalid_path],
            device_config,
            requirement_set,
        )
    
    # Verify status is failed
    test_run = db.get_test_run(test_run_id)
    assert test_run["status"] == "failed"
    assert "error_message" in test_run


def test_process_test_run_immutability(temp_dir):
    """Test that completed test runs cannot be reprocessed."""
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
    
    file_path = create_test_s2p_file(temp_dir)
    device_config = create_test_device_config()
    requirement_set = create_test_requirement_set()
    
    # Process once
    service.process_test_run(
        test_run_id,
        [file_path],
        device_config,
        requirement_set,
    )
    
    # Try to process again - should fail due to immutability
    with pytest.raises(ValueError, match="Cannot update immutable"):
        service.process_test_run(
            test_run_id,
            [file_path],
            device_config,
            requirement_set,
        )


def test_process_test_run_multiple_files(temp_dir):
    """Test processing multiple files."""
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
    
    # Create two files
    file1 = create_test_s2p_file(temp_dir)
    file2 = temp_dir / "test2.s2p"
    file2.write_text(file1.read_text())  # Copy content
    
    device_config = create_test_device_config()
    requirement_set = create_test_requirement_set()
    
    service.process_test_run(
        test_run_id,
        [file1, file2],
        device_config,
        requirement_set,
    )
    
    # Verify both files were processed
    files = db.test_run_files[test_run_id]
    assert len(files) == 2

