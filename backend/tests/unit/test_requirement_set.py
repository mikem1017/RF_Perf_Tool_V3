"""
Tests for requirement set schemas.
"""
import pytest
from backend.src.core.schemas.requirement_set import (
    RequirementSet,
    MetricLimit,
    PassPolicy,
)
from backend.src.core.schemas.device import FrequencyBand


def test_metric_limit_creation():
    """Test creating MetricLimit."""
    limit = MetricLimit(
        metric_name="gain",
        aggregation="min",
        operator=">=",
        limit_value=-10.0,
        frequency_band=FrequencyBand(start_hz=1e9, stop_hz=2e9),
    )
    assert limit.metric_name == "gain"
    assert limit.aggregation == "min"
    assert limit.operator == ">="
    assert limit.limit_value == -10.0


def test_metric_limit_validation_metric_name():
    """Test metric name validation."""
    # Valid metrics
    for metric in ["gain", "vswr", "return_loss", "gain_flatness"]:
        limit = MetricLimit(
            metric_name=metric,
            aggregation="min",
            operator=">=",
            limit_value=1.0,
            frequency_band=FrequencyBand(start_hz=1e9, stop_hz=2e9),
        )
        assert limit.metric_name == metric

    # Invalid metric
    with pytest.raises(ValueError, match="Metric name must be one of"):
        MetricLimit(
            metric_name="invalid_metric",
            aggregation="min",
            operator=">=",
            limit_value=1.0,
            frequency_band=FrequencyBand(start_hz=1e9, stop_hz=2e9),
        )


def test_metric_limit_aggregation_types():
    """Test all aggregation types."""
    for agg in ["min", "max", "avg", "pkpk"]:
        limit = MetricLimit(
            metric_name="gain",
            aggregation=agg,
            operator=">=",
            limit_value=1.0,
            frequency_band=FrequencyBand(start_hz=1e9, stop_hz=2e9),
        )
        assert limit.aggregation == agg


def test_pass_policy_creation():
    """Test creating PassPolicy."""
    policy = PassPolicy(
        all_files_must_pass=True,
        required_paths=["PRI"],
    )
    assert policy.all_files_must_pass is True
    assert "PRI" in policy.required_paths


def test_pass_policy_path_validation():
    """Test path validation in PassPolicy."""
    # Valid paths
    policy = PassPolicy(required_paths=["PRI", "RED"])
    assert "PRI" in policy.required_paths
    assert "RED" in policy.required_paths

    # Invalid path
    with pytest.raises(ValueError, match="Path must be one of"):
        PassPolicy(required_paths=["INVALID"])

    # Case insensitive
    policy = PassPolicy(required_paths=["pri", "red"])
    assert "PRI" in policy.required_paths  # Normalized to uppercase
    assert "RED" in policy.required_paths


def test_requirement_set_creation():
    """Test creating RequirementSet."""
    req_set = RequirementSet(
        name="S-Parameter Requirements",
        test_type="s_parameter",
        metric_limits=[
            MetricLimit(
                metric_name="gain",
                aggregation="min",
                operator=">=",
                limit_value=-10.0,
                frequency_band=FrequencyBand(start_hz=1e9, stop_hz=2e9),
            )
        ],
    )
    assert req_set.name == "S-Parameter Requirements"
    assert len(req_set.metric_limits) == 1


def test_requirement_set_hash():
    """Test requirement set hash computation."""
    req_set1 = RequirementSet(
        name="Test",
        test_type="s_parameter",
        metric_limits=[
            MetricLimit(
                metric_name="gain",
                aggregation="min",
                operator=">=",
                limit_value=-10.0,
                frequency_band=FrequencyBand(start_hz=1e9, stop_hz=2e9),
            )
        ],
    )
    hash1 = req_set1.compute_hash()

    # Same requirement set should have same hash
    req_set2 = RequirementSet(
        name="Test",
        test_type="s_parameter",
        metric_limits=[
            MetricLimit(
                metric_name="gain",
                aggregation="min",
                operator=">=",
                limit_value=-10.0,
                frequency_band=FrequencyBand(start_hz=1e9, stop_hz=2e9),
            )
        ],
    )
    hash2 = req_set2.compute_hash()
    assert hash1 == hash2

    # Different requirement set should have different hash
    req_set3 = RequirementSet(
        name="Test",
        test_type="s_parameter",
        metric_limits=[
            MetricLimit(
                metric_name="gain",
                aggregation="min",
                operator=">=",
                limit_value=-5.0,  # Different limit
                frequency_band=FrequencyBand(start_hz=1e9, stop_hz=2e9),
            )
        ],
    )
    hash3 = req_set3.compute_hash()
    assert hash1 != hash3

