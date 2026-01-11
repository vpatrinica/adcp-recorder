"""Tests for serial consumer."""

import time
from queue import Queue
from unittest.mock import Mock

import pytest

from adcp_recorder.db import DatabaseManager
from adcp_recorder.parsers import PNORI, PNORI1
from adcp_recorder.serial import MessageRouter, SerialConsumer


class TestMessageRouter:
    """Test MessageRouter."""

    def test_init_creates_empty_registry(self):
        """Test that router initializes with empty registry."""
        router = MessageRouter()
        # Router should be able to handle unknown prefix
        result = router.route("$UNKNOWN,1,2,3*00")
        assert result is None

    def test_register_parser(self):
        """Test registering a parser."""
        router = MessageRouter()
        router.register_parser("PNORI", PNORI)

        # Should now be able to route PNORI
        result = router.route("$PNORI,4,Test123,4,20,0.20,1.00,0*00")
        assert result is not None
        assert isinstance(result, PNORI)

    def test_register_multiple_parsers(self):
        """Test registering multiple parsers."""
        router = MessageRouter()
        router.register_parser("PNORI", PNORI)
        router.register_parser("PNORI1", PNORI1)

        # Should route to correct parser
        result1 = router.route("$PNORI,4,Test,4,20,0.20,1.00,0*00")
        result2 = router.route("$PNORI1,4,Test,4,20,0.20,1.00,ENU*00")

        assert isinstance(result1, PNORI)
        assert isinstance(result2, PNORI1)

    def test_route_unknown_prefix_returns_none(self):
        """Test that unknown prefix returns None."""
        router = MessageRouter()
        router.register_parser("PNORI", PNORI)

        result = router.route("$UNKNOWN,1,2,3*00")
        assert result is None

    def test_route_invalid_sentence_raises_error(self):
        """Test that invalid sentence raises ValueError."""
        router = MessageRouter()
        router.register_parser("PNORI", PNORI)

        with pytest.raises(ValueError):
            router.route("$PNORI,INVALID,DATA*00")

    def test_route_uppercase_prefix(self):
        """Test that routing works with uppercase prefix."""
        router = MessageRouter()
        router.register_parser("PNORI", PNORI)

        # Uppercase prefix
        result = router.route("$PNORI,4,Test,4,20,0.20,1.00,0*00")
        assert isinstance(result, PNORI)


