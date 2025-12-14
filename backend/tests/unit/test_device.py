"""
Tests for device schemas.
"""
import pytest
from backend.src.core.schemas.device import (
    Device,
    DeviceConfig,
    SParameterConfig,
    FrequencyBand,
)


def test_frequency_band_creation():
    """Test creating FrequencyBand."""
    band = FrequencyBand(start_hz=1e9, stop_hz=2e9)
    assert band.start_hz == 1e9
    assert band.stop_hz == 2e9


def test_frequency_band_validation_stop_greater_than_start():
    """Test that stop_hz must be greater than start_hz."""
    with pytest.raises(ValueError, match="stop_hz must be greater than start_hz"):
        FrequencyBand(start_hz=2e9, stop_hz=1e9)


def test_frequency_band_validation_positive():
    """Test that frequencies must be positive."""
    with pytest.raises(ValueError):
        FrequencyBand(start_hz=-1e9, stop_hz=2e9)


def test_s_parameter_config_defaults():
    """Test SParameterConfig with defaults."""
    config = SParameterConfig(
        operational_band_hz=FrequencyBand(start_hz=1e9, stop_hz=2e9),
        wideband_band_hz=FrequencyBand(start_hz=0.5e9, stop_hz=3e9),
    )
    assert config.gain_parameter == "S21"
    assert config.input_return_parameter == "S11"
    assert config.output_return_parameter == "S22"


def test_s_parameter_config_validation_format():
    """Test S-parameter format validation."""
    # Valid formats
    config = SParameterConfig(
        operational_band_hz=FrequencyBand(start_hz=1e9, stop_hz=2e9),
        wideband_band_hz=FrequencyBand(start_hz=0.5e9, stop_hz=3e9),
        gain_parameter="S31",
        input_return_parameter="S11",
    )
    assert config.gain_parameter == "S31"

    # Invalid format - doesn't start with S
    with pytest.raises(ValueError, match="must start with 'S'"):
        SParameterConfig(
            operational_band_hz=FrequencyBand(start_hz=1e9, stop_hz=2e9),
            wideband_band_hz=FrequencyBand(start_hz=0.5e9, stop_hz=3e9),
            gain_parameter="X21",
        )

    # Invalid format - wrong length
    with pytest.raises(ValueError, match="Invalid S-parameter format"):
        SParameterConfig(
            operational_band_hz=FrequencyBand(start_hz=1e9, stop_hz=2e9),
            wideband_band_hz=FrequencyBand(start_hz=0.5e9, stop_hz=3e9),
            gain_parameter="S211",
        )


def test_s_parameter_config_validate_against_port_count():
    """Test validation against port count."""
    config = SParameterConfig(
        operational_band_hz=FrequencyBand(start_hz=1e9, stop_hz=2e9),
        wideband_band_hz=FrequencyBand(start_hz=0.5e9, stop_hz=3e9),
        gain_parameter="S21",
        input_return_parameter="S11",
    )

    # Valid for 2-port
    config.validate_against_port_count(2)

    # Invalid - S31 doesn't exist for 2-port
    config.gain_parameter = "S31"
    with pytest.raises(ValueError, match="Port 3 is invalid for 2-port device"):
        config.validate_against_port_count(2)

    # Valid for 4-port
    config.gain_parameter = "S31"
    config.validate_against_port_count(4)


def test_device_config_creation():
    """Test creating DeviceConfig."""
    config = DeviceConfig(
        name="Test Device",
        description="A test device",
        part_number="L123456",
    )
    assert config.name == "Test Device"
    assert config.part_number == "L123456"


def test_device_creation():
    """Test creating Device."""
    device_config = DeviceConfig(name="Test Device")
    device = Device(id=1, config=device_config)
    assert device.id == 1
    assert device.config.name == "Test Device"

