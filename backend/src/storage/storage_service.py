"""
Storage service that combines database and file storage.

Implements IStorageFactory interface.
"""
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from .interfaces import IDatabase, IFileStorage, IStorageFactory
from .database import create_database_engine, init_database, get_session_factory
from .sqlite_db import SQLiteDatabase
from .file_storage import FilesystemFileStorage


class StorageService(IStorageFactory):
    """Storage service factory."""
    
    def __init__(
        self,
        database_url: str = "sqlite:///rf_tool.db",
        file_storage_path: Optional[Path] = None,
    ):
        """
        Initialize storage service.
        
        Args:
            database_url: SQLAlchemy database URL
            file_storage_path: Base path for file storage (default: results/)
        """
        self.database_url = database_url
        self.file_storage_path = file_storage_path or Path("results")
        
        # Initialize database
        self.engine = create_database_engine(database_url)
        init_database(self.engine)
        self.session_factory = get_session_factory(self.engine)
    
    def create_database(self) -> IDatabase:
        """Create a database instance."""
        session = self.session_factory()
        return SQLiteDatabase(session)
    
    def create_file_storage(self) -> IFileStorage:
        """Create a file storage instance."""
        return FilesystemFileStorage(self.file_storage_path)
    
    def get_session(self) -> Session:
        """Get a database session (for advanced usage)."""
        return self.session_factory()

