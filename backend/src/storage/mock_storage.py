"""
In-memory mock storage implementations for testing.
"""
from typing import Optional, Dict, Any
from pathlib import Path
from collections import defaultdict
from .interfaces import IDatabase, IFileStorage, IStorageFactory


class MockDatabase(IDatabase):
    """In-memory mock database for testing."""
    
    def __init__(self):
        self.devices: Dict[int, dict] = {}
        self.test_stages: Dict[int, dict] = {}
        self.requirement_sets: Dict[int, dict] = {}
        self.test_runs: Dict[int, dict] = {}
        self.test_run_files: Dict[int, Dict[int, dict]] = defaultdict(dict)
        self.metrics: Dict[int, Dict[int, dict]] = defaultdict(dict)
        self.compliance: Dict[int, Dict[int, dict]] = defaultdict(dict)
        self._next_id = 1
    
    def _get_next_id(self) -> int:
        """Get next available ID."""
        id = self._next_id
        self._next_id += 1
        return id
    
    def create_device(self, device_data: dict) -> int:
        device_id = self._get_next_id()
        self.devices[device_id] = {**device_data, "id": device_id}
        return device_id
    
    def get_device(self, device_id: int) -> Optional[dict]:
        return self.devices.get(device_id)
    
    def create_test_stage(self, stage_data: dict) -> int:
        stage_id = self._get_next_id()
        self.test_stages[stage_id] = {**stage_data, "id": stage_id}
        return stage_id
    
    def get_test_stage(self, stage_id: int) -> Optional[dict]:
        return self.test_stages.get(stage_id)
    
    def create_requirement_set(self, req_set_data: dict) -> int:
        req_set_id = self._get_next_id()
        self.requirement_sets[req_set_id] = {**req_set_data, "id": req_set_id}
        return req_set_id
    
    def get_requirement_set(self, req_set_id: int) -> Optional[dict]:
        return self.requirement_sets.get(req_set_id)
    
    def create_test_run(self, test_run_data: dict) -> int:
        test_run_id = self._get_next_id()
        self.test_runs[test_run_id] = {
            **test_run_data,
            "id": test_run_id,
            "status": "created",
        }
        return test_run_id
    
    def get_test_run(self, test_run_id: int) -> Optional[dict]:
        return self.test_runs.get(test_run_id)
    
    def update_test_run_status(self, test_run_id: int, status: str, error_message: Optional[str] = None) -> None:
        if test_run_id not in self.test_runs:
            raise ValueError(f"Test run {test_run_id} not found")
        test_run = self.test_runs[test_run_id]
        current_status = test_run.get("status")
        if current_status in ("completed", "failed"):
            raise ValueError(f"Cannot update immutable test run {test_run_id}")
        test_run["status"] = status
        if error_message:
            test_run["error_message"] = error_message
    
    def add_test_run_file(self, test_run_id: int, file_data: dict) -> int:
        if test_run_id not in self.test_runs:
            raise ValueError(f"Test run {test_run_id} not found")
        file_id = self._get_next_id()
        self.test_run_files[test_run_id][file_id] = {**file_data, "id": file_id}
        return file_id
    
    def store_metrics(self, test_run_id: int, file_id: int, metrics_data: dict) -> None:
        if test_run_id not in self.test_runs:
            raise ValueError(f"Test run {test_run_id} not found")
        if file_id not in self.test_run_files[test_run_id]:
            raise ValueError(f"File {file_id} not found in test run {test_run_id}")
        self.metrics[test_run_id][file_id] = metrics_data
    
    def store_compliance(self, test_run_id: int, file_id: int, compliance_data: dict) -> None:
        if test_run_id not in self.test_runs:
            raise ValueError(f"Test run {test_run_id} not found")
        if file_id not in self.test_run_files[test_run_id]:
            raise ValueError(f"File {file_id} not found in test run {test_run_id}")
        self.compliance[test_run_id][file_id] = compliance_data


class MockFileStorage(IFileStorage):
    """In-memory mock file storage for testing."""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path("/mock/storage")
        self.files: Dict[str, bytes] = {}
        self.artifacts: Dict[str, bytes] = {}
    
    def store_uploaded_file(self, test_run_id: int, original_filename: str, file_content: bytes) -> Path:
        storage_path = self.base_path / str(test_run_id) / "inputs" / original_filename
        key = str(storage_path)
        self.files[key] = file_content
        return storage_path
    
    def get_file_path(self, test_run_id: int, filename: str) -> Optional[Path]:
        storage_path = self.base_path / str(test_run_id) / "inputs" / filename
        key = str(storage_path)
        if key in self.files:
            return storage_path
        return None
    
    def create_artifact_directory(self, test_run_id: int, artifact_type: str) -> Path:
        artifact_path = self.base_path / str(test_run_id) / "artifacts" / artifact_type
        return artifact_path
    
    def store_artifact(self, test_run_id: int, artifact_type: str, filename: str, content: bytes) -> Path:
        artifact_path = self.create_artifact_directory(test_run_id, artifact_type) / filename
        key = str(artifact_path)
        self.artifacts[key] = content
        return artifact_path
    
    def get_artifact_path(self, test_run_id: int, artifact_type: str, filename: str) -> Optional[Path]:
        artifact_path = self.base_path / str(test_run_id) / "artifacts" / artifact_type / filename
        key = str(artifact_path)
        if key in self.artifacts:
            return artifact_path
        return None


class MockStorageFactory(IStorageFactory):
    """Factory for creating mock storage instances."""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path
    
    def create_database(self) -> IDatabase:
        return MockDatabase()
    
    def create_file_storage(self) -> IFileStorage:
        return MockFileStorage(self.base_path)

