"""
Compliance evaluation logic.

Pure function for evaluating metrics against requirement sets.
No side effects, no I/O operations.
"""
from typing import Dict, List, Any, Optional
import numpy as np
from backend.src.core.schemas.requirement_set import RequirementSet, MetricLimit
from backend.src.core.schemas.device import FrequencyBand


class ComplianceResult:
    """Result of compliance evaluation."""
    
    def __init__(self):
        self.requirements: List[Dict[str, Any]] = []
        self.overall_pass: bool = True
        self.failure_reasons: List[str] = []
    
    def add_requirement_result(
        self,
        requirement_name: str,
        limit_value: float,
        computed_value: float,
        passed: bool,
        failure_reason: Optional[str] = None,
    ):
        """Add a requirement evaluation result."""
        self.requirements.append({
            "requirement_name": requirement_name,
            "limit_value": limit_value,
            "computed_value": computed_value,
            "passed": passed,
            "failure_reason": failure_reason,
        })
        if not passed:
            self.overall_pass = False
            if failure_reason:
                self.failure_reasons.append(failure_reason)


def evaluate_compliance(
    metrics: Dict[str, np.ndarray],
    frequencies: np.ndarray,
    requirement_set: RequirementSet,
) -> ComplianceResult:
    """
    Evaluate metrics against requirement set.
    
    Args:
        metrics: Dictionary of metric arrays (e.g., {"gain": array, "vswr": array})
        frequencies: Frequency array in Hz
        requirement_set: Requirement set to evaluate against
    
    Returns:
        ComplianceResult with pass/fail for each requirement
    """
    result = ComplianceResult()
    
    for metric_limit in requirement_set.metric_limits:
        metric_name = metric_limit.metric_name
        
        if metric_name not in metrics:
            result.add_requirement_result(
                requirement_name=metric_limit.description or metric_name,
                limit_value=metric_limit.limit_value,
                computed_value=0.0,
                passed=False,
                failure_reason=f"Metric '{metric_name}' not found in computed metrics",
            )
            continue
        
        # Get metric values within the frequency band
        metric_values = metrics[metric_name]
        band = metric_limit.frequency_band
        mask = (frequencies >= band.start_hz) & (frequencies <= band.stop_hz)
        
        if not np.any(mask):
            result.add_requirement_result(
                requirement_name=metric_limit.description or metric_name,
                limit_value=metric_limit.limit_value,
                computed_value=0.0,
                passed=False,
                failure_reason=f"No frequency points in band {band.start_hz}-{band.stop_hz} Hz",
            )
            continue
        
        band_metric_values = metric_values[mask]
        
        # Aggregate based on aggregation method
        aggregated_value = _aggregate_metric(
            band_metric_values,
            metric_limit.aggregation
        )
        
        # Evaluate against limit
        passed = _evaluate_limit(
            aggregated_value,
            metric_limit.limit_value,
            metric_limit.operator
        )
        
        # Generate failure reason if needed
        failure_reason = None
        if not passed:
            failure_reason = (
                f"{metric_name} {metric_limit.aggregation} = {aggregated_value:.3f} "
                f"{metric_limit.operator} {metric_limit.limit_value} (limit)"
            )
        
        result.add_requirement_result(
            requirement_name=metric_limit.description or metric_name,
            limit_value=metric_limit.limit_value,
            computed_value=aggregated_value,
            passed=passed,
            failure_reason=failure_reason,
        )
    
    return result


def _aggregate_metric(values: np.ndarray, aggregation: str) -> float:
    """
    Aggregate metric values over frequency band.
    
    Args:
        values: Array of metric values
        aggregation: Aggregation method (min, max, avg, pkpk)
    
    Returns:
        Aggregated value
    """
    if aggregation == "min":
        return float(np.min(values))
    elif aggregation == "max":
        return float(np.max(values))
    elif aggregation == "avg":
        return float(np.mean(values))
    elif aggregation == "pkpk":
        return float(np.max(values) - np.min(values))
    else:
        raise ValueError(f"Unknown aggregation method: {aggregation}")


def _evaluate_limit(value: float, limit: float, operator: str) -> bool:
    """
    Evaluate value against limit using operator.
    
    Args:
        value: Computed value
        limit: Limit value
        operator: Comparison operator (<=, >=, <, >)
    
    Returns:
        True if condition is met, False otherwise
    """
    if operator == "<=":
        return value <= limit
    elif operator == ">=":
        return value >= limit
    elif operator == "<":
        return value < limit
    elif operator == ">":
        return value > limit
    else:
        raise ValueError(f"Unknown operator: {operator}")

