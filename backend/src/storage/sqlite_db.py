"""
SQLite implementation of IDatabase interface.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .interfaces import IDatabase
from .models import (
    Device, TestStage, RequirementSet, TestRun, TestRunFile,
    TestRunMetrics, TestRunCompliance
)


class SQLiteDatabase(IDatabase):
    """SQLite implementation of IDatabase."""
    
    def __init__(self, session: Session):
        """
        Initialize with SQLAlchemy session.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
    
    def create_device(self, device_data: dict) -> int:
        """Create a device and return its ID."""
        device = Device(**device_data)
        self.session.add(device)
        self.session.commit()
        self.session.refresh(device)
        return device.id
    
    def get_device(self, device_id: int) -> Optional[dict]:
        """Get a device by ID."""
        device = self.session.query(Device).filter(Device.id == device_id).first()
        if device is None:
            return None
        return self._device_to_dict(device)
    
    def create_test_stage(self, stage_data: dict) -> int:
        """Create a test stage and return its ID."""
        stage = TestStage(**stage_data)
        self.session.add(stage)
        try:
            self.session.commit()
            self.session.refresh(stage)
            return stage.id
        except IntegrityError:
            self.session.rollback()
            raise ValueError(f"Test stage with name '{stage_data.get('name')}' already exists")
    
    def get_test_stage(self, stage_id: int) -> Optional[dict]:
        """Get a test stage by ID."""
        stage = self.session.query(TestStage).filter(TestStage.id == stage_id).first()
        if stage is None:
            return None
        return self._test_stage_to_dict(stage)
    
    def create_requirement_set(self, req_set_data: dict) -> int:
        """Create a requirement set and return its ID."""
        req_set = RequirementSet(**req_set_data)
        self.session.add(req_set)
        self.session.commit()
        self.session.refresh(req_set)
        return req_set.id
    
    def get_requirement_set(self, req_set_id: int) -> Optional[dict]:
        """Get a requirement set by ID."""
        req_set = self.session.query(RequirementSet).filter(RequirementSet.id == req_set_id).first()
        if req_set is None:
            return None
        return self._requirement_set_to_dict(req_set)
    
    def create_test_run(self, test_run_data: dict) -> int:
        """Create a test run and return its ID."""
        test_run = TestRun(**test_run_data)
        self.session.add(test_run)
        self.session.commit()
        self.session.refresh(test_run)
        return test_run.id
    
    def get_test_run(self, test_run_id: int) -> Optional[dict]:
        """Get a test run by ID."""
        test_run = self.session.query(TestRun).filter(TestRun.id == test_run_id).first()
        if test_run is None:
            return None
        return self._test_run_to_dict(test_run)
    
    def update_test_run_status(self, test_run_id: int, status: str, error_message: Optional[str] = None) -> None:
        """Update test run status. Raises error if test run is immutable."""
        test_run = self.session.query(TestRun).filter(TestRun.id == test_run_id).first()
        if test_run is None:
            raise ValueError(f"Test run {test_run_id} not found")
        
        # Check immutability
        if test_run.status in ("completed", "failed"):
            raise ValueError(f"Cannot update immutable test run {test_run_id}")
        
        test_run.status = status
        if error_message:
            test_run.error_message = error_message
        
        if status in ("completed", "failed"):
            from datetime import datetime, timezone
            test_run.completed_at = datetime.now(timezone.utc)
        
        self.session.commit()
    
    def add_test_run_file(self, test_run_id: int, file_data: dict) -> int:
        """Add a file to a test run and return file ID."""
        # Verify test run exists
        test_run = self.session.query(TestRun).filter(TestRun.id == test_run_id).first()
        if test_run is None:
            raise ValueError(f"Test run {test_run_id} not found")
        
        file_data["test_run_id"] = test_run_id
        file = TestRunFile(**file_data)
        self.session.add(file)
        self.session.commit()
        self.session.refresh(file)
        return file.id
    
    def store_metrics(self, test_run_id: int, file_id: int, metrics_data: dict) -> None:
        """Store computed metrics for a test run file."""
        # Verify test run and file exist
        test_run = self.session.query(TestRun).filter(TestRun.id == test_run_id).first()
        if test_run is None:
            raise ValueError(f"Test run {test_run_id} not found")
        
        file = self.session.query(TestRunFile).filter(TestRunFile.id == file_id).first()
        if file is None or file.test_run_id != test_run_id:
            raise ValueError(f"File {file_id} not found in test run {test_run_id}")
        
        # Check if metrics already exist
        existing = self.session.query(TestRunMetrics).filter(TestRunMetrics.file_id == file_id).first()
        if existing:
            existing.metrics = metrics_data["metrics"]
            existing.frequencies = metrics_data["frequencies"]
        else:
            metrics = TestRunMetrics(
                test_run_id=test_run_id,
                file_id=file_id,
                metrics=metrics_data["metrics"],
                frequencies=metrics_data["frequencies"],
            )
            self.session.add(metrics)
        
        self.session.commit()
    
    def store_compliance(self, test_run_id: int, file_id: int, compliance_data: dict) -> None:
        """Store compliance results for a test run file."""
        # Verify test run and file exist
        test_run = self.session.query(TestRun).filter(TestRun.id == test_run_id).first()
        if test_run is None:
            raise ValueError(f"Test run {test_run_id} not found")
        
        file = self.session.query(TestRunFile).filter(TestRunFile.id == file_id).first()
        if file is None or file.test_run_id != test_run_id:
            raise ValueError(f"File {file_id} not found in test run {test_run_id}")
        
        # Check if compliance already exists
        existing = self.session.query(TestRunCompliance).filter(TestRunCompliance.file_id == file_id).first()
        if existing:
            existing.overall_pass = compliance_data["overall_pass"]
            existing.requirements = compliance_data["requirements"]
            existing.failure_reasons = compliance_data.get("failure_reasons", [])
        else:
            compliance = TestRunCompliance(
                test_run_id=test_run_id,
                file_id=file_id,
                overall_pass=compliance_data["overall_pass"],
                requirements=compliance_data["requirements"],
                failure_reasons=compliance_data.get("failure_reasons", []),
            )
            self.session.add(compliance)
        
        self.session.commit()
    
    # Helper methods to convert models to dicts
    def _device_to_dict(self, device: Device) -> dict:
        """Convert Device model to dict."""
        return {
            "id": device.id,
            "name": device.name,
            "part_number": device.part_number,
            "description": device.description,
            "s_parameter_config": device.s_parameter_config,
            "created_at": device.created_at,
            "updated_at": device.updated_at,
        }
    
    def _test_stage_to_dict(self, stage: TestStage) -> dict:
        """Convert TestStage model to dict."""
        return {
            "id": stage.id,
            "name": stage.name,
            "description": stage.description,
            "created_at": stage.created_at,
            "updated_at": stage.updated_at,
        }
    
    def _requirement_set_to_dict(self, req_set: RequirementSet) -> dict:
        """Convert RequirementSet model to dict."""
        return {
            "id": req_set.id,
            "name": req_set.name,
            "test_type": req_set.test_type,
            "metric_limits": req_set.metric_limits,
            "pass_policy": req_set.pass_policy,
            "requirement_hash": req_set.requirement_hash,
            "created_at": req_set.created_at,
            "updated_at": req_set.updated_at,
        }
    
    def _test_run_to_dict(self, test_run: TestRun) -> dict:
        """Convert TestRun model to dict."""
        return {
            "id": test_run.id,
            "device_id": test_run.device_id,
            "test_stage_id": test_run.test_stage_id,
            "requirement_set_id": test_run.requirement_set_id,
            "test_type": test_run.test_type,
            "status": test_run.status,
            "error_message": test_run.error_message,
            "created_at": test_run.created_at,
            "completed_at": test_run.completed_at,
        }

