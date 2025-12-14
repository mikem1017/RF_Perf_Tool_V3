"""
Tests for SQLite database helper methods.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.src.storage.database import init_database, create_database_engine
from backend.src.storage.sqlite_db import SQLiteDatabase
from backend.src.storage.models import Device, TestStage, RequirementSet, TestRun


@pytest.fixture
def db():
    """Create database instance."""
    engine = create_database_engine("sqlite:///:memory:")
    init_database(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return SQLiteDatabase(session)


def test_device_to_dict(db):
    """Test _device_to_dict helper method."""
    device_id = db.create_device({
        "name": "Test Device",
        "part_number": "L123456",
        "description": "Test description",
        "s_parameter_config": {"gain_parameter": "S21"},
    })
    
    device = db.get_device(device_id)
    assert device is not None
    assert device["name"] == "Test Device"
    assert device["part_number"] == "L123456"
    assert device["description"] == "Test description"
    assert "id" in device
    assert "created_at" in device
    assert "updated_at" in device


def test_test_stage_to_dict(db):
    """Test _test_stage_to_dict helper method."""
    stage_id = db.create_test_stage({
        "name": "Test Stage",
        "description": "Stage description",
    })
    
    stage = db.get_test_stage(stage_id)
    assert stage is not None
    assert stage["name"] == "Test Stage"
    assert stage["description"] == "Stage description"
    assert "id" in stage
    assert "created_at" in stage
    assert "updated_at" in stage


def test_requirement_set_to_dict(db):
    """Test _requirement_set_to_dict helper method."""
    req_set_id = db.create_requirement_set({
        "name": "Test Requirements",
        "test_type": "s_parameter",
        "metric_limits": [{"metric_name": "gain"}],
        "requirement_hash": "abc123",
    })
    
    req_set = db.get_requirement_set(req_set_id)
    assert req_set is not None
    assert req_set["name"] == "Test Requirements"
    assert req_set["test_type"] == "s_parameter"
    assert req_set["requirement_hash"] == "abc123"
    assert "id" in req_set
    assert "created_at" in req_set
    assert "updated_at" in req_set


def test_test_run_to_dict(db):
    """Test _test_run_to_dict helper method."""
    device_id = db.create_device({"name": "Test", "s_parameter_config": {}})
    stage_id = db.create_test_stage({"name": "Test"})
    req_set_id = db.create_requirement_set({
        "name": "Test", "test_type": "s_parameter", "metric_limits": [], "requirement_hash": "abc"
    })
    
    test_run_id = db.create_test_run({
        "device_id": device_id,
        "test_stage_id": stage_id,
        "requirement_set_id": req_set_id,
        "test_type": "s_parameter",
    })
    
    test_run = db.get_test_run(test_run_id)
    assert test_run is not None
    assert test_run["device_id"] == device_id
    assert test_run["test_stage_id"] == stage_id
    assert test_run["requirement_set_id"] == req_set_id
    assert test_run["status"] == "created"
    assert "id" in test_run
    assert "created_at" in test_run


