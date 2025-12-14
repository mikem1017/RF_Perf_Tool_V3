"""
Filesystem file storage implementation.
"""
from pathlib import Path
from typing import Optional
from .interfaces import IFileStorage


class FilesystemFileStorage(IFileStorage):
    """Filesystem implementation of IFileStorage."""
    
    def __init__(self, base_path: Path):
        """
        Initialize filesystem storage.
        
        Args:
            base_path: Base path for storing files (e.g., Path("results"))
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def store_uploaded_file(self, test_run_id: int, original_filename: str, file_content: bytes) -> Path:
        """Store an uploaded file and return the storage path."""
        storage_dir = self.base_path / str(test_run_id) / "inputs"
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        storage_path = storage_dir / original_filename
        storage_path.write_bytes(file_content)
        
        return storage_path
    
    def get_file_path(self, test_run_id: int, filename: str) -> Optional[Path]:
        """Get the path to a stored file."""
        storage_path = self.base_path / str(test_run_id) / "inputs" / filename
        if storage_path.exists():
            return storage_path
        return None
    
    def create_artifact_directory(self, test_run_id: int, artifact_type: str) -> Path:
        """Create directory for artifacts and return the path."""
        artifact_path = self.base_path / str(test_run_id) / "artifacts" / artifact_type
        artifact_path.mkdir(parents=True, exist_ok=True)
        return artifact_path
    
    def store_artifact(self, test_run_id: int, artifact_type: str, filename: str, content: bytes) -> Path:
        """Store an artifact file and return the storage path."""
        artifact_path = self.create_artifact_directory(test_run_id, artifact_type)
        file_path = artifact_path / filename
        file_path.write_bytes(content)
        return file_path
    
    def get_artifact_path(self, test_run_id: int, artifact_type: str, filename: str) -> Optional[Path]:
        """Get the path to a stored artifact."""
        artifact_path = self.base_path / str(test_run_id) / "artifacts" / artifact_type / filename
        if artifact_path.exists():
            return artifact_path
        return None

