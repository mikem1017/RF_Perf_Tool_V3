"""
Integration tests for file storage implementation.
"""
import pytest
from pathlib import Path

# File storage doesn't require SQLAlchemy, so these tests should always run
from backend.src.storage.file_storage import FilesystemFileStorage


@pytest.fixture
def file_storage(temp_dir):
    """Create FilesystemFileStorage instance."""
    return FilesystemFileStorage(temp_dir)


def test_store_uploaded_file(file_storage, temp_dir):
    """Test storing an uploaded file."""
    test_run_id = 1
    filename = "test.s2p"
    content = b"test file content"
    
    path = file_storage.store_uploaded_file(test_run_id, filename, content)
    
    assert path.exists()
    assert path.name == filename
    assert path.read_bytes() == content
    assert "inputs" in str(path)


def test_get_file_path(file_storage):
    """Test getting file path."""
    test_run_id = 1
    filename = "test.s2p"
    content = b"test content"
    
    file_storage.store_uploaded_file(test_run_id, filename, content)
    retrieved_path = file_storage.get_file_path(test_run_id, filename)
    
    assert retrieved_path is not None
    assert retrieved_path.name == filename


def test_get_file_path_not_found(file_storage):
    """Test getting non-existent file path."""
    path = file_storage.get_file_path(999, "nonexistent.s2p")
    assert path is None


def test_create_artifact_directory(file_storage):
    """Test creating artifact directory."""
    test_run_id = 1
    artifact_type = "plots"
    
    path = file_storage.create_artifact_directory(test_run_id, artifact_type)
    
    assert path.exists()
    assert path.is_dir()
    assert artifact_type in str(path)


def test_store_artifact(file_storage):
    """Test storing an artifact."""
    test_run_id = 1
    artifact_type = "plots"
    filename = "plot.png"
    content = b"fake png content"
    
    path = file_storage.store_artifact(test_run_id, artifact_type, filename, content)
    
    assert path.exists()
    assert path.name == filename
    assert path.read_bytes() == content


def test_get_artifact_path(file_storage):
    """Test getting artifact path."""
    test_run_id = 1
    artifact_type = "plots"
    filename = "plot.png"
    content = b"fake content"
    
    file_storage.store_artifact(test_run_id, artifact_type, filename, content)
    retrieved_path = file_storage.get_artifact_path(test_run_id, artifact_type, filename)
    
    assert retrieved_path is not None
    assert retrieved_path.name == filename


def test_get_artifact_path_not_found(file_storage):
    """Test getting non-existent artifact path."""
    path = file_storage.get_artifact_path(999, "plots", "nonexistent.png")
    assert path is None


def test_storage_directory_structure(file_storage, temp_dir):
    """Test that storage creates proper directory structure."""
    test_run_id = 1
    
    # Store file
    file_storage.store_uploaded_file(test_run_id, "test.s2p", b"content")
    
    # Store artifact
    file_storage.store_artifact(test_run_id, "plots", "plot.png", b"content")
    
    # Verify structure
    inputs_dir = temp_dir / str(test_run_id) / "inputs"
    artifacts_dir = temp_dir / str(test_run_id) / "artifacts" / "plots"
    
    assert inputs_dir.exists()
    assert artifacts_dir.exists()

