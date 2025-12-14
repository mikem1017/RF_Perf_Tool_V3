"""
Metadata parsing and effective metadata models.
"""
from __future__ import annotations

from typing import Optional, Annotated, Union
from datetime import date
from pydantic import BaseModel, Field, ConfigDict


class ParsedMetadata(BaseModel):
    """Metadata parsed from filename."""
    model_config = ConfigDict()
    
    serial_number: Optional[str] = Field(default=None, description="Serial number (SNxxxx)")
    path: Optional[str] = Field(default=None, description="Path identifier (PRI or RED)")
    part_number: Optional[str] = Field(default=None, description="Part number (Lxxxxxx)")
    temperature: Optional[str] = Field(default=None, description="Temperature (CLD, AMB, HOT)")
    date: Annotated[Optional[date], Field(default=None, description="Date in ISO format (YYYY-MM-DD)")]
    missing_tokens: list[str] = Field(default_factory=list, description="Tokens that were expected but not found")
    unknown_tokens: list[str] = Field(default_factory=list, description="Unknown tokens found in filename")


class UserOverrides(BaseModel):
    """User-provided metadata overrides."""
    model_config = ConfigDict()
    
    serial_number: Optional[str] = None
    path: Optional[str] = None
    part_number: Optional[str] = None
    temperature: Optional[str] = None
    date: Annotated[Optional[date], Field(default=None, description="Date in ISO format (YYYY-MM-DD)")]


class EffectiveMetadata(BaseModel):
    """Effective metadata (parsed + user overrides)."""
    model_config = ConfigDict()
    
    serial_number: Optional[str] = None
    path: Optional[str] = None
    part_number: Optional[str] = None
    temperature: Optional[str] = None
    date: Annotated[Optional[date], Field(default=None, description="Date in ISO format (YYYY-MM-DD)")]

    @classmethod
    def from_parsed_and_overrides(
        cls, parsed: ParsedMetadata, overrides: Optional[UserOverrides] = None
    ) -> "EffectiveMetadata":
        """Create effective metadata from parsed and optional overrides."""
        overrides = overrides or UserOverrides()
        return cls(
            serial_number=overrides.serial_number or parsed.serial_number,
            path=overrides.path or parsed.path,
            part_number=overrides.part_number or parsed.part_number,
            temperature=overrides.temperature or parsed.temperature,
            date=overrides.date or parsed.date,
        )

