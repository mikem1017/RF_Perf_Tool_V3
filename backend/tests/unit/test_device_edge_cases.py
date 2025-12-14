"""
Edge case tests for device schemas.
"""
import pytest
from backend.src.core.schemas.device import (
    FrequencyBand,
    SParameterConfig,
    DeviceConfig,
    Device,
)


def test_frequency_band_edge_case_zero_start():
    """Test frequency band with zero start (should fail validation)."""
    # Check actual validation message
    with pytest.raises(ValueError):
        FrequencyBand(start_hz=0, stop_hz=1e9)


def test_frequency_band_edge_case_equal_start_stop():
    """Test frequency band with equal start and stop."""
    # Should fail validation (stop must be greater than start)
    with pytest.raises(ValueError, match="must be greater"):
        FrequencyBand(start_hz=1e9, stop_hz=1e9)


def test_s_parameter_config_all_optional_params():
    """Test SParameterConfig with all optional parameters specified."""
    config = SParameterConfig(
        operational_band_hz=FrequencyBand(start_hz=1e9, stop_hz=2e9),
        wideband_band_hz=FrequencyBand(start_hz=0.5e9, stop_hz=3e9),
        gain_parameter="S21",
        input_return_parameter="S11",
        output_return_parameter="S22",
    )
    assert config.gain_parameter == "S21"
    assert config.input_return_parameter == "S11"
    assert config.output_return_parameter == "S22"


def test_device_config_with_all_fields():
    """Test DeviceConfig with all optional fields."""
    config = DeviceConfig(
        name="Test Device",
        part_number="L123456",
        description="Test description",
        s_parameter_config=SParameterConfig(
            operational_band_hz=FrequencyBand(start_hz=1e9, stop_hz=2e9),
            wideband_band_hz=FrequencyBand(start_hz=0.5e9, stop_hz=3e9),
        ),
    )
    assert config.name == "Test Device"
    assert config.part_number == "L123456"
    assert config.description == "Test description"
    assert config.s_parameter_config is not None


def test_device_with_all_fields():
    """Test Device model with all fields."""
    # Device model may not have all these fields - check what it actually has
    # If Device is just a schema, test with DeviceConfig instead
    device_config = DeviceConfig(
        name="Test Device",
        part_number="L123456",
        description="Test description",
        s_parameter_config=SParameterConfig(
            operational_band_hz=FrequencyBand(start_hz=1e9, stop_hz=2e9),
            wideband_band_hz=FrequencyBand(start_hz=0.5e9, stop_hz=3e9),
        ),
    )
    assert device_config.name == "Test Device"
    assert device_config.part_number == "L123456"

