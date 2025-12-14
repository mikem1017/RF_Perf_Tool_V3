"""
FastAPI dependencies for dependency injection.
"""
from pathlib import Path
from functools import lru_cache
from backend.src.storage.interfaces import IDatabase, IFileStorage
from backend.src.storage.storage_service import StorageService
from backend.src.services.test_run_service import TestRunService


@lru_cache()
def get_storage_service() -> StorageService:
    """
    Get storage service instance (cached).
    
    Uses in-memory database for testing, or file-based for production.
    """
    import os
    database_url = os.getenv("RF_TOOL_DATABASE_URL", "sqlite:///:memory:")
    file_storage_path = Path(os.getenv("RF_TOOL_STORAGE_PATH", "results"))
    
    return StorageService(
        database_url=database_url,
        file_storage_path=file_storage_path,
    )


def get_database() -> IDatabase:
    """Dependency to get database instance."""
    return get_storage_service().create_database()


def get_file_storage() -> IFileStorage:
    """Dependency to get file storage instance."""
    return get_storage_service().create_file_storage()


def get_test_run_service() -> TestRunService:
    """Dependency to get test run service."""
    storage = get_storage_service()
    return TestRunService(
        database=storage.create_database(),
        file_storage=storage.create_file_storage(),
    )


