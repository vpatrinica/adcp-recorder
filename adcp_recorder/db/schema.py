"""SQL schema definitions for DuckDB tables.

Defines table schemas for raw NMEA sentence storage and error tracking.
"""

# Raw lines table - stores all received NMEA sentences before parsing
RAW_LINES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_lines (
    line_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    raw_sentence TEXT NOT NULL,
    parse_status VARCHAR(10) CHECK (parse_status IN ('OK', 'FAIL', 'PENDING')),
    record_type VARCHAR(20),
    checksum_valid BOOLEAN,
    error_message TEXT
);
"""

# Create sequence for line_id
RAW_LINES_SEQUENCE_SQL = """
CREATE SEQUENCE IF NOT EXISTS raw_lines_seq START 1;
"""

# Indexes for raw_lines table
RAW_LINES_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_raw_lines_received_at ON raw_lines(received_at);",
    "CREATE INDEX IF NOT EXISTS idx_raw_lines_record_type ON raw_lines(record_type);",
    "CREATE INDEX IF NOT EXISTS idx_raw_lines_parse_status ON raw_lines(parse_status);",
]

# Parse errors table - stores sentences that failed parsing
PARSE_ERRORS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS parse_errors (
    error_id BIGINT PRIMARY KEY,
    received_at TIMESTAMP DEFAULT current_timestamp,
    raw_sentence TEXT NOT NULL,
    error_type VARCHAR(50) NOT NULL,
    error_message TEXT,
    attempted_prefix VARCHAR(20),
    checksum_expected VARCHAR(2),
    checksum_actual VARCHAR(2)
);
"""

# Create sequence for error_id
PARSE_ERRORS_SEQUENCE_SQL = """
CREATE SEQUENCE IF NOT EXISTS parse_errors_seq START 1;
"""

# Indexes for parse_errors table
PARSE_ERRORS_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_errors_received_at ON parse_errors(received_at);",
    "CREATE INDEX IF NOT EXISTS idx_errors_type ON parse_errors(error_type);",
    "CREATE INDEX IF NOT EXISTS idx_errors_prefix ON parse_errors(attempted_prefix);",
]

# All schema creation statements in order
ALL_SCHEMA_SQL = [
    RAW_LINES_SEQUENCE_SQL,
    RAW_LINES_TABLE_SQL,
    *RAW_LINES_INDEXES_SQL,
    PARSE_ERRORS_SEQUENCE_SQL,
    PARSE_ERRORS_TABLE_SQL,
    *PARSE_ERRORS_INDEXES_SQL,
]
