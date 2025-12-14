"""
End-to-end tests for the full RF analysis pipeline.

Tests the complete workflow:
1. Create device -> Create requirement set -> Create test run
2. Upload S-parameter files
3. Process test run (parse, load, compute metrics, evaluate compliance)
4. Verify results (metrics, compliance, plots)
"""
import pytest
import tempfile
import shutil
import numpy as np
import skrf as rf
from pathlib import Path
from typing import Dict

from backend.src.storage.storage_service import StorageService
from backend.src.services.test_run_service import TestRunService
from backend.src.core.schemas.device import DeviceConfig
from backend.src.core.schemas.requirement_set import RequirementSet


@pytest.fixture
def temp_storage():
    """Create temporary storage for E2E tests."""
    temp_path = Path(tempfile.mkdtemp())
    db_url = f"sqlite:///{temp_path / 'test.db'}"
    storage_service = StorageService(
        database_url=db_url,
        file_storage_path=temp_path / "files"
    )
    yield storage_service
    
    # Cleanup with retry for Windows file locking
    try:
        # Close any database connections
        if hasattr(storage_service, 'engine'):
            storage_service.engine.dispose()
        
        # Try to remove the directory
        import time
        max_retries = 3
        for i in range(max_retries):
            try:
                shutil.rmtree(temp_path)
                break
            except PermissionError:
                if i < max_retries - 1:
                    time.sleep(0.1)
                else:
                    # On Windows, database may still be locked - just warn
                    import warnings
                    warnings.warn(f"Could not clean up temp directory: {temp_path}")
    except Exception as e:
        import warnings
        warnings.warn(f"Error during cleanup: {e}")


@pytest.fixture
def sample_s2p_file(temp_storage):
    """Create a sample S2P file programmatically."""
    # Create temporary file
    temp_file = temp_storage.file_storage_path.parent / "sample_SN1234_PRI_L567890_AMB_20240101.s2p"
    
    # Generate S-parameter data
    freq = rf.Frequency(0.5e9, 3e9, 201, unit='Hz')
    n_points = len(freq)
    s = np.zeros((n_points, 2, 2), dtype=complex)
    
    for i, f in enumerate(freq.f):
        # S11: Input return loss ~15 dB
        s11_mag = 10**(-15/20)
        s[i, 0, 0] = s11_mag * np.exp(1j * np.pi * f / freq.f[-1])
        
        # S21: Forward gain ~10 dB
        s21_mag = 10**(10/20)
        s[i, 1, 0] = s21_mag * np.exp(-1j * np.pi * f / freq.f[-1] * 0.5)
        
        # S12: Reverse isolation ~40 dB
        s12_mag = 10**(-40/20)
        s[i, 0, 1] = s12_mag * np.exp(1j * np.pi * f / freq.f[-1] * 0.3)
        
        # S22: Output return loss ~12 dB
        s22_mag = 10**(-12/20)
        s[i, 1, 1] = s22_mag * np.exp(1j * np.pi * f / freq.f[-1] * 0.7)
    
    network = rf.Network(frequency=freq, s=s)
    network.write_touchstone(str(temp_file))
    
    yield temp_file
    
    # Cleanup
    if temp_file.exists():
        temp_file.unlink()


@pytest.fixture
def test_device(temp_storage):
    """Create a test device."""
    db = temp_storage.create_database()
    
    device_data = {
        "name": "2-Port RF Amplifier",
        "description": "Test amplifier for E2E testing",
        "part_number": "L567890",
        "s_parameter_config": {
            "operational_band_hz": {
                "start_hz": 1e9,
                "stop_hz": 2e9
            },
            "wideband_band_hz": {
                "start_hz": 0.5e9,
                "stop_hz": 3e9
            },
            "gain_parameter": "S21",
            "input_return_parameter": "S11",
            "output_return_parameter": "S22"
        }
    }
    
    device_id = db.create_device(device_data)
    return device_id


