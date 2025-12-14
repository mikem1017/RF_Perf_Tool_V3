"""
Edge case tests for SQLite database implementation.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.src.storage.database import init_database, create_database_engine
from backend.src.storage.sqlite_db import SQLiteDatabase


@pytest.fixture
def db():
    """Create database instance."""
    engine = create_database_engine("sqlite:///:memory:")
    init_database(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return SQLiteDatabase(session)


def test_sqlite_db_update_nonexistent_test_run(db):
    """Test updating non-existent test run."""
    with pytest.raises(ValueError, match="not found"):
        db.update_test_run_status(999, "processing")


def test_sqlite_db_add_file_to_nonexistent_test_run(db):
    """Test adding file to non-existent test run."""
    with pytest.raises(ValueError, match="not found"):
        db.add_test_run_file(999, {
            "original_filename": "test.s2p",
            "stored_path": "/path/to/test.s2p",
            "effective_metadata": {},
        })


def test_sqlite_db_store_metrics_nonexistent_test_run(db):
    """Test storing metrics for non-existent test run."""
    with pytest.raises(ValueError, match="not found"):
        db.store_metrics(999, 1, {"metrics": {}, "frequencies": []})


def test_sqlite_db_store_metrics_nonexistent_file(db):
    """Test storing metrics for non-existent file."""
    # Create test run
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
    
    # Try to store metrics for non-existent file
    with pytest.raises(ValueError, match="not found"):
        db.store_metrics(test_run_id, 999, {"metrics": {}, "frequencies": []})


def test_sqlite_db_store_compliance_nonexistent_test_run(db):
    """Test storing compliance for non-existent test run."""
    with pytest.raises(ValueError, match="not found"):
        db.store_compliance(999, 1, {"overall_pass": True, "requirements": []})


def test_sqlite_db_store_compliance_nonexistent_file(db):
    """Test storing compliance for non-existent file."""
    # Create test run
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
    
    # Try to store compliance for non-existent file
    with pytest.raises(ValueError, match="not found"):
        db.store_compliance(test_run_id, 999, {"overall_pass": True, "requirements": []})


def test_sqlite_db_update_metrics_existing(db):
    """Test updating existing metrics."""
    # Create test run and file
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
    file_id = db.add_test_run_file(test_run_id, {
        "original_filename": "test.s2p",
        "stored_path": "/path/to/test.s2p",
        "effective_metadata": {},
    })
    
    # Store metrics
    db.store_metrics(test_run_id, file_id, {
        "metrics": {"gain": [-5.0]},
        "frequencies": [1e9],
    })
    
    # Update metrics
    db.store_metrics(test_run_id, file_id, {
        "metrics": {"gain": [-6.0]},
        "frequencies": [2e9],
    })
    
    # Should not raise error (update works)


def test_sqlite_db_update_compliance_existing(db):
    """Test updating existing compliance."""
    # Create test run and file
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
    file_id = db.add_test_run_file(test_run_id, {
        "original_filename": "test.s2p",
        "stored_path": "/path/to/test.s2p",
        "effective_metadata": {},
    })
    
    # Store compliance
    db.store_compliance(test_run_id, file_id, {
        "overall_pass": True,
        "requirements": [{"passed": True}],
    })
    
    # Update compliance
    db.store_compliance(test_run_id, file_id, {
        "overall_pass": False,
        "requirements": [{"passed": False}],
    })
    
    # Should not raise error (update works)


