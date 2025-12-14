"""
Tests for storage interfaces using mocks.
"""
import pytest
from backend.src.storage.interfaces import IDatabase, IFileStorage
from backend.src.storage.mock_storage import MockDatabase, MockFileStorage, MockStorageFactory


def test_mock_database_create_device():
    """Test creating a device in mock database."""
    db = MockDatabase()
    device_id = db.create_device({"name": "Test Device", "part_number": "L123456"})
    assert device_id == 1
    
    device = db.get_device(device_id)
    assert device is not None
    assert device["name"] == "Test Device"
    assert device["id"] == device_id


def test_mock_database_create_test_run():
    """Test creating a test run in mock database."""
    db = MockDatabase()
    test_run_id = db.create_test_run({
        "device_id": 1,
        "test_stage_id": 1,
        "requirement_set_id": 1,
        "test_type": "s_parameter",
    })
    assert test_run_id == 1
    
    test_run = db.get_test_run(test_run_id)
    assert test_run is not None
    assert test_run["status"] == "created"


def test_mock_database_immutability():
    """Test that immutable test runs cannot be updated."""
    db = MockDatabase()
    test_run_id = db.create_test_run({
        "device_id": 1,
        "test_stage_id": 1,
        "requirement_set_id": 1,
        "test_type": "s_parameter",
    })
    
    # Mark as completed
    db.update_test_run_status(test_run_id, "completed")
    test_run = db.get_test_run(test_run_id)
    assert test_run["status"] == "completed"
    
    # Try to update - should fail
    with pytest.raises(ValueError, match="Cannot update immutable"):
        db.update_test_run_status(test_run_id, "processing")


def test_mock_file_storage_store_file():
    """Test storing a file in mock file storage."""
    storage = MockFileStorage()
    test_run_id = 1
    filename = "test.s2p"
    content = b"test file content"
    
    path = storage.store_uploaded_file(test_run_id, filename, content)
    assert path.name == filename
    assert "inputs" in str(path)
    
    retrieved_path = storage.get_file_path(test_run_id, filename)
    assert retrieved_path == path


def test_mock_file_storage_store_artifact():
    """Test storing an artifact in mock file storage."""
    storage = MockFileStorage()
    test_run_id = 1
    artifact_type = "plots"
    filename = "plot.png"
    content = b"fake png content"
    
    path = storage.store_artifact(test_run_id, artifact_type, filename, content)
    assert path.name == filename
    assert artifact_type in str(path)
    
    retrieved_path = storage.get_artifact_path(test_run_id, artifact_type, filename)
    assert retrieved_path == path


def test_mock_storage_factory():
    """Test mock storage factory."""
    factory = MockStorageFactory()
    db = factory.create_database()
    file_storage = factory.create_file_storage()
    
    assert isinstance(db, MockDatabase)
    assert isinstance(file_storage, MockFileStorage)