@pytest.fixture
def test_stage(temp_storage):
    """Create a test stage."""
    db = temp_storage.create_database()
    
    stage_data = {
        "name": "Production Test",
        "description": "Production testing stage"
    }
    
    stage_id = db.create_test_stage(stage_data)
    return stage_id


@pytest.fixture
def test_requirement_set(temp_storage, test_stage):
    """Create a test requirement set."""
    db = temp_storage.create_database()
    
    # Import to compute hash
    from backend.src.core.schemas.requirement_set import RequirementSet as RequirementSetSchema
    
    req_set_schema = RequirementSetSchema(
        name="Operational Band Requirements",
        test_type="s_parameter",
        metric_limits=[
            {
                "metric_name": "gain",
                "aggregation": "min",
                "operator": ">=",
                "limit_value": -10.0,
                "frequency_band": {
                    "start_hz": 1e9,
                    "stop_hz": 2e9
                },
                "description": "Minimum gain in operational band"
            },
            {
                "metric_name": "vswr",
                "aggregation": "max",
                "operator": "<=",
                "limit_value": 2.0,
                "frequency_band": {
                    "start_hz": 1e9,
                    "stop_hz": 2e9
                },
                "description": "Maximum VSWR in operational band"
            },
            {
                "metric_name": "return_loss",
                "aggregation": "min",
                "operator": ">=",
                "limit_value": 10.0,
                "frequency_band": {
                    "start_hz": 1e9,
                    "stop_hz": 2e9
                },
                "description": "Minimum return loss in operational band"
            }
        ],
        pass_policy={
            "all_files_must_pass": True,
            "required_paths": ["PRI"]
        }
    )
    
    # Compute hash for database
    req_hash = req_set_schema.compute_hash()
    
    req_set_data = {
        "name": req_set_schema.name,
        "test_type": req_set_schema.test_type,
        "metric_limits": [m.model_dump() for m in req_set_schema.metric_limits],
        "pass_policy": req_set_schema.pass_policy.model_dump(),
        "requirement_hash": req_hash
    }
    
    req_set_id = db.create_requirement_set(req_set_data)
    return req_set_id


def test_full_pipeline_workflow(
    temp_storage,
    sample_s2p_file,
    test_device,
    test_stage,
    test_requirement_set
):
    """Test the complete pipeline: create -> upload -> process -> verify."""
    db = temp_storage.create_database()
    file_storage = temp_storage.create_file_storage()
    service = TestRunService(db, file_storage)
    
    # 1. Create test run
    test_run_data = {
        "device_id": test_device,
        "test_stage_id": test_stage,
        "requirement_set_id": test_requirement_set,
        "test_type": "s_parameter"
    }
    test_run_id = db.create_test_run(test_run_data)
    
    # Verify test run was created
    test_run = db.get_test_run(test_run_id)
    assert test_run is not None
    assert test_run["status"] in ["pending", "created"]  # Allow both as initial status
    
    # 2. Get device and requirement set configs
    device = db.get_device(test_device)
    req_set = db.get_requirement_set(test_requirement_set)
    
    device_config = DeviceConfig(**device)
    requirement_set = RequirementSet(**req_set)
    
    # 3. Process test run
    service.process_test_run(
        test_run_id=test_run_id,
        file_paths=[sample_s2p_file],
        device_config=device_config,
        requirement_set=requirement_set
    )
    
    # 4. Verify test run status
    test_run = db.get_test_run(test_run_id)
    assert test_run["status"] == "completed"
    
    # 5. Verify file was stored
    files = db.get_test_run_files(test_run_id)
    assert len(files) == 1
    file_record = files[0]
    assert "SN1234" in file_record["original_filename"]
    assert file_record["effective_metadata"]["serial_number"] == "SN1234"
    assert file_record["effective_metadata"]["path"] == "PRI"
    assert file_record["effective_metadata"]["part_number"] == "L567890"
    
    # 6. Verify metrics were computed and stored
    metrics = db.get_test_run_metrics(test_run_id, file_record["id"])
    assert metrics is not None
    assert "metrics" in metrics
    assert "frequencies" in metrics
    
    metric_data = metrics["metrics"]
    assert "gain" in metric_data
    assert "vswr" in metric_data
    assert "return_loss" in metric_data
    
    # Verify gain values are reasonable (should be ~10 dB = ~3.16 linear)
    gain_values = metric_data["gain"]
    assert len(gain_values) > 0
    # Gain should be positive (in dB, around 10 dB)
    assert max(gain_values) > 0
    
    # 7. Verify compliance was evaluated
    compliance = db.get_test_run_compliance(test_run_id, file_record["id"])
    assert compliance is not None
    assert "overall_pass" in compliance
    assert "requirements" in compliance
    
    # With our test data (gain ~10 dB, VSWR ~1.5, return_loss ~15 dB),
    # all requirements should pass
    assert compliance["overall_pass"] is True


