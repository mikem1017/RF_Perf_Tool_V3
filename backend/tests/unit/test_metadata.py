"""
Tests for metadata schemas.
"""
import pytest
from datetime import date
from backend.src.core.schemas.metadata import ParsedMetadata, UserOverrides, EffectiveMetadata


def test_parsed_metadata_creation():
    """Test creating ParsedMetadata."""
    parsed = ParsedMetadata(
        serial_number="SN1234",
        path="PRI",
        part_number="L567890",
        temperature="AMB",
        date=date(2024, 1, 1),
    )
    assert parsed.serial_number == "SN1234"
    assert parsed.path == "PRI"
    assert parsed.date == date(2024, 1, 1)


def test_parsed_metadata_missing_tokens():
    """Test ParsedMetadata with missing tokens."""
    parsed = ParsedMetadata(
        serial_number="SN1234",
        missing_tokens=["part_number", "temperature"],
    )
    assert "part_number" in parsed.missing_tokens
    assert "temperature" in parsed.missing_tokens


def test_effective_metadata_from_parsed_only():
    """Test creating EffectiveMetadata from parsed only."""
    parsed = ParsedMetadata(
        serial_number="SN1234",
        path="PRI",
        part_number="L567890",
    )
    effective = EffectiveMetadata.from_parsed_and_overrides(parsed)
    assert effective.serial_number == "SN1234"
    assert effective.path == "PRI"
    assert effective.part_number == "L567890"


def test_effective_metadata_with_overrides():
    """Test creating EffectiveMetadata with user overrides."""
    parsed = ParsedMetadata(
        serial_number="SN1234",
        path="PRI",
        part_number="L567890",
    )
    overrides = UserOverrides(
        serial_number="SN9999",
        path="RED",
    )
    effective = EffectiveMetadata.from_parsed_and_overrides(parsed, overrides)
    # Overrides take precedence
    assert effective.serial_number == "SN9999"
    assert effective.path == "RED"
    # Non-overridden values come from parsed
    assert effective.part_number == "L567890"


def test_effective_metadata_override_none():
    """Test that None overrides don't replace parsed values."""
    parsed = ParsedMetadata(
        serial_number="SN1234",
        path="PRI",
    )
    overrides = UserOverrides(
        serial_number=None,  # Explicit None should not override
    )
    effective = EffectiveMetadata.from_parsed_and_overrides(parsed, overrides)
    assert effective.serial_number == "SN1234"  # Should keep parsed value

