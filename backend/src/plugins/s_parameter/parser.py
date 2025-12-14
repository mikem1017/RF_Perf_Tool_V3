"""
Filename metadata parser for S-parameter files.

Parses metadata tokens from filenames:
- Serial number: SNxxxx, snxxxx
- Path: PRI or RED
- Part number: Lxxxxxx
- Temperature: CLD, AMB, HOT
- Date: YYYYMMDD or YYMMDD (normalized to ISO YYYY-MM-DD)

Rules:
- Case-insensitive
- Tokens can appear in any order
- Missing tokens are reported but don't cause failure
- Unknown tokens are ignored
"""
import re
from datetime import datetime
from typing import Optional
from backend.src.core.schemas.metadata import ParsedMetadata


def parse_filename_metadata(filename: str) -> ParsedMetadata:
    """
    Parse metadata from filename.
    
    Args:
        filename: Filename to parse (e.g., "SN1234_PRI_L567890_AMB_20240101.s2p")
    
    Returns:
        ParsedMetadata with extracted tokens and missing/unknown token lists
    """
    # Remove file extension for parsing
    name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
    
    # Initialize result
    serial_number: Optional[str] = None
    path: Optional[str] = None
    part_number: Optional[str] = None
    temperature: Optional[str] = None
    date_value: Optional[datetime.date] = None
    unknown_tokens: list[str] = []
    
    # Split filename into tokens (by underscore, dash, or space)
    tokens = re.split(r'[_\-\s]+', name_without_ext)
    
    # Patterns for each token type
    serial_pattern = re.compile(r'^sn(\d+)$', re.IGNORECASE)
    path_pattern = re.compile(r'^(pri|red)$', re.IGNORECASE)
    part_pattern = re.compile(r'^l(\d+)$', re.IGNORECASE)
    temp_pattern = re.compile(r'^(cld|amb|hot)$', re.IGNORECASE)
    date_pattern_yyyy = re.compile(r'^(\d{4})(\d{2})(\d{2})$')  # YYYYMMDD
    date_pattern_yy = re.compile(r'^(\d{2})(\d{2})(\d{2})$')    # YYMMDD
    
    # Process each token
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        
        matched = False
        
        # Check serial number (SNxxxx)
        match = serial_pattern.match(token)
        if match:
            serial_number = f"SN{match.group(1).zfill(4)}"  # Normalize to SN0001 format
            matched = True
        
        # Check path (PRI or RED)
        match = path_pattern.match(token)
        if match:
            path = match.group(1).upper()  # Normalize to uppercase
            matched = True
        
        # Check part number (Lxxxxxx)
        match = part_pattern.match(token)
        if match:
            part_number = f"L{match.group(1)}"
            matched = True
        
        # Check temperature (CLD, AMB, HOT)
        match = temp_pattern.match(token)
        if match:
            temperature = match.group(1).upper()  # Normalize to uppercase
            matched = True
        
        # Check date (YYYYMMDD or YYMMDD)
        match = date_pattern_yyyy.match(token)
        if match:
            try:
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                date_value = datetime(year, month, day).date()
                matched = True
            except ValueError:
                pass  # Invalid date, treat as unknown
        
        if not matched:
            # Try YYMMDD format
            match = date_pattern_yy.match(token)
            if match:
                try:
                    year_2dig = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
                    # Assume years 00-50 are 2000-2050, 51-99 are 1951-1999
                    year = 2000 + year_2dig if year_2dig <= 50 else 1900 + year_2dig
                    date_value = datetime(year, month, day).date()
                    matched = True
                except ValueError:
                    pass  # Invalid date, treat as unknown
        
        # If no pattern matched, it's an unknown token
        if not matched:
            unknown_tokens.append(token)
    
    # Determine missing tokens
    missing_tokens: list[str] = []
    if serial_number is None:
        missing_tokens.append("serial_number")
    if path is None:
        missing_tokens.append("path")
    if part_number is None:
        missing_tokens.append("part_number")
    if temperature is None:
        missing_tokens.append("temperature")
    if date_value is None:
        missing_tokens.append("date")
    
    return ParsedMetadata(
        serial_number=serial_number,
        path=path,
        part_number=part_number,
        temperature=temperature,
        date=date_value,
        missing_tokens=missing_tokens,
        unknown_tokens=unknown_tokens,
    )

