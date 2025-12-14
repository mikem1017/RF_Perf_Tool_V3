"""
Tests for test stage schemas.
"""
import pytest
from backend.src.core.schemas.test_stage import TestStage


def test_test_stage_creation():
    """Test creating TestStage."""
    stage = TestStage(
        id=1,
        name="Qualification",
        description="Qualification test stage",
    )
    assert stage.id == 1
    assert stage.name == "Qualification"


def test_test_stage_name_validation():
    """Test test stage name validation."""
    # Valid name
    TestStage.validate_name_format("Qualification")

    # Empty name
    with pytest.raises(ValueError, match="cannot be empty"):
        TestStage.validate_name_format("")

    # Whitespace only
    with pytest.raises(ValueError, match="cannot be empty"):
        TestStage.validate_name_format("   ")

    # Too long
    long_name = "A" * 101
    with pytest.raises(ValueError, match="cannot exceed 100 characters"):
        TestStage.validate_name_format(long_name)


def test_test_stage_pydantic_validation():
    """Test Pydantic validation for TestStage."""
    # Valid
    stage = TestStage(name="EM")
    assert stage.name == "EM"

    # Empty name fails Pydantic validation
    with pytest.raises(Exception):  # Pydantic ValidationError
        TestStage(name="")

