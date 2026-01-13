"""Common utilities and validation for NMEA parsers."""

import re
from datetime import datetime


def validate_date_mm_dd_yy(date_str: str) -> None:
    """Validate MMDDYY date string."""
    if not re.match(r"^\d{6}$", date_str):
        raise ValueError(f"Invalid date format (MMDDYY): {date_str}")
    try:
        datetime.strptime(date_str, "%m%d%y")
    except ValueError:
        raise ValueError(f"Invalid date: {date_str}")


def validate_date_yy_mm_dd(date_str: str) -> None:
    """Validate YYMMDD date string."""
    if not re.match(r"^\d{6}$", date_str):
        raise ValueError(f"Invalid date format (YYMMDD): {date_str}")
    try:
        datetime.strptime(date_str, "%y%m%d")
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


def validate_hex_string(hex_str: str, min_length: int = 1, max_length: int = 8) -> None:
    """Validate hexadecimal string within length range."""
    if not re.match(rf"^[0-9A-Fa-f]{{{min_length},{max_length}}}$", hex_str):
        raise ValueError(f"Invalid hex string: {hex_str}")


def validate_range(value: float, field_name: str, range_min: float, range_max: float) -> None:
    """Validate numeric value within range."""
    if not (range_min <= value <= range_max):
        raise ValueError(f"{field_name} out of range ({range_min} to {range_max}): {value}")


def parse_tagged_field(field_str: str) -> tuple[str, str]:
    """Parse a TAG=VALUE field.

    Returns:
        Tuple of (TAG, VALUE) normalized to uppercase tag.
    """
    if "=" not in field_str:
        raise ValueError(f"Tagged field must contain '=': {field_str}")
    tag, value = field_str.split("=", 1)
    return tag.strip().upper(), value.strip()


def parse_optional_float(
    value_str: str,
    invalid_values: tuple = ("-9.00", "-99.99", "-9.000", "-9.0000"),
) -> float | None:
    """Parse float from string, returning None for invalid indicators or empty fields."""
    if not value_str or value_str in invalid_values:
        return None
    try:
        return float(value_str)
    except ValueError:
        return None