def test_s_parameter_analysis_pipeline(
    temp_storage,
    sample_s2p_file,
    test_device,
    test_stage,
    test_requirement_set
):
    """Test the full S-parameter analysis pipeline."""
    db = temp_storage.create_database()
    file_storage = temp_storage.create_file_storage()
    service = TestRunService(db, file_storage)
    
    # Create test run
    test_run_id = db.create_test_run({
        "device_id": test_device,
        "test_stage_id": test_stage,
        "requirement_set_id": test_requirement_set,
        "test_type": "s_parameter"
    })
    
    # Get configs
    device = db.get_device(test_device)
    req_set = db.get_requirement_set(test_requirement_set)
    device_config = DeviceConfig(**device)
    requirement_set = RequirementSet(**req_set)
    
    # Process
    service.process_test_run(
        test_run_id=test_run_id,
        file_paths=[sample_s2p_file],
        device_config=device_config,
        requirement_set=requirement_set
    )
    
    # Verify analysis results
    test_run = db.get_test_run(test_run_id)
    assert test_run["status"] == "completed"
    
    files = db.get_test_run_files(test_run_id)
    assert len(files) == 1
    
    file_record = files[0]
    metrics = db.get_test_run_metrics(test_run_id, file_record["id"])
    
    # Verify all expected metrics are present
    metric_names = ["gain", "vswr", "return_loss", "gain_flatness_operational", "gain_flatness_wideband"]
    for metric_name in metric_names:
        assert metric_name in metrics["metrics"], f"Missing metric: {metric_name}"
    
    # Verify frequency data
    frequencies = metrics["frequencies"]
    assert len(frequencies) == 201  # Should match our generated data
    assert min(frequencies) >= 0.5e9
    assert max(frequencies) <= 3e9


def test_compliance_evaluation(
    temp_storage,
    sample_s2p_file,
    test_device,
    test_stage,
    test_requirement_set
):
    """Test compliance evaluation with requirement sets."""
    db = temp_storage.create_database()
    file_storage = temp_storage.create_file_storage()
    service = TestRunService(db, file_storage)
    
    # Create test run
    test_run_id = db.create_test_run({
        "device_id": test_device,
        "test_stage_id": test_stage,
        "requirement_set_id": test_requirement_set,
        "test_type": "s_parameter"
    })
    
    # Get configs
    device = db.get_device(test_device)
    req_set = db.get_requirement_set(test_requirement_set)
    device_config = DeviceConfig(**device)
    requirement_set = RequirementSet(**req_set)
    
    # Process
    service.process_test_run(
        test_run_id=test_run_id,
        file_paths=[sample_s2p_file],
        device_config=device_config,
        requirement_set=requirement_set
    )
    
    # Verify compliance
    files = db.get_test_run_files(test_run_id)
    file_record = files[0]
    
    compliance = db.get_test_run_compliance(test_run_id, file_record["id"])
    
    # Check compliance structure
    assert compliance["overall_pass"] is not None
    assert isinstance(compliance["overall_pass"], bool)
    assert "requirements" in compliance
    assert isinstance(compliance["requirements"], list)
    
    # With our test data, compliance should pass
    # (gain ~10 dB >= -10 dB, VSWR ~1.5 <= 2.0, return_loss ~15 dB >= 10 dB)
    assert compliance["overall_pass"] is True
    
    # Verify individual requirement results
    assert len(compliance["requirements"]) > 0
    for req_result in compliance["requirements"]:
        assert "metric_name" in req_result
        assert "pass" in req_result
        assert isinstance(req_result["pass"], bool)


