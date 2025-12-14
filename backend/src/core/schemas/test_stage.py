"""
Test stage models.
"""
from typing import Optional
from pydantic import BaseModel, Field


class TestStage(BaseModel):
    """Test stage model."""
    id: Optional[int] = Field(None, description="Test stage ID")
    name: str = Field(..., min_length=1, max_length=100, description="Test stage name")
    description: Optional[str] = Field(None, description="Test stage description")

    @classmethod
    def validate_name_format(cls, name: str) -> None:
        """Validate test stage name format (basic validation, uniqueness is storage-level)."""
        if not name or not name.strip():
            raise ValueError("Test stage name cannot be empty")
        if len(name) > 100:
            raise ValueError("Test stage name cannot exceed 100 characters")

