"""DuckDB backend for NMEA data storage.

This package provides database management, schema definitions, and operations
for persisting NMEA telemetry data in DuckDB.
"""

from .db import DatabaseManager
from .operations import (
    insert_raw_line,
    batch_insert_raw_lines,
    insert_parse_error,
    update_raw_line_status,
    query_raw_lines,
    query_parse_errors,
)

__all__ = [
    "DatabaseManager",
    "insert_raw_line",
    "batch_insert_raw_lines",
    "insert_parse_error",
    "update_raw_line_status",
    "query_raw_lines",
    "query_parse_errors",
]
