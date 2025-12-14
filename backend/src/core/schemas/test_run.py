"""
Test run models.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timezone
from .metadata import EffectiveMetadata


class TestRunStatus(BaseModel):
    """Test run status."""
    status: Literal["created", "uploaded", "processing", "completed", "failed"] = Field(
        default="created", description="Test run status"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")


class TestRunFile(BaseModel):
    """Test run file model."""
    id: Optional[int] = Field(None, description="File ID")
    original_filename: str = Field(..., description="Original filename")
    stored_path: str = Field(..., description="Filesystem path to stored file")
    effective_metadata: EffectiveMetadata = Field(..., description="Effective metadata")


class TestRun(BaseModel):
    """Test run model (immutable record)."""
    id: Optional[int] = Field(None, description="Test run ID")
    device_id: int = Field(..., description="Device ID")
    test_stage_id: int = Field(..., description="Test stage ID")
    requirement_set_id: int = Field(..., description="Requirement set ID")
    test_type: str = Field(..., description="Test type")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    tool_version: Optional[str] = Field(None, description="Tool version")
    requirement_hash: Optional[str] = Field(None, description="Requirement set hash for traceability")
    status: TestRunStatus = Field(default_factory=TestRunStatus, description="Test run status")
    files: list[TestRunFile] = Field(default_factory=list, description="Uploaded files")

    def is_completed(self) -> bool:
        """Check if test run is completed."""
        return self.status.status == "completed"

    def is_immutable(self) -> bool:
        """Check if test run is immutable (completed or failed)."""
        return self.status.status in ("completed", "failed")

