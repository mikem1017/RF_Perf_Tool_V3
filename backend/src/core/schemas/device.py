"""
Device and device configuration models.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


class FrequencyBand(BaseModel):
    """Frequency band definition."""
    start_hz: float = Field(..., gt=0, description="Start frequency in Hz")
    stop_hz: float = Field(..., gt=0, description="Stop frequency in Hz")

    @field_validator("stop_hz")
    @classmethod
    def validate_stop_greater_than_start(cls, v, info):
        """Validate that stop frequency is greater than start frequency."""
        if "start_hz" in info.data and v <= info.data["start_hz"]:
            raise ValueError("stop_hz must be greater than start_hz")
        return v


class SParameterConfig(BaseModel):
    """S-parameter configuration for a device."""
    operational_band_hz: FrequencyBand = Field(..., description="Operational frequency band")
    wideband_band_hz: FrequencyBand = Field(..., description="Wideband frequency band")
    gain_parameter: str = Field(default="S21", description="S-parameter for gain (e.g., S21, S31)")
    input_return_parameter: str = Field(default="S11", description="S-parameter for input return loss")
    output_return_parameter: Optional[str] = Field(default="S22", description="S-parameter for output return loss")
    additional_traces: list[str] = Field(default_factory=list, description="Additional Sij traces to plot")
    port_labels: Optional[dict[int, str]] = Field(None, description="Port labels (e.g., {1: 'RF IN', 2: 'RF OUT'})")

    @field_validator("gain_parameter", "input_return_parameter", "output_return_parameter")
    @classmethod
    def validate_s_parameter_format(cls, v):
        """Validate S-parameter format (Sij where i,j are digits)."""
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("S-parameter must be a string")
        if not v.startswith("S"):
            raise ValueError("S-parameter must start with 'S'")
        # Extract port numbers (e.g., "S21" -> i=2, j=1)
        try:
            port_str = v[1:]
            if len(port_str) != 2:
                raise ValueError("S-parameter must have format Sij where i and j are single digits")
            i, j = int(port_str[0]), int(port_str[1])
            if i < 1 or j < 1 or i > 9 or j > 9:
                raise ValueError("Port numbers must be between 1 and 9")
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid S-parameter format: {v}") from e
        return v

    def validate_against_port_count(self, port_count: int) -> None:
        """Validate that S-parameters are valid for the given port count."""
        def get_port_numbers(s_param: str) -> tuple[int, int]:
            port_str = s_param[1:]
            return int(port_str[0]), int(port_str[1])

        def check_port_valid(port: int) -> None:
            if port < 1 or port > port_count:
                raise ValueError(f"Port {port} is invalid for {port_count}-port device")

        if self.gain_parameter:
            i, j = get_port_numbers(self.gain_parameter)
            check_port_valid(i)
            check_port_valid(j)

        if self.input_return_parameter:
            i, j = get_port_numbers(self.input_return_parameter)
            check_port_valid(i)
            check_port_valid(j)

        if self.output_return_parameter:
            i, j = get_port_numbers(self.output_return_parameter)
            check_port_valid(i)
            check_port_valid(j)

        for trace in self.additional_traces:
            i, j = get_port_numbers(trace)
            check_port_valid(i)
            check_port_valid(j)


class DeviceConfig(BaseModel):
    """Device configuration."""
    name: str = Field(..., min_length=1, description="Device name")
    description: Optional[str] = Field(None, description="Device description")
    part_number: Optional[str] = Field(None, description="Part number")
    revision: Optional[str] = Field(None, description="Revision")
    supported_test_types: list[str] = Field(default_factory=list, description="Supported test types")
    s_parameter_config: Optional[SParameterConfig] = Field(None, description="S-parameter configuration")


class Device(BaseModel):
    """Device model."""
    id: Optional[int] = Field(None, description="Device ID")
    config: DeviceConfig = Field(..., description="Device configuration")

