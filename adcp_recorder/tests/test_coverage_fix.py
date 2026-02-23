from queue import Queue
from unittest.mock import MagicMock

import pytest

from adcp_recorder.db import DatabaseManager
from adcp_recorder.db.migration import ensure_raw_lines_time_columns
from adcp_recorder.serial.consumer import MessageRouter, SerialConsumer


@pytest.fixture
def db_path(tmp_path):
    """Fixture for test database path."""
    return str(tmp_path / "test.db")


def test_consumer_datetime_parsing_value_error(db_path):
    """Test ValueError handling in datetime parsing in consumer.py (lines 467-468)."""
    db = DatabaseManager(db_path)
    router = MessageRouter()

    # Create a dummy message object that returns invalid date/time strings
    mock_parsed_obj = MagicMock()
    mock_parsed_obj.to_dict.return_value = {"date": "999999", "time": "999999"}

    # Mock the parser class
    mock_parser = MagicMock()
    mock_parser.from_nmea.return_value = mock_parsed_obj

    # Register for PNORS
    router.register_parser("PNORS", mock_parser)

    consumer = SerialConsumer(Queue(), db, router)
    conn = db.get_connection()

    # PNORS sentence with VALID checksum (4C)
    # $PNORS,999999,999999,0,0,0,0,0,0,0,0,0,0,0,0,0*4C
    sentence = "$PNORS,999999,999999,0,0,0,0,0,0,0,0,0,0,0,0,0*4C"
    line_bytes = sentence.encode("ascii")

    # Call _process_line directly
    consumer._process_line(conn, line_bytes)

    # Verify that it attempted parsing and handled the ValueErrors
    # The result should have None for measurement_datetime because parsing failed
    result = conn.execute(
        "SELECT measurement_datetime FROM raw_lines WHERE record_type = 'PNORS'"
    ).fetchone()
    assert result is not None
    assert result[0] is None

    # Confirm mock was called
    mock_parser.from_nmea.assert_called_once()
    mock_parsed_obj.to_dict.assert_called()


def test_consumer_to_dict_exception(db_path):
    """Test Exception handling in consumer.py (lines 469-470)."""
    db = DatabaseManager(db_path)
    router = MessageRouter()

    # Mock a parsed object that raises an exception in to_dict
    mock_parsed_obj = MagicMock()
    mock_parsed_obj.to_dict.side_effect = Exception("Mock exception in to_dict")

    # Mock the parser class
    mock_parser = MagicMock()
    mock_parser.from_nmea.return_value = mock_parsed_obj

    # Register for PNORS
    router.register_parser("PNORS", mock_parser)

    consumer = SerialConsumer(Queue(), db, router)
    conn = db.get_connection()

    # PNORS sentence with VALID checksum (4E)
    sentence = "$PNORS,010123,120000,0,0,0,0,0,0,0,0,0,0,0,0,0*4E"

    # Direct call
    consumer._process_line(conn, sentence.encode("ascii"))

    # Verify handled - parse_status should be OK because parsing succeeded,
    # and the exception in to_dict (for time extraction) was caught.
    # Wait, if to_dict fails in _store_parsed_message, it returns early.
    # But in _process_line, it's caught and m_dt stays None.
    result = conn.execute(
        "SELECT parse_status FROM raw_lines WHERE record_type = 'PNORS'"
    ).fetchone()
    assert result is not None
    # Note: _store_parsed_message will also fail due to the same dummy mock,
    # but that's fine for coverage of _process_line.
    assert result[0] == "OK"


def test_ensure_raw_lines_time_columns_exception():
    """Test Exception handling in migration.py (lines 526-527)."""
    mock_conn = MagicMock()

    # Success on table check, fail on column check
    def mock_execute(sql, *args):
        if "information_schema.tables" in sql:
            m = MagicMock()
            m.fetchone.return_value = [1]
            return m
        raise Exception("Mock PRAGMA failure")

    mock_conn.execute.side_effect = mock_execute

    # This should trigger the logger.warning
    mock_logger = MagicMock()
    import adcp_recorder.db.migration as migration

    original_logger = migration.logger
    migration.logger = mock_logger
    try:
        ensure_raw_lines_time_columns(mock_conn)
        # Verify warning was logged
        mock_logger.warning.assert_called()
    finally:
        migration.logger = original_logger
