"""
Integration tests for storage service.
"""
import pytest
from pathlib import Path
from backend.src.storage.storage_service import StorageService


@pytest.fixture
def storage_service(temp_dir):
    """Create storage service with temporary directory."""
    return StorageService(
        database_url="sqlite:///:memory:",
        file_storage_path=temp_dir,
    )


def test_storage_service_full_workflow(storage_service):
    """Test complete workflow using storage service."""
    # Create database and file storage
    db = storage_service.create_database()
    file_storage = storage_service.create_file_storage()
    
    # Create a device
    device_id = db.create_device({
        "name": "Test Device",
        "s_parameter_config": {"gain_parameter": "S21"},
    })
    
    # Store a file
    file_path = file_storage.store_uploaded_file(
        test_run_id=1,
        original_filename="test.s2p",
        file_content=b"test content",
    )
    
    # Verify both work together
    assert device_id == 1
    assert file_path.exists()
    assert file_path.read_bytes() == b"test content"


def test_storage_service_multiple_instances():
    """Test that multiple database instances work correctly."""
    service = StorageService(database_url="sqlite:///:memory:")
    
    db1 = service.create_database()
    db2 = service.create_database()
    
    # Each should be independent (they share the same engine but have different sessions)
    # In SQLite with in-memory, they actually share the same database
    device_id1 = db1.create_device({"name": "Device 1", "s_parameter_config": {}})
    device_id2 = db2.create_device({"name": "Device 2", "s_parameter_config": {}})
    
    # Both should work - they share the same in-memory database
    assert device_id1 == 1
    assert device_id2 == 2  # Same database, so IDs increment


def test_storage_service_file_storage_path_creation(storage_service, temp_dir):
    """Test that file storage creates directories."""
    file_storage = storage_service.create_file_storage()
    
    # Store a file - should create directory structure
    file_path = file_storage.store_uploaded_file(
        test_run_id=1,
        original_filename="test.s2p",
        file_content=b"content",
    )
    
    # Verify directory was created
    assert file_path.parent.exists()
    assert "inputs" in str(file_path)

