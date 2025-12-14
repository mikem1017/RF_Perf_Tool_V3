"""
Tests for API dependencies.
"""
import pytest
import os
from pathlib import Path
from backend.src.api.dependencies import (
    get_storage_service,
    get_database,
    get_file_storage,
    get_test_run_service,
)
from backend.src.storage.interfaces import IDatabase, IFileStorage
from backend.src.services.test_run_service import TestRunService


def test_get_storage_service():
    """Test getting storage service."""
    # Clear cache to ensure fresh instance
    get_storage_service.cache_clear()
    
    # Set environment for in-memory database
    os.environ["RF_TOOL_DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["RF_TOOL_STORAGE_PATH"] = "/tmp/test_storage"
    
    service = get_storage_service()
    assert service is not None
    assert service.database_url == "sqlite:///:memory:"
    assert service.file_storage_path == Path("/tmp/test_storage")


def test_get_storage_service_caching():
    """Test that get_storage_service is cached."""
    get_storage_service.cache_clear()
    
    os.environ["RF_TOOL_DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["RF_TOOL_STORAGE_PATH"] = "/tmp/test_storage"
    
    service1 = get_storage_service()
    service2 = get_storage_service()
    
    # Should return the same instance (cached)
    assert service1 is service2


def test_get_database():
    """Test getting database dependency."""
    get_storage_service.cache_clear()
    os.environ["RF_TOOL_DATABASE_URL"] = "sqlite:///:memory:"
    
    db = get_database()
    assert isinstance(db, IDatabase)
    assert hasattr(db, 'create_device')


def test_get_file_storage():
    """Test getting file storage dependency."""
    get_storage_service.cache_clear()
    os.environ["RF_TOOL_STORAGE_PATH"] = "/tmp/test_storage"
    
    file_storage = get_file_storage()
    assert isinstance(file_storage, IFileStorage)
    assert hasattr(file_storage, 'store_uploaded_file')


def test_get_test_run_service():
    """Test getting test run service dependency."""
    get_storage_service.cache_clear()
    os.environ["RF_TOOL_DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["RF_TOOL_STORAGE_PATH"] = "/tmp/test_storage"
    
    service = get_test_run_service()
    assert isinstance(service, TestRunService)
    assert hasattr(service, 'process_test_run')


