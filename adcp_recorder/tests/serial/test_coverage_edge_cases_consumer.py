import logging
import time
from queue import Queue
from unittest.mock import Mock, patch

from adcp_recorder.db.db import DatabaseManager
from adcp_recorder.serial.consumer import MessageRouter, SerialConsumer


def test_router_prefix_none():
    """Cover MessageRouter.route when extract_prefix returns None."""
    router = MessageRouter()
    # extract_prefix raises ValueError if '$' missing.
    # We must patch extract_prefix to return None to reach the line:
    # if prefix is None: return None
    with patch("adcp_recorder.serial.consumer.extract_prefix", return_value=None):
        assert router.route("$VALID,BUT,PREFIX,MISSING*00") is None


def test_consumer_stop_idempotent(tmp_path):
    """Cover SerialConsumer.stop when not running."""
    db_path = str(tmp_path / "test_stop.db")
    queue = Queue()
    db = DatabaseManager(db_path)
    router = MessageRouter()
    consumer = SerialConsumer(queue, db, router)

    # Ensuring it's not running
    assert not consumer.is_running
    # Calling stop should return early
    consumer.stop()
    assert not consumer.is_running


def test_consumer_exception_handling(tmp_path, caplog):
    """Cover exception handling in _consume_loop."""
    db_path = str(tmp_path / "test_exception.db")
    queue = Queue()
    db = DatabaseManager(db_path)
    router = MessageRouter()
    consumer = SerialConsumer(queue, db, router)

    # Mock _process_line to raise an exception
    with patch.object(consumer, "_process_line", side_effect=Exception("Forced Crash")):
        queue.put(b"$PNORI,4,Test,4,20,0.20,1.00,0*2E")
        consumer.start()
        # Wait for log
        time.sleep(0.5)
        consumer.stop()

    assert "Error processing line: Forced Crash" in caplog.text


def test_store_parsed_message_unknown_prefix(tmp_path, caplog):
    """Cover _store_parsed_message else branch."""
    db_path = str(tmp_path / "test_store.db")
    queue = Queue()
    db = DatabaseManager(db_path)
    router = MessageRouter()

    # Create a mock parser that returns a dummy object
    mock_parser = Mock()
    mock_obj = Mock()
    mock_obj.to_dict.return_value = {}
    mock_parser.from_nmea.return_value = mock_obj

    # Register "UNKNOWN_TYPE" parser
    router.register_parser("UNKNOWN_TYPE", mock_parser)

    consumer = SerialConsumer(queue, db, router)

    # Send sentence
    queue.put(b"$UNKNOWN_TYPE,1,2,3*00")

    with caplog.at_level(logging.WARNING):
        consumer.start()
        time.sleep(0.5)
        consumer.stop()

    assert "No database insert for UNKNOWN_TYPE" in caplog.text
