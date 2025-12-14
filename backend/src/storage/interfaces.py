"""
Storage interfaces for dependency injection and testability.
"""
from abc import ABC, abstractmethod
from typing import Optional, Any
from pathlib import Path


class IDatabase(ABC):
    """Abstract database operations interface."""
    
    @abstractmethod
    def create_device(self, device_data: dict) -> int:
        """Create a device and return its ID."""
        pass
    
    @abstractmethod
    def get_device(self, device_id: int) -> Optional[dict]:
        """Get a device by ID."""
        pass
    
    @abstractmethod
    def create_test_stage(self, stage_data: dict) -> int:
        """Create a test stage and return its ID."""
        pass
    
    @abstractmethod
    def get_test_stage(self, stage_id: int) -> Optional[dict]:
        """Get a test stage by ID."""
        pass
    
    @abstractmethod
    def create_requirement_set(self, req_set_data: dict) -> int:
        """Create a requirement set and return its ID."""
        pass
    
    @abstractmethod
    def get_requirement_set(self, req_set_id: int) -> Optional[dict]:
        """Get a requirement set by ID."""
        pass
    
    @abstractmethod
    def create_test_run(self, test_run_data: dict) -> int:
        """Create a test run and return its ID."""
        pass
    
    @abstractmethod
    def get_test_run(self, test_run_id: int) -> Optional[dict]:
        """Get a test run by ID."""
        pass
    
    @abstractmethod
    def update_test_run_status(self, test_run_id: int, status: str, error_message: Optional[str] = None) -> None:
        """Update test run status. Raises error if test run is immutable."""
        pass
    
    @abstractmethod
    def add_test_run_file(self, test_run_id: int, file_data: dict) -> int:
        """Add a file to a test run and return file ID."""
        pass
    
    @abstractmethod
    def store_metrics(self, test_run_id: int, file_id: int, metrics_data: dict) -> None:
        """Store computed metrics for a test run file."""
        pass
    
    @abstractmethod
    def store_compliance(self, test_run_id: int, file_id: int, compliance_data: dict) -> None:
        """Store compliance results for a test run file."""
        pass


class IFileStorage(ABC):
    """Abstract file storage operations interface."""
    
    @abstractmethod
    def store_uploaded_file(self, test_run_id: int, original_filename: str, file_content: bytes) -> Path:
        """Store an uploaded file and return the storage path."""
        pass
    
    @abstractmethod
    def get_file_path(self, test_run_id: int, filename: str) -> Optional[Path]:
        """Get the path to a stored file."""
        pass
    
    @abstractmethod
    def create_artifact_directory(self, test_run_id: int, artifact_type: str) -> Path:
        """Create directory for artifacts and return the path."""
        pass
    
    @abstractmethod
    def store_artifact(self, test_run_id: int, artifact_type: str, filename: str, content: bytes) -> Path:
        """Store an artifact file and return the storage path."""
        pass
    
    @abstractmethod
    def get_artifact_path(self, test_run_id: int, artifact_type: str, filename: str) -> Optional[Path]:
        """Get the path to a stored artifact."""
        pass


class IStorageFactory(ABC):
    """Factory for creating storage instances."""
    
    @abstractmethod
    def create_database(self) -> IDatabase:
        """Create a database instance."""
        pass
    
    @abstractmethod
    def create_file_storage(self) -> IFileStorage:
        """Create a file storage instance."""
        pass

