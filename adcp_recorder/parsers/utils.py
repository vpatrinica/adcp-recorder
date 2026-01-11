"""Common utilities and validation for NMEA parsers.
"""

import re
from datetime import datetime


def validate_date_string(date_str: str) -> None:
    """Validate MMDDYY date string."""
    if not re.match(r"^\d{6}$", date_str):
        raise ValueError(f"Invalid date format (MMDDYY): {date_str}")
    try:
        datetime.strptime(date_str, "%m%d%y")
    except ValueError:
        raise ValueError(f"Invalid date: {date_str}")


def validate_time_string(time_str: str) -> None:
    """Validate HHMMSS time string."""
    if not re.match(r"^\d{6}$", time_str):
        raise ValueError(f"Invalid time format (HHMMSS): {time_str}")
    try:
        datetime.strptime(time_str, "%H%M%S")
    except ValueError:
        raise ValueError(f"Invalid time: {time_str}")


def validate_hex_string(hex_str: str, length: int = 8) -> None:
    """Validate hexadecimal string of exact length."""
    if not re.match(rf"^[0-9A-Fa-f]{{{length}}}$", hex_str):
        raise ValueError(f"Invalid hex string (expected {length} chars): {hex_str}")


def validate_range(value: float, field_name: str, range_min: float, range_max: float) -> None:
    """Validate numeric value within range."""
    if not (range_min <= value <= range_max):
        raise ValueError(f"{field_name} out of range ({range_min} to {range_max}): {value}")
