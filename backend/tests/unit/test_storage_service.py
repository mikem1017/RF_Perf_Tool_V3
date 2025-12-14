"""
Tests for storage service.
"""
import pytest
from pathlib import Path
from backend.src.storage.storage_service import StorageService
from backend.src.storage.interfaces import IDatabase, IFileStorage


def test_storage_service_initialization():
    """Test storage service initialization."""
    service = StorageService(
        database_url="sqlite:///:memory:",
        file_storage_path=Path("/tmp/test_storage"),
    )
    
    assert service.database_url == "sqlite:///:memory:"
    assert service.file_storage_path == Path("/tmp/test_storage")


def test_storage_service_default_path():
    """Test storage service with default file storage path."""
    service = StorageService(database_url="sqlite:///:memory:")
    assert service.file_storage_path == Path("results")


def test_storage_service_create_database():
    """Test creating database instance."""
    service = StorageService(database_url="sqlite:///:memory:")
    db = service.create_database()
    
    assert isinstance(db, IDatabase)
    # Verify it's a SQLiteDatabase by checking it has the expected methods
    assert hasattr(db, 'create_device')
    assert hasattr(db, 'get_device')


def test_storage_service_create_file_storage():
    """Test creating file storage instance."""
    service = StorageService(
        database_url="sqlite:///:memory:",
        file_storage_path=Path("/tmp/test_storage"),
    )
    file_storage = service.create_file_storage()
    
    assert isinstance(file_storage, IFileStorage)
    assert hasattr(file_storage, 'store_uploaded_file')
    assert hasattr(file_storage, 'get_file_path')


def test_storage_service_get_session():
    """Test getting database session."""
    service = StorageService(database_url="sqlite:///:memory:")
    session = service.get_session()
    
    # Verify it's a SQLAlchemy session
    assert hasattr(session, 'query')
    assert hasattr(session, 'commit')
    assert hasattr(session, 'close')


def test_storage_service_implements_factory():
    """Test that StorageService implements IStorageFactory."""
    from backend.src.storage.interfaces import IStorageFactory
    
    service = StorageService(database_url="sqlite:///:memory:")
    assert isinstance(service, IStorageFactory)


