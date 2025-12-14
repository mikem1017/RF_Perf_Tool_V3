"""
Tests for filename metadata parser.
"""
import pytest
from datetime import date
from backend.src.plugins.s_parameter.parser import parse_filename_metadata


def test_parse_standard_format():
    """Test parsing standard filename format."""
    result = parse_filename_metadata("SN1234_PRI_L567890_AMB_20240101.s2p")
    assert result.serial_number == "SN1234"
    assert result.path == "PRI"
    assert result.part_number == "L567890"
    assert result.temperature == "AMB"
    assert result.date == date(2024, 1, 1)
    assert len(result.missing_tokens) == 0
    assert len(result.unknown_tokens) == 0


def test_parse_case_insensitive():
    """Test case-insensitive parsing."""
    result = parse_filename_metadata("sn0001_pri_l123456_amb_20240101.s2p")
    assert result.serial_number == "SN0001"
    assert result.path == "PRI"
    assert result.part_number == "L123456"
    assert result.temperature == "AMB"


def test_parse_token_order_independence():
    """Test that token order doesn't matter."""
    result1 = parse_filename_metadata("SN1234_PRI_L567890_AMB_20240101.s2p")
    result2 = parse_filename_metadata("PRI_SN1234_AMB_L567890_20240101.s2p")
    assert result1.serial_number == result2.serial_number
    assert result1.path == result2.path
    assert result1.part_number == result2.part_number
    assert result1.temperature == result2.temperature
    assert result1.date == result2.date


def test_parse_missing_tokens():
    """Test that missing tokens are reported but don't cause failure."""
    result = parse_filename_metadata("SN1234_PRI_20240101.s2p")
    assert result.serial_number == "SN1234"
    assert result.path == "PRI"
    assert result.part_number is None
    assert result.temperature is None
    assert "part_number" in result.missing_tokens
    assert "temperature" in result.missing_tokens


def test_parse_unknown_tokens():
    """Test that unknown tokens are ignored."""
    result = parse_filename_metadata("SN1234_PRI_L567890_AMB_20240101_UNKNOWN_TOKEN.s2p")
    assert result.serial_number == "SN1234"
    # Parser splits on underscores, so "UNKNOWN_TOKEN" becomes ["UNKNOWN", "TOKEN"]
    assert "UNKNOWN" in result.unknown_tokens
    assert "TOKEN" in result.unknown_tokens
    assert len(result.unknown_tokens) == 2


def test_parse_date_yyyymmdd():
    """Test YYYYMMDD date format."""
    result = parse_filename_metadata("SN1234_PRI_L567890_AMB_20240101.s2p")
    assert result.date == date(2024, 1, 1)


def test_parse_date_yymmdd():
    """Test YYMMDD date format."""
    result = parse_filename_metadata("SN1234_PRI_L567890_AMB_240101.s2p")
    assert result.date == date(2024, 1, 1)


def test_parse_date_yymmdd_century_assumption():
    """Test YYMMDD century assumption (00-50 = 2000-2050, 51-99 = 1951-1999)."""
    result1 = parse_filename_metadata("SN1234_PRI_L567890_AMB_240101.s2p")
    assert result1.date == date(2024, 1, 1)
    
    result2 = parse_filename_metadata("SN1234_PRI_L567890_AMB_990101.s2p")
    assert result2.date == date(1999, 1, 1)


def test_parse_serial_number_normalization():
    """Test serial number normalization."""
    result1 = parse_filename_metadata("sn1_PRI_L567890_AMB_20240101.s2p")
    assert result1.serial_number == "SN0001"
    
    result2 = parse_filename_metadata("SN123_PRI_L567890_AMB_20240101.s2p")
    assert result2.serial_number == "SN0123"


def test_parse_temperature_normalization():
    """Test temperature normalization to uppercase."""
    result1 = parse_filename_metadata("SN1234_PRI_L567890_cld_20240101.s2p")
    assert result1.temperature == "CLD"
    
    result2 = parse_filename_metadata("SN1234_PRI_L567890_hot_20240101.s2p")
    assert result2.temperature == "HOT"


def test_parse_path_normalization():
    """Test path normalization to uppercase."""
    result1 = parse_filename_metadata("sn1234_pri_L567890_AMB_20240101.s2p")
    assert result1.path == "PRI"
    
    result2 = parse_filename_metadata("sn1234_red_L567890_AMB_20240101.s2p")
    assert result2.path == "RED"


def test_parse_empty_filename():
    """Test parsing empty filename."""
    result = parse_filename_metadata("")
    assert result.serial_number is None
    assert len(result.missing_tokens) == 5  # All tokens missing


def test_parse_filename_with_dashes():
    """Test parsing filename with dashes as separators."""
    result = parse_filename_metadata("SN1234-PRI-L567890-AMB-20240101.s2p")
    assert result.serial_number == "SN1234"
    assert result.path == "PRI"


def test_parse_filename_with_spaces():
    """Test parsing filename with spaces as separators."""
    result = parse_filename_metadata("SN1234 PRI L567890 AMB 20240101.s2p")
    assert result.serial_number == "SN1234"
    assert result.path == "PRI"


def test_parse_invalid_date():
    """Test that invalid dates are treated as unknown tokens."""
    result = parse_filename_metadata("SN1234_PRI_L567890_AMB_20241301.s2p")  # Invalid month 13
    assert result.date is None
    assert "20241301" in result.unknown_tokens or "date" in result.missing_tokens


def test_parse_multiple_unknown_tokens():
    """Test parsing with multiple unknown tokens."""
    result = parse_filename_metadata("SN1234_PRI_L567890_AMB_20240101_TEST1_TEST2.s2p")
    assert "TEST1" in result.unknown_tokens
    assert "TEST2" in result.unknown_tokens
    assert len(result.unknown_tokens) == 2

