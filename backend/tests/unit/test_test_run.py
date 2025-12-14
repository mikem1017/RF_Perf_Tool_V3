"""
Tests for test run schemas.
"""
import pytest
from datetime import datetime
from backend.src.core.schemas.test_run import (
    TestRun,
    TestRunStatus,
    TestRunFile,
)
from backend.src.core.schemas.metadata import EffectiveMetadata


def test_test_run_status_creation():
    """Test creating TestRunStatus."""
    status = TestRunStatus(status="created")
    assert status.status == "created"
    assert status.error_message is None


def test_test_run_status_failed():
    """Test TestRunStatus with error."""
    status = TestRunStatus(
        status="failed",
        error_message="Test failed",
    )
    assert status.status == "failed"
    assert status.error_message == "Test failed"


def test_test_run_file_creation():
    """Test creating TestRunFile."""
    metadata = EffectiveMetadata(
        serial_number="SN1234",
        path="PRI",
    )
    file = TestRunFile(
        id=1,
        original_filename="test.s2p",
        stored_path="/path/to/test.s2p",
        effective_metadata=metadata,
    )
    assert file.original_filename == "test.s2p"
    assert file.effective_metadata.serial_number == "SN1234"


def test_test_run_creation():
    """Test creating TestRun."""
    test_run = TestRun(
        id=1,
        device_id=10,
        test_stage_id=20,
        requirement_set_id=30,
        test_type="s_parameter",
    )
    assert test_run.id == 1
    assert test_run.device_id == 10
    assert test_run.status.status == "created"


def test_test_run_is_completed():
    """Test is_completed method."""
    test_run = TestRun(
        device_id=10,
        test_stage_id=20,
        requirement_set_id=30,
        test_type="s_parameter",
    )
    assert not test_run.is_completed()

    test_run.status.status = "completed"
    assert test_run.is_completed()


def test_test_run_is_immutable():
    """Test is_immutable method."""
    test_run = TestRun(
        device_id=10,
        test_stage_id=20,
        requirement_set_id=30,
        test_type="s_parameter",
    )
    assert not test_run.is_immutable()

    test_run.status.status = "completed"
    assert test_run.is_immutable()

    test_run.status.status = "failed"
    assert test_run.is_immutable()

    test_run.status.status = "processing"
    assert not test_run.is_immutable()