class TestSerialConsumer:
    """Test SerialConsumer."""

    @pytest.fixture
    def db_path(self, tmp_path):
        return str(tmp_path / "test_consumer.db")

    def test_init_sets_properties(self, db_path):
        """Test that initialization sets properties correctly."""
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()

        consumer = SerialConsumer(queue, db, router, heartbeat_interval=10.0)

        assert not consumer.is_running
        assert consumer.last_heartbeat > 0

    def test_start_starts_thread(self, db_path):
        """Test starting the consumer."""
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()

        consumer = SerialConsumer(queue, db, router)
        consumer.start()

        assert consumer.is_running

        # Clean up
        consumer.stop()

    def test_start_when_already_running(self, db_path):
        """Test that starting when already running does not create new thread."""
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()

        consumer = SerialConsumer(queue, db, router)
        consumer.start()

        # Try to start again
        consumer.start()

        assert consumer.is_running

        # Clean up
        consumer.stop()

    def test_stop_stops_thread(self, db_path):
        """Test stopping the consumer."""
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()

        consumer = SerialConsumer(queue, db, router)
        consumer.start()
        time.sleep(0.1)  # Let thread start

        consumer.stop()

        assert not consumer.is_running

    def test_consume_and_parse_pnori(self, db_path):
        """Test consuming and parsing PNORI message."""
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()
        router.register_parser("PNORI", PNORI)

        consumer = SerialConsumer(queue, db, router)

        # Add message to queue
        sentence = "$PNORI,4,TestDevice,4,20,0.20,1.00,0*2E"
        queue.put(sentence.encode("ascii"))

        consumer.start()
        time.sleep(0.5)  # Let consumer process
        consumer.stop()

        # Check database for parsed configuration
        conn = db.get_connection()
        result = conn.execute(
            "SELECT head_id, instrument_type_name FROM pnori_configurations"
        ).fetchone()

        assert result is not None
        assert result[0] == "TestDevice"
        assert result[1] == "SIGNATURE"

    def test_consume_unknown_message_type(self, db_path):
        """Test consuming unknown message type."""
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()
        # Don't register any parsers

        consumer = SerialConsumer(queue, db, router)

        # Add unknown message
        sentence = "$UNKNOWN,1,2,3*00"
        queue.put(sentence.encode("ascii"))

        consumer.start()
        time.sleep(0.5)
        consumer.stop()

        # Check raw_lines for PENDING status
        conn = db.get_connection()
        result = conn.execute(
            "SELECT parse_status, record_type FROM raw_lines"
        ).fetchone()

        assert result is not None
        assert result[0] == "PENDING"
        assert result[1] == "UNKNOWN"

    def test_consume_invalid_message_logs_error(self, db_path):
        """Test consuming invalid message logs to parse_errors."""
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()
        router.register_parser("PNORI", PNORI)

        consumer = SerialConsumer(queue, db, router)

        # Add invalid PNORI message
        sentence = "$PNORI,INVALID,DATA*FF"
        queue.put(sentence.encode("ascii"))

        consumer.start()
        time.sleep(0.5)
        consumer.stop()

        # Check parse_errors table
        conn = db.get_connection()
        result = conn.execute(
            "SELECT error_type, attempted_prefix FROM parse_errors"
        ).fetchone()

        assert result is not None
        assert result[0] == "PARSE_ERROR"
        assert result[1] == "PNORI"

    def test_consume_binary_data_logs_error(self, db_path):
        """Test consuming binary data logs to errors."""
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()

        consumer = SerialConsumer(queue, db, router)

        # Add binary data
        binary_data = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09"
        queue.put(binary_data)

        consumer.start()
        time.sleep(0.5)
        consumer.stop()

        # Check parse_errors for binary data
        conn = db.get_connection()
        result = conn.execute(
            "SELECT error_type FROM parse_errors"
        ).fetchone()

        assert result is not None
        assert result[0] == "BINARY_DATA"

    def test_consume_updates_heartbeat(self, db_path):
        """Test that heartbeat is updated when consuming."""
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()
        router.register_parser("PNORI", PNORI)

        consumer = SerialConsumer(queue, db, router)

        initial_heartbeat = consumer.last_heartbeat
        time.sleep(0.01)

        # Add message
        sentence = "$PNORI,4,Test,4,20,0.20,1.00,0*2E"
        queue.put(sentence.encode("ascii"))

        consumer.start()
        time.sleep(0.5)
        consumer.stop()

        # Heartbeat should have been updated
        assert consumer.last_heartbeat > initial_heartbeat

    def test_consume_empty_queue_continues(self, db_path):
        """Test that empty queue doesn't crash consumer."""
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()

        consumer = SerialConsumer(queue, db, router)

        consumer.start()
        time.sleep(0.2)  # Run with empty queue
        consumer.stop()

        # Should exit cleanly
        assert not consumer.is_running

    def test_consume_no_prefix_logs_error(self, db_path):
        """Test that message without prefix logs error."""
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()

        consumer = SerialConsumer(queue, db, router)

        # Add message without NMEA prefix
        sentence = "NOT_A_NMEA_SENTENCE"
        queue.put(sentence.encode("ascii"))

        consumer.start()
        time.sleep(0.5)
        consumer.stop()

        # Check raw_lines for FAIL status
        conn = db.get_connection()
        result = conn.execute("SELECT parse_status FROM raw_lines").fetchone()

        assert result is not None
        assert result[0] == "FAIL"

    def test_consume_all_phase2_message_families(self, db_path):
        """Test consuming and storing different message families."""
        from adcp_recorder.parsers import (
            PNORS, PNORC, PNORH4, PNORW,
            PNORB, PNORE, PNORF, PNORWD, PNORA
        )
        
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()
        
        # Register all families
        router.register_parser("PNORS", PNORS)
        router.register_parser("PNORC", PNORC)
        router.register_parser("PNORH4", PNORH4)
        router.register_parser("PNORW", PNORW)
        router.register_parser("PNORB", PNORB)
        router.register_parser("PNORE", PNORE)
        router.register_parser("PNORF", PNORF)
        router.register_parser("PNORWD", PNORWD)
        router.register_parser("PNORA", PNORA)
        
        consumer = SerialConsumer(queue, db, router)
        
        # PNORS - Sensor
        queue.put(b"$PNORS,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,2.3,0.0,22.45,0,0*1F")
        # PNORC - Velocity
        queue.put(b"$PNORC,102115,090715,1,0.123,-0.456,0.012*1B")
        # PNORH4 - Header
        queue.put(b"$PNORH4,102115,090715,20,1,50,ENU,60.0*45")
        # PNORW - Wave
        queue.put(b"$PNORW,102115,090715,2.5,4.1,8.5,285.0*38")
        # PNORB - Bottom Track
        queue.put(b"$PNORB,102115,090715,0.1,0.2,0.05,25.5,95*7C")
        # PNORE - Echo
        queue.put(b"$PNORE,102115,090715,1,50,60,70,80*45")
        # PNORF - Frequency
        queue.put(b"$PNORF,102115,090715,1000.0,25.0,90.0*4B")
        # PNORWD - Wave Directional
        queue.put(b"$PNORWD,102115,090715,10,180.0,20.0,50.0*5C")
        # PNORA - Altitude
        queue.put(b"$PNORA,102115,090715,1,15.50,95*45")
        
        consumer.start()
        time.sleep(2.0)  # Wait longer
        consumer.stop()
        
        # Verify all tables have data
        conn = db.get_connection()
        
        # Check raw_lines first (4 existing + 5 new = 9)
        raw_count = conn.execute("SELECT count(*) FROM raw_lines").fetchone()[0]
        if raw_count < 9:
            # If failed, let's see why
            raw_lines = conn.execute("SELECT sentence_type, parse_status, error_message FROM raw_lines").fetchall()
            print(f"Raw lines: {raw_lines}")
            parse_errors = conn.execute("SELECT error_type, error_message FROM parse_errors").fetchall()
            print(f"Parse errors: {parse_errors}")

        assert raw_count == 9
        assert conn.execute("SELECT count(*) FROM sensor_data").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM velocity_data").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM header_data").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM pnorw_data").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM pnorb_data").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM echo_data").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM pnorf_data").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM pnorwd_data").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM pnora_data").fetchone()[0] == 1

    def test_consume_writes_to_file(self, db_path):
        """Test that consumer writes to file writer."""
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()
        router.register_parser("PNORI", PNORI)
        mock_file_writer = Mock()

        consumer = SerialConsumer(queue, db, router, file_writer=mock_file_writer)

        sentence = "$PNORI,4,Test,4,20,0.20,1.00,0*2E"
        queue.put(sentence.encode("ascii"))

        consumer.start()
        time.sleep(0.5)
        consumer.stop()

        mock_file_writer.write.assert_called_with("PNORI", sentence)

    def test_consume_writes_binary_errors_to_file(self, db_path):
        """Test that consumer writes binary errors to file writer."""
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()
        mock_file_writer = Mock()

        consumer = SerialConsumer(queue, db, router, file_writer=mock_file_writer)

        binary_data = b"\x00\x01\x02"
        queue.put(binary_data)

        consumer.start()
        time.sleep(0.5)
        consumer.stop()

        mock_file_writer.write.assert_called_once()
        args = mock_file_writer.write.call_args[0]
        assert args[0] == "ERRORS"
        assert "\x00\x01\x02" in args[1]
    
    def test_consume_writes_unknown_to_file(self, db_path):
        """Test that consumer writes unknown messages to file writer."""
        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()
        mock_file_writer = Mock()
        
        consumer = SerialConsumer(queue, db, router, file_writer=mock_file_writer)
        
        sentence = "$UNKNOWN,1,2*00"
        queue.put(sentence.encode("ascii"))
        
        consumer.start()
        time.sleep(0.5)
        consumer.stop()
        
        mock_file_writer.write.assert_called_with("UNKNOWN", sentence)
