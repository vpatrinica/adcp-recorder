"""Final coverage tests for consumer and utils."""

from queue import Queue
from typing import Any
from unittest.mock import Mock, patch

import pytest

from adcp_recorder.db import DatabaseManager
from adcp_recorder.parsers.utils import parse_nmea_sentence
from adcp_recorder.serial import MessageRouter
from adcp_recorder.serial.consumer import SerialConsumer


def test_utils_parse_nmea_invalid_checksum_logic() -> None:
    """Test validation failure logic in parse_nmea_sentence (Line 24)."""
    # Valid format ($...*CS) but invalid checksum value
    sentence = "$PNORI,1,2,3*99"
    with pytest.raises(ValueError, match="Invalid NMEA checksum"):
        parse_nmea_sentence(sentence)


def test_consumer_checksum_validation_exception() -> None:
    """Test exception handling during checksum validation in consumer (Lines 426-428)."""
    queue: Queue[Any] = Queue()
    db = DatabaseManager(":memory:")
    router = MessageRouter()
    consumer = SerialConsumer(queue, db, router)
    conn = db.get_connection()

    # We mock validate_checksum to raise ValueError to hit the specific exception handler
    with patch(
        "adcp_recorder.serial.consumer.validate_checksum", side_effect=ValueError("Bad Hex")
    ):
        # This sentence enters the `if "*" in sentence` block
        consumer._process_line(conn, b"$TEST*ZZ")

        # Verify error recorded in DB
        res = conn.execute(
            "SELECT error_type, error_message FROM parse_errors WHERE error_type='CHECKSUM_ERROR'"
        ).fetchone()

        assert res is not None
        assert res[0] == "CHECKSUM_ERROR"
        assert "Bad Hex" in res[1]


def test_consumer_db_insert_pnore() -> None:
    """Test execution of PNORE database insertion (Line 518)."""
    # This test ensures we hit the specific `elif prefix == "PNORE":` block.
    queue: Queue[Any] = Queue()
    db = DatabaseManager(":memory:")
    router = MessageRouter()
    consumer = SerialConsumer(queue, db, router)
    conn = db.get_connection()

    # Mock the parser result
    mock_parser = Mock()
    mock_parser.to_dict.return_value = {"sentence_type": "PNORE"}

    with patch("adcp_recorder.serial.consumer.insert_pnore_data") as mock_insert:
        # Call _store_parsed_message directly to bypass queue/parsing logic
        consumer._store_parsed_message(conn, "$PNORE,test", "PNORE", mock_parser)

        # Verify insert_pnore_data was called (Line 518)
        mock_insert.assert_called_once()