def test_multiple_files_processing(
    temp_storage,
    test_device,
    test_stage,
    test_requirement_set
):
    """Test processing multiple S-parameter files."""
    db = temp_storage.create_database()
    file_storage = temp_storage.create_file_storage()
    service = TestRunService(db, file_storage)
    
    # Create two S-parameter files (PRI and RED paths)
    temp_path = temp_storage.file_storage_path.parent
    
    # PRI file
    pri_file = temp_path / "SN1234_PRI_L567890_AMB_20240101.s2p"
    freq = rf.Frequency(0.5e9, 3e9, 201, unit='Hz')
    n_points = len(freq)
    s_pri = np.zeros((n_points, 2, 2), dtype=complex)
    for i, f in enumerate(freq.f):
        s_pri[i, 0, 0] = 10**(-15/20) * np.exp(1j * np.pi * f / freq.f[-1])
        s_pri[i, 1, 0] = 10**(10/20) * np.exp(-1j * np.pi * f / freq.f[-1] * 0.5)
        s_pri[i, 0, 1] = 10**(-40/20) * np.exp(1j * np.pi * f / freq.f[-1] * 0.3)
        s_pri[i, 1, 1] = 10**(-12/20) * np.exp(1j * np.pi * f / freq.f[-1] * 0.7)
    network_pri = rf.Network(frequency=freq, s=s_pri)
    network_pri.write_touchstone(str(pri_file))
    
    # RED file (slightly different)
    red_file = temp_path / "SN1234_RED_L567890_AMB_20240101.s2p"
    s_red = s_pri.copy()
    s_red[:, 1, 0] *= 0.95  # Slightly lower gain
    network_red = rf.Network(frequency=freq, s=s_red)
    network_red.write_touchstone(str(red_file))
    
    try:
        # Create test run
        test_run_id = db.create_test_run({
            "device_id": test_device,
            "test_stage_id": test_stage,
            "requirement_set_id": test_requirement_set,
            "test_type": "s_parameter"
        })
        
        # Get configs
        device = db.get_device(test_device)
        req_set = db.get_requirement_set(test_requirement_set)
        device_config = DeviceConfig(**device)
        requirement_set = RequirementSet(**req_set)
        
        # Process both files
        service.process_test_run(
            test_run_id=test_run_id,
            file_paths=[pri_file, red_file],
            device_config=device_config,
            requirement_set=requirement_set
        )
        
        # Verify both files were processed
        files = db.get_test_run_files(test_run_id)
        assert len(files) == 2
        
        # Verify both have metrics and compliance
        for file_record in files:
            metrics = db.get_test_run_metrics(test_run_id, file_record["id"])
            assert metrics is not None
            
            compliance = db.get_test_run_compliance(test_run_id, file_record["id"])
            assert compliance is not None
            
            # Verify path metadata
            assert file_record["effective_metadata"]["path"] in ["PRI", "RED"]
    
    finally:
        # Cleanup
        if pri_file.exists():
            pri_file.unlink()
        if red_file.exists():
            red_file.unlink()


