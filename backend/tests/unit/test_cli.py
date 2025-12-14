"""
Tests for CLI commands.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from backend.src.cli.main import (
    cmd_parse, cmd_load, cmd_compute, cmd_evaluate, cmd_plot,
    cmd_test_db, cmd_test_storage,
)


def test_cmd_parse(capsys):
    """Test parse command."""
    class Args:
        filename = "SN1234_PRI_L567890_AMB_20240101.s2p"
    
    result = cmd_parse(Args())
    assert result == 0
    captured = capsys.readouterr()
    assert "SN1234" in captured.out
    assert "PRI" in captured.out


def test_cmd_load_success(capsys, tmp_path):
    """Test load command with valid file."""
    # Create a minimal S2P file
    s2p_content = """! S2P file
# HZ S RI R 50.0
!freq Re(S11) Im(S11) Re(S21) Im(S21) Re(S12) Im(S12) Re(S22) Im(S22)
1.000000000E+09  0.1  0.0  0.5  0.0  0.5  0.0  0.1  0.0
"""
    test_file = tmp_path / "test.s2p"
    test_file.write_text(s2p_content)
    
    class Args:
        file_path = str(test_file)
    
    result = cmd_load(Args())
    assert result == 0
    captured = capsys.readouterr()
    assert "Successfully loaded" in captured.out


def test_cmd_load_not_found(capsys):
    """Test load command with non-existent file."""
    class Args:
        file_path = "/nonexistent/file.s2p"
    
    result = cmd_load(Args())
    assert result == 1
    captured = capsys.readouterr()
    assert "Error loading file" in captured.err


def test_cmd_compute(capsys, tmp_path):
    """Test compute command."""
    # Create S2P file
    s2p_content = """! S2P file
# HZ S RI R 50.0
!freq Re(S11) Im(S11) Re(S21) Im(S21) Re(S12) Im(S12) Re(S22) Im(S22)
1.000000000E+09  0.1  0.0  0.5  0.0  0.5  0.0  0.1  0.0
"""
    s2p_file = tmp_path / "test.s2p"
    s2p_file.write_text(s2p_content)
    
    # Create device config
    config = {
        "name": "Test Device",
        "s_parameter_config": {
            "operational_band_hz": {"start_hz": 0.9e9, "stop_hz": 1.1e9},
            "wideband_band_hz": {"start_hz": 0.5e9, "stop_hz": 2e9},
            "gain_parameter": "S21",
            "input_return_parameter": "S11",
        }
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    
    class Args:
        file_path = str(s2p_file)
        device_config = str(config_file)
        output = None
    
    result = cmd_compute(Args())
    assert result == 0
    captured = capsys.readouterr()
    assert "Computed metrics" in captured.out
    assert "Gain" in captured.out


def test_cmd_evaluate(capsys, tmp_path):
    """Test evaluate command."""
    # Create metrics JSON
    metrics = {
        "gain": [-5.0, -6.0, -7.0],
        "vswr": [1.2, 1.3, 1.4],
        "return_loss": [15.0, 14.0, 13.0],
        "frequencies": [1e9, 1.5e9, 2e9],
    }
    metrics_file = tmp_path / "metrics.json"
    metrics_file.write_text(json.dumps(metrics))
    
    # Create requirements JSON
    requirements = {
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
        "pass_policy": {"all_files_must_pass": True},
    }
    req_file = tmp_path / "requirements.json"
    req_file.write_text(json.dumps(requirements))
    
    class Args:
        metrics_json = str(metrics_file)
        requirements_json = str(req_file)
    
    result = cmd_evaluate(Args())
    assert result == 0  # Should pass
    captured = capsys.readouterr()
    assert "Compliance Evaluation" in captured.out
    assert "PASS" in captured.out


def test_cmd_plot(capsys, tmp_path):
    """Test plot command."""
    # Create plot spec - check actual PlotSpec schema
    import numpy as np
    spec = {
        "title": "Test Plot",
        "y_label": "Gain (dB)",
        "series": [
            {
                "frequency_hz": [1e9, 2e9],
                "values": [-5.0, -6.0],
                "label": "Gain",
                "trace_identity": "PRI",
            }
        ]
    }
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec))
    
    # Create plot config
    config = {
        "x_min": 0.9e9,
        "x_max": 2.1e9,
        "y_min": -10.0,
        "y_max": 0.0,
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    
    output_file = tmp_path / "plot.png"
    
    class Args:
        spec_json = str(spec_file)
        config_json = str(config_file)
        output = str(output_file)
    
    result = cmd_plot(Args())
    assert result == 0
    assert output_file.exists()
    captured = capsys.readouterr()
    assert "Plot saved" in captured.out


def test_cmd_test_db(capsys):
    """Test test-db command."""
    class Args:
        database_url = "sqlite:///:memory:"
    
    result = cmd_test_db(Args())
    assert result == 0
    captured = capsys.readouterr()
    assert "Database operations successful" in captured.out


def test_cmd_test_storage(capsys, tmp_path):
    """Test test-storage command."""
    class Args:
        storage_path = str(tmp_path)
    
    result = cmd_test_storage(Args())
    assert result == 0
    captured = capsys.readouterr()
    assert "File storage operations successful" in captured.out

