"""
Integration tests for database models and SQLite implementation.
"""
import pytest

# Skip all tests in this module if SQLAlchemy is not installed
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.src.storage.database import init_database, create_database_engine
    from backend.src.storage.sqlite_db import SQLiteDatabase
    from backend.src.storage.models import Device, TestStage, RequirementSet, TestRun
    SQLALCHEMY_AVAILABLE = True
    # Mark all tests in this module as requiring SQLAlchemy
    pytestmark = pytest.mark.requires_sqlalchemy
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Skip all tests if SQLAlchemy is not available
    pytestmark = pytest.mark.skip(
        reason="SQLAlchemy not installed. Install with: pip install -r backend/requirements.txt"
    )


@pytest.fixture
def db_session():
    """Create an in-memory database session for testing."""
    engine = create_database_engine("sqlite:///:memory:")
    init_database(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def db(db_session):
    """Create SQLiteDatabase instance."""
    return SQLiteDatabase(db_session)


def test_create_device(db):
    """Test creating a device."""
    device_id = db.create_device({
        "name": "Test Device",
        "part_number": "L123456",
        "s_parameter_config": {"gain_parameter": "S21"},
    })
    assert device_id == 1
    
    device = db.get_device(device_id)
    assert device is not None
    assert device["name"] == "Test Device"
    assert device["part_number"] == "L123456"


def test_get_device_not_found(db):
    """Test getting non-existent device."""
    device = db.get_device(999)
    assert device is None


def test_create_test_stage(db):
    """Test creating a test stage."""
    stage_id = db.create_test_stage({
        "name": "Production Test",
        "description": "Production testing stage",
    })
    assert stage_id == 1
    
    stage = db.get_test_stage(stage_id)
    assert stage is not None
    assert stage["name"] == "Production Test"


def test_create_test_stage_duplicate_name(db):
    """Test that duplicate test stage names are rejected."""
    db.create_test_stage({"name": "Production Test"})
    
    with pytest.raises(ValueError, match="already exists"):
        db.create_test_stage({"name": "Production Test"})


def test_create_requirement_set(db):
    """Test creating a requirement set."""
    req_set_id = db.create_requirement_set({
        "name": "Test Requirements",
        "test_type": "s_parameter",
        "metric_limits": [{"metric_name": "gain", "limit_value": -10.0}],
        "requirement_hash": "abc123",
    })
    assert req_set_id == 1
    
    req_set = db.get_requirement_set(req_set_id)
    assert req_set is not None
    assert req_set["name"] == "Test Requirements"
    assert req_set["requirement_hash"] == "abc123"


def test_create_test_run(db):
    """Test creating a test run."""
    # Create dependencies
    device_id = db.create_device({
        "name": "Test Device",
        "s_parameter_config": {},
    })
    stage_id = db.create_test_stage({"name": "Test Stage"})
    req_set_id = db.create_requirement_set({
        "name": "Test Requirements",
        "test_type": "s_parameter",
        "metric_limits": [],
        "requirement_hash": "abc123",
    })
    
    test_run_id = db.create_test_run({
        "device_id": device_id,
        "test_stage_id": stage_id,
        "requirement_set_id": req_set_id,
        "test_type": "s_parameter",
    })
    assert test_run_id == 1
    
    test_run = db.get_test_run(test_run_id)
    assert test_run is not None
    assert test_run["status"] == "created"
    assert test_run["device_id"] == device_id


def test_update_test_run_status(db):
    """Test updating test run status."""
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
    
    # Update status
    db.update_test_run_status(test_run_id, "processing")
    test_run = db.get_test_run(test_run_id)
    assert test_run["status"] == "processing"
    
    # Complete test run
    db.update_test_run_status(test_run_id, "completed")
    test_run = db.get_test_run(test_run_id)
    assert test_run["status"] == "completed"
    assert test_run["completed_at"] is not None


def test_update_test_run_immutability(db):
    """Test that immutable test runs cannot be updated."""
    # Create and complete test run
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
    
    db.update_test_run_status(test_run_id, "completed")
    
    # Try to update - should fail
    with pytest.raises(ValueError, match="Cannot update immutable"):
        db.update_test_run_status(test_run_id, "processing")


def test_add_test_run_file(db):
    """Test adding a file to a test run."""
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
    
    # Add file
    file_id = db.add_test_run_file(test_run_id, {
        "original_filename": "test.s2p",
        "stored_path": "/path/to/test.s2p",
        "effective_metadata": {"serial_number": "SN1234"},
    })
    assert file_id == 1


def test_store_metrics(db):
    """Test storing metrics."""
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
        "metrics": {"gain": [-5.0, -6.0]},
        "frequencies": [1e9, 2e9],
    })


def test_store_compliance(db):
    """Test storing compliance results."""
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
        "requirements": [{"requirement_name": "gain", "passed": True}],
        "failure_reasons": [],
    })