def test_test_run_failure_handling(
    temp_storage,
    test_device,
    test_stage,
    test_requirement_set
):
    """Test that test run failures are handled correctly."""
    db = temp_storage.create_database()
    file_storage = temp_storage.create_file_storage()
    service = TestRunService(db, file_storage)
    
    # Create test run
    test_run_id = db.create_test_run({
        "device_id": test_device,
        "test_stage_id": test_stage,
        "requirement_set_id": test_requirement_set,
        "test_type": "s_parameter"
    })
    
    # Get configs
    device = db.get_device(test_device)
    req_set = db.get_requirement_set(test_requirement_set)
    device_config = DeviceConfig(**device)
    requirement_set = RequirementSet(**req_set)
    
    # Try to process a non-existent file
    non_existent_file = Path("/nonexistent/file.s2p")
    
    with pytest.raises(Exception):
        service.process_test_run(
            test_run_id=test_run_id,
            file_paths=[non_existent_file],
            device_config=device_config,
            requirement_set=requirement_set
        )
    
    # Verify test run status is set to failed
    test_run = db.get_test_run(test_run_id)
    assert test_run["status"] == "failed"
    assert test_run.get("error_message") is not None


def test_plot_generation_and_retrieval(
    temp_storage,
    sample_s2p_file,
    test_device,
    test_stage,
    test_requirement_set
):
    """Test plot generation and retrieval."""
    from backend.src.plugins.s_parameter.plotting import render_plot
    from backend.src.core.schemas.plotting import PlotSpec, PlotSeries, PlotConfig
    
    db = temp_storage.create_database()
    file_storage = temp_storage.create_file_storage()
    service = TestRunService(db, file_storage)
    
    # Create and process test run
    test_run_id = db.create_test_run({
        "device_id": test_device,
        "test_stage_id": test_stage,
        "requirement_set_id": test_requirement_set,
        "test_type": "s_parameter"
    })
    
    device = db.get_device(test_device)
    req_set = db.get_requirement_set(test_requirement_set)
    device_config = DeviceConfig(**device)
    requirement_set = RequirementSet(**req_set)
    
    service.process_test_run(
        test_run_id=test_run_id,
        file_paths=[sample_s2p_file],
        device_config=device_config,
        requirement_set=requirement_set
    )
    
    # Get metrics for plotting
    files = db.get_test_run_files(test_run_id)
    file_record = files[0]
    metrics = db.get_test_run_metrics(test_run_id, file_record["id"])
    
    frequencies = metrics["frequencies"]
    gain_values = metrics["metrics"]["gain"]
    
    # Create plot specification
    plot_spec = PlotSpec(
        title="Gain vs Frequency",
        x_label="Frequency",
        x_unit="GHz",
        y_label="Gain (dB)",
        series=[
            PlotSeries(
                frequency_hz=frequencies,
                values=gain_values,
                label="Gain (S21)",
                trace_identity="PRI"
            )
        ]
    )
    
    # Create plot configuration
    plot_config = PlotConfig(
        figure_width=10,
        figure_height=6,
        dpi=100,
        line_style_pri="solid",
        line_style_red="dashed",
        color_pri="blue",
        color_red="red"
    )
    
    # Generate plot
    artifact_dir = file_storage.create_artifact_directory(test_run_id, file_record["id"])
    plot_path = artifact_dir / "gain_plot.png"
    
    rendered_path = render_plot(plot_spec, plot_config, plot_path)
    
    # Verify plot was created
    assert rendered_path.exists()
    assert rendered_path.suffix == ".png"
    assert rendered_path.stat().st_size > 0  # File is not empty
    
    # Store plot artifact
    stored_artifact_path = file_storage.store_artifact(
        test_run_id, file_record["id"], "gain_plot.png", plot_path.read_bytes()
    )
    
    # Verify artifact can be retrieved
    retrieved_path = file_storage.get_artifact_path(test_run_id, file_record["id"], "gain_plot.png")
    assert retrieved_path.exists()
    assert retrieved_path == stored_artifact_path
