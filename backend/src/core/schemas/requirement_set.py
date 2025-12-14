"""
Requirement set and metric limit models.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
from .device import FrequencyBand


class MetricLimit(BaseModel):
    """Metric limit definition."""
    metric_name: str = Field(..., description="Metric name (e.g., 'gain', 'vswr', 'return_loss')")
    aggregation: Literal["min", "max", "avg", "pkpk"] = Field(..., description="Aggregation method")
    operator: Literal["<=", ">=", "<", ">"] = Field(..., description="Comparison operator")
    limit_value: float = Field(..., description="Limit value")
    frequency_band: FrequencyBand = Field(..., description="Frequency band for evaluation")
    description: Optional[str] = Field(None, description="Requirement description")

    @field_validator("metric_name")
    @classmethod
    def validate_metric_name(cls, v):
        """Validate metric name."""
        valid_metrics = {"gain", "vswr", "return_loss", "gain_flatness"}
        if v not in valid_metrics:
            raise ValueError(f"Metric name must be one of: {valid_metrics}")
        return v


class PassPolicy(BaseModel):
    """Pass policy for requirement set."""
    all_files_must_pass: bool = Field(default=True, description="All files must pass for overall pass")
    required_paths: list[str] = Field(default_factory=list, description="Required paths (e.g., ['PRI'])")

    @field_validator("required_paths")
    @classmethod
    def validate_paths(cls, v):
        """Validate path identifiers."""
        valid_paths = {"PRI", "RED"}
        for path in v:
            if path.upper() not in valid_paths:
                raise ValueError(f"Path must be one of: {valid_paths}")
        return [p.upper() for p in v]


class RequirementSet(BaseModel):
    """Requirement set model."""
    id: Optional[int] = Field(None, description="Requirement set ID")
    name: str = Field(..., min_length=1, description="Requirement set name")
    test_type: str = Field(..., description="Test type (e.g., 's_parameter')")
    test_stage_id: Optional[int] = Field(None, description="Associated test stage ID")
    metric_limits: list[MetricLimit] = Field(default_factory=list, description="Metric limits")
    pass_policy: PassPolicy = Field(default_factory=PassPolicy, description="Pass policy")

    def compute_hash(self) -> str:
        """Compute hash of requirement set for traceability."""
        import hashlib
        import json
        # Create a deterministic JSON representation
        data = {
            "name": self.name,
            "test_type": self.test_type,
            "metric_limits": [
                {
                    "metric_name": m.metric_name,
                    "aggregation": m.aggregation,
                    "operator": m.operator,
                    "limit_value": m.limit_value,
                    "frequency_band": {
                        "start_hz": m.frequency_band.start_hz,
                        "stop_hz": m.frequency_band.stop_hz,
                    },
                }
                for m in self.metric_limits
            ],
            "pass_policy": {
                "all_files_must_pass": self.pass_policy.all_files_must_pass,
                "required_paths": self.pass_policy.required_paths,
            },
        }
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]

