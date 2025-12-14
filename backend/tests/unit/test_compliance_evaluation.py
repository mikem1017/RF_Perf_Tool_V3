"""
Tests for compliance evaluation.
"""
import pytest
import numpy as np
from backend.src.plugins.s_parameter.compliance import (
    evaluate_compliance,
    ComplianceResult,
    _aggregate_metric,
    _evaluate_limit,
)
from backend.src.core.schemas.requirement_set import (
    RequirementSet,
    MetricLimit,
    PassPolicy,
)
from backend.src.core.schemas.device import FrequencyBand


def create_sample_requirement_set() -> RequirementSet:
    """Create a sample requirement set for testing."""
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
            MetricLimit(
                metric_name="vswr",
                aggregation="max",
                operator="<=",
                limit_value=2.0,
                frequency_band=FrequencyBand(start_hz=1e9, stop_hz=2e9),
                description="Maximum VSWR",
            ),
        ],
    )


def test_aggregate_metric_min():
    """Test min aggregation."""
    values = np.array([-5.0, -10.0, -8.0, -12.0])
    result = _aggregate_metric(values, "min")
    assert result == -12.0


def test_aggregate_metric_max():
    """Test max aggregation."""
    values = np.array([-5.0, -10.0, -8.0, -12.0])
    result = _aggregate_metric(values, "max")
    assert result == -5.0


def test_aggregate_metric_avg():
    """Test average aggregation."""
    values = np.array([-5.0, -10.0, -8.0, -12.0])
    result = _aggregate_metric(values, "avg")
    assert np.isclose(result, -8.75)


def test_aggregate_metric_pkpk():
    """Test peak-to-peak aggregation."""
    values = np.array([-5.0, -10.0, -8.0, -12.0])
    result = _aggregate_metric(values, "pkpk")
    assert result == 7.0  # -5.0 - (-12.0) = 7.0


def test_evaluate_limit_less_equal():
    """Test <= operator."""
    assert _evaluate_limit(5.0, 10.0, "<=") is True
    assert _evaluate_limit(10.0, 10.0, "<=") is True
    assert _evaluate_limit(15.0, 10.0, "<=") is False


def test_evaluate_limit_greater_equal():
    """Test >= operator."""
    assert _evaluate_limit(15.0, 10.0, ">=") is True
    assert _evaluate_limit(10.0, 10.0, ">=") is True
    assert _evaluate_limit(5.0, 10.0, ">=") is False


def test_evaluate_limit_less_than():
    """Test < operator."""
    assert _evaluate_limit(5.0, 10.0, "<") is True
    assert _evaluate_limit(10.0, 10.0, "<") is False
    assert _evaluate_limit(15.0, 10.0, "<") is False


def test_evaluate_limit_greater_than():
    """Test > operator."""
    assert _evaluate_limit(15.0, 10.0, ">") is True
    assert _evaluate_limit(10.0, 10.0, ">") is False
    assert _evaluate_limit(5.0, 10.0, ">") is False


def test_evaluate_compliance_pass():
    """Test compliance evaluation with passing metrics."""
    req_set = create_sample_requirement_set()
    
    # Create metrics that pass
    frequencies = np.array([1e9, 1.5e9, 2e9])
    metrics = {
        "gain": np.array([-5.0, -6.0, -7.0]),  # All >= -10.0 (min = -7.0)
        "vswr": np.array([1.5, 1.6, 1.7]),     # All <= 2.0 (max = 1.7)
    }
    
    result = evaluate_compliance(metrics, frequencies, req_set)
    
    assert result.overall_pass is True
    assert len(result.requirements) == 2
    assert all(r["passed"] for r in result.requirements)
    assert len(result.failure_reasons) == 0


def test_evaluate_compliance_fail():
    """Test compliance evaluation with failing metrics."""
    req_set = create_sample_requirement_set()
    
    # Create metrics that fail
    frequencies = np.array([1e9, 1.5e9, 2e9])
    metrics = {
        "gain": np.array([-5.0, -6.0, -15.0]),  # Min = -15.0 < -10.0 (fails)
        "vswr": np.array([1.5, 1.6, 1.7]),      # Max = 1.7 <= 2.0 (passes)
    }
    
    result = evaluate_compliance(metrics, frequencies, req_set)
    
    assert result.overall_pass is False
    assert len(result.requirements) == 2
    # First requirement (gain) should fail
    assert result.requirements[0]["passed"] is False
    # Second requirement (vswr) should pass
    assert result.requirements[1]["passed"] is True
    assert len(result.failure_reasons) == 1


