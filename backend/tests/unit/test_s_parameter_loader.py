"""
Tests for S-parameter file loader.
"""
import pytest
import numpy as np
from pathlib import Path
from backend.src.plugins.s_parameter.loader import load_s_parameter_file


def create_sample_s2p_file(temp_dir: Path, filename: str = "test.s2p") -> Path:
    """Create a minimal valid S2P file for testing."""
    file_path = temp_dir / filename
    # Create a minimal Touchstone S2P file
    # Format: ! Comment line
    # # HZ S RI R 50.0
    # !freq Re(S11) Im(S11) Re(S21) Im(S21) Re(S12) Im(S12) Re(S22) Im(S22)
    content = """! Sample S2P file
# HZ S RI R 50.0
!freq Re(S11) Im(S11) Re(S21) Im(S21) Re(S12) Im(S12) Re(S22) Im(S22)
1.000000000e+09    0.1    0.0    0.9    0.0    0.9    0.0    0.1    0.0
2.000000000e+09    0.1    0.0    0.8    0.0    0.8    0.0    0.1    0.0
"""
    file_path.write_text(content)
    return file_path


def test_load_s2p_file(temp_dir):
    """Test loading an S2P file."""
    file_path = create_sample_s2p_file(temp_dir, "test.s2p")
    network = load_s_parameter_file(file_path)
    
    assert network is not None
    assert network.nports == 2
    assert len(network.f) > 0  # Has frequency points


def test_load_s2p_file_not_found(temp_dir):
    """Test error handling for non-existent file."""
    file_path = temp_dir / "nonexistent.s2p"
    with pytest.raises(FileNotFoundError, match="not found"):
        load_s_parameter_file(file_path)


def test_load_s2p_file_invalid_extension(temp_dir):
    """Test error handling for invalid file extension."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("not an s-parameter file")
    
    with pytest.raises(ValueError, match="Unsupported S-parameter file format"):
        load_s_parameter_file(file_path)


def test_load_s2p_file_invalid_content(temp_dir):
    """Test error handling for invalid file content."""
    file_path = temp_dir / "invalid.s2p"
    file_path.write_text("This is not a valid S2P file")
    
    with pytest.raises(ValueError, match="Failed to load"):
        load_s_parameter_file(file_path)


def test_load_s2p_file_path_object(temp_dir):
    """Test that Path objects are accepted."""
    file_path = create_sample_s2p_file(temp_dir, "test.s2p")
    network = load_s_parameter_file(Path(file_path))
    
    assert network is not None
    assert network.nports == 2


def test_load_s2p_file_network_properties(temp_dir):
    """Test that loaded network has expected properties."""
    file_path = create_sample_s2p_file(temp_dir, "test.s2p")
    network = load_s_parameter_file(file_path)
    
    # Check that network has S-parameters
    assert hasattr(network, 's')
    assert network.s.shape[0] == 2  # 2 frequency points
    assert network.s.shape[1] == 2  # 2 ports
    assert network.s.shape[2] == 2  # 2 ports
    
    # Check frequency array
    assert len(network.f) == 2
    assert network.f[0] == 1e9
    assert network.f[1] == 2e9

