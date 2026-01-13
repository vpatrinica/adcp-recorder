"""Core NMEA protocol utilities."""

from .enums import CoordinateSystem, InstrumentType
from .nmea import (
    compute_checksum,
    extract_prefix,
    is_binary_data,
    split_sentence,
    validate_checksum,
)

__all__ = [
    "compute_checksum",
    "validate_checksum",
    "extract_prefix",
    "split_sentence",
    "is_binary_data",
    "InstrumentType",
    "CoordinateSystem",
]