def test_evaluate_compliance_exactly_at_limit():
    """Test compliance evaluation when value is exactly at limit."""
    req_set = create_sample_requirement_set()
    
    frequencies = np.array([1e9, 2e9])
    metrics = {
        "gain": np.array([-10.0, -10.0]),  # Exactly at limit (>= -10.0 should pass)
        "vswr": np.array([2.0, 2.0]),      # Exactly at limit (<= 2.0 should pass)
    }
    
    result = evaluate_compliance(metrics, frequencies, req_set)
    
    assert result.overall_pass is True
    assert all(r["passed"] for r in result.requirements)


def test_evaluate_compliance_frequency_band_slicing():
    """Test that metrics are sliced by frequency band before aggregation."""
    req_set = RequirementSet(
        name="Test",
        test_type="s_parameter",
        metric_limits=[
            MetricLimit(
                metric_name="gain",
                aggregation="min",
                operator=">=",
                limit_value=-8.0,
                frequency_band=FrequencyBand(start_hz=1.5e9, stop_hz=2e9),  # Only last 2 points
                description="Gain in upper band",
            ),
        ],
    )
    
    frequencies = np.array([1e9, 1.5e9, 2e9])
    metrics = {
        "gain": np.array([-15.0, -6.0, -5.0]),  # First point is bad, but not in band
    }
    
    result = evaluate_compliance(metrics, frequencies, req_set)
    
    # Should pass because only points in band (1.5e9-2e9) are considered
    # Min of [-6.0, -5.0] = -6.0 >= -8.0
    assert result.overall_pass is True
    assert result.requirements[0]["passed"] is True


def test_evaluate_compliance_missing_metric():
    """Test compliance evaluation with missing metric."""
    req_set = create_sample_requirement_set()
    
    frequencies = np.array([1e9, 2e9])
    metrics = {
        "gain": np.array([-5.0, -6.0]),
        # vswr is missing
    }
    
    result = evaluate_compliance(metrics, frequencies, req_set)
    
    assert result.overall_pass is False
    # Second requirement should fail due to missing metric
    assert result.requirements[1]["passed"] is False
    assert "not found" in result.requirements[1]["failure_reason"].lower()


def test_evaluate_compliance_out_of_band():
    """Test compliance evaluation when no frequencies are in band."""
    req_set = RequirementSet(
        name="Test",
        test_type="s_parameter",
        metric_limits=[
            MetricLimit(
                metric_name="gain",
                aggregation="min",
                operator=">=",
                limit_value=-10.0,
                frequency_band=FrequencyBand(start_hz=3e9, stop_hz=4e9),  # Out of range
                description="Gain",
            ),
        ],
    )
    
    frequencies = np.array([1e9, 2e9])
    metrics = {
        "gain": np.array([-5.0, -6.0]),
    }
    
    result = evaluate_compliance(metrics, frequencies, req_set)
    
    assert result.overall_pass is False
    assert result.requirements[0]["passed"] is False
    assert "No frequency points" in result.requirements[0]["failure_reason"]


def test_evaluate_compliance_all_aggregation_types():
    """Test all aggregation types."""
    frequencies = np.array([1e9, 1.5e9, 2e9])
    values = np.array([-5.0, -8.0, -12.0])
    
    for agg in ["min", "max", "avg", "pkpk"]:
        req_set = RequirementSet(
            name="Test",
            test_type="s_parameter",
            metric_limits=[
                MetricLimit(
                    metric_name="gain",
                    aggregation=agg,
                    operator=">=",
                    limit_value=-20.0,  # High limit so it passes
                    frequency_band=FrequencyBand(start_hz=1e9, stop_hz=2e9),
                ),
            ],
        )
        
        metrics = {"gain": values}
        result = evaluate_compliance(metrics, frequencies, req_set)
        
        assert result.overall_pass is True
        assert result.requirements[0]["passed"] is True

