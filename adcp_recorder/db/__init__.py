"""DuckDB backend for NMEA data storage.

This package provides database management, schema definitions, and operations
for persisting NMEA telemetry data in DuckDB.
"""

from .db import DatabaseManager
from .migration import migrate_database
from .operations import (
    batch_insert_raw_lines,
    expand_coefficients,
    expand_energy_densities,
    expand_pnorwd_values,
    insert_echo_data,  # Backwards compatibility alias
    insert_header_data,
    insert_parse_error,
    insert_pnora_data,
    insert_pnorb_data,
    insert_pnore_data,
    insert_pnorf_data,
    insert_pnori_configuration,
    insert_pnorw_data,
    insert_pnorwd_data,
    insert_raw_line,
    insert_sensor_data,
    insert_velocity_data,
    query_echo_data,  # Backwards compatibility alias
    query_header_data,
    query_parse_errors,
    query_pnora_data,
    query_pnorb_data,
    query_pnore_data,
    query_pnorf_data,
    query_pnori_configurations,
    query_pnorw_data,
    query_pnorwd_data,
    query_raw_lines,
    query_sensor_data,
    query_velocity_data,
    update_raw_line_status,
)

__all__ = [
    "DatabaseManager",
    "insert_raw_line",
    "batch_insert_raw_lines",
    "insert_parse_error",
    "update_raw_line_status",
    "query_raw_lines",
    "query_parse_errors",
    "insert_pnori_configuration",
    "query_pnori_configurations",
    "insert_sensor_data",
    "query_sensor_data",
    "insert_velocity_data",
    "query_velocity_data",
    "insert_header_data",
    "query_header_data",
    "insert_pnorw_data",
    "query_pnorw_data",
    "insert_pnorb_data",
    "query_pnorb_data",
    "insert_pnorf_data",
    "query_pnorf_data",
    "insert_pnorwd_data",
    "query_pnorwd_data",
    "insert_pnora_data",
    "query_pnora_data",
    "insert_pnore_data",
    "query_pnore_data",
    "insert_echo_data",  # Backwards compatibility alias
    "query_echo_data",  # Backwards compatibility alias
    "expand_energy_densities",
    "expand_coefficients",
    "expand_pnorwd_values",
    "migrate_database",
]
