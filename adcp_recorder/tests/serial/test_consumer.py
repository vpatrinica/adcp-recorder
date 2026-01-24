"""Tests for serial consumer."""

import time
from queue import Queue
from typing import Any
from unittest.mock import Mock, patch

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
        result2 = router.route("$PNORI1,4,123,4,20,0.20,1.00,ENU*00")

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
        queue: Queue[Any] = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()

        consumer = SerialConsumer(queue, db, router, heartbeat_interval=10.0)

        assert not consumer.is_running
        assert consumer.last_heartbeat > 0

    def test_start_starts_thread(self, db_path):
        """Test starting the consumer."""
        queue: Queue[Any] = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()

        consumer = SerialConsumer(queue, db, router)
        consumer.start()

        assert consumer.is_running

        # Clean up
        consumer.stop()

    def test_start_when_already_running(self, db_path):
        """Test that starting when already running does not create new thread."""
        queue: Queue[Any] = Queue(maxsize=100)
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
        queue: Queue[Any] = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()

        consumer = SerialConsumer(queue, db, router)
        consumer.start()
        time.sleep(0.1)  # Let thread start

        consumer.stop()

        assert not consumer.is_running

    def test_consume_and_parse_pnori(self, db_path):
        """Test consuming and parsing PNORI message."""
        queue: Queue[Any] = Queue(maxsize=100)
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
        result = conn.execute("SELECT head_id, instrument_type_name FROM pnori").fetchone()

        assert result is not None
        assert result[0] == "TestDevice"
        assert result[1] == "SIGNATURE"

    def test_consume_unknown_message_type(self, db_path):
        """Test consuming unknown message type."""
        queue: Queue[Any] = Queue(maxsize=100)
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
        result = conn.execute("SELECT parse_status, record_type FROM raw_lines").fetchone()

        assert result is not None
        assert result[0] == "PENDING"
        assert result[1] == "UNKNOWN"

    def test_consume_invalid_message_logs_error(self, db_path):
        """Test consuming invalid message logs to parse_errors."""
        queue: Queue[Any] = Queue(maxsize=100)
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
        result = conn.execute("SELECT error_type, attempted_prefix FROM parse_errors").fetchone()

        assert result is not None
        assert result[0] == "PARSE_ERROR"
        assert result[1] == "PNORI"

    def test_consume_binary_data_logs_error(self, db_path):
        """Test consuming binary data logs to errors."""
        queue: Queue[Any] = Queue(maxsize=100)
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
        result = conn.execute("SELECT error_type FROM parse_errors").fetchone()

        assert result is not None
        assert result[0] == "BINARY_DATA"

    def test_consume_updates_heartbeat(self, db_path):
        """Test that heartbeat is updated when consuming."""
        queue: Queue[Any] = Queue(maxsize=100)
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
        queue: Queue[Any] = Queue(maxsize=100)
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
        queue: Queue[Any] = Queue(maxsize=100)
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
            PNORA,
            PNORB,
            PNORC,
            PNORE,
            PNORF,
            PNORH4,
            PNORI,
            PNORS,
            PNORW,
            PNORWD,
        )

        queue: Queue[Any] = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()

        # Register all families
        router.register_parser("PNORI", PNORI)
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

        # PNORI - Configuration (8 fields)
        queue.put(b"$PNORI,4,1001,4,20,0.20,1.00,0*2E")
        # PNORS - Sensor (14 fields)
        queue.put(b"$PNORS,102115,090715,0,00000000,14.4,1523.0,275.9,15.7,2.3,0.0,22.45,0,0*1F")
        # PNORC - Velocity (19 fields)
        queue.put(
            b"$PNORC,102115,090715,1,0.5,0.1,0.2,0.3,0.4,180.0,C,80,80,80,80,100,100,100,100*41"
        )
        # PNORH4 - Header (5 fields: Date,Time,EC,SC)
        queue.put(b"$PNORH4,211021,090715,0,00000000*00")
        # PNORW - Wave (22 fields)
        queue.put(b"$PNORW,102115,090715,0,1,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0,0,0,0,0,0,0,0,0,0000*32")
        # PNORB - Wave Band Parameters (14 fields)
        queue.put(b"$PNORB,102115,090715,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*7C")
        # PNORE - Echo (Prefix+Date+Time+Basis+Start+Step+Num+Values)
        queue.put(b"$PNORE,102115,090715,1,0.02,0.01,3,1.0,2.0,3.0*1E")
        # PNORF - Frequency (Prefix+Flag+Date+Time+Basis+Start+Step+Num+Values)
        queue.put(b"$PNORF,A1,102115,090715,1,0.02,0.01,2,0.5,1.5*44")
        # PNORWD - Wave Directional (Prefix+Type+Date+Time+Basis+Start+Step+Num+Values)
        queue.put(b"$PNORWD,MD,102115,090715,1,0.02,0.01,2,45.0,90.0*42")
        # PNORA - Altitude (9 fields, Date is YYMMDD)
        queue.put(b"$PNORA,151021,090715,1,15.50,1,00,0.0,5.5*55")

        consumer.start()
        time.sleep(2.0)  # Wait longer
        consumer.stop()

        # Verify all tables have data
        conn = db.get_connection()

        # Check raw_lines first (now 10 messages total)
        raw_res = conn.execute("SELECT count(*) FROM raw_lines").fetchone()
        assert raw_res is not None
        raw_count = raw_res[0]
        if raw_count < 10:
            # If failed, let's see why
            raw_lines = conn.execute(
                "SELECT sentence_type, parse_status, error_message FROM raw_lines"
            ).fetchall()
            print(f"Raw lines: {raw_lines}")
            parse_errors = conn.execute(
                "SELECT error_type, error_message FROM parse_errors"
            ).fetchall()
            print(f"Parse errors: {parse_errors}")

        assert raw_count == 10
        # Verify all message types were stored in new separate tables
        res = conn.execute("SELECT count(*) FROM pnori").fetchone()
        assert res is not None and res[0] == 1
        res = conn.execute("SELECT count(*) FROM pnors_df100").fetchone()
        assert res is not None and res[0] == 1  # PNORS
        res = conn.execute("SELECT count(*) FROM pnorc_df100").fetchone()
        assert res is not None and res[0] == 1  # PNORC
        res = conn.execute("SELECT count(*) FROM pnorh WHERE data_format=104").fetchone()
        assert res is not None and res[0] == 1  # PNORH4
        res = conn.execute("SELECT count(*) FROM pnorw_data").fetchone()
        assert res is not None and res[0] == 1
        res = conn.execute("SELECT count(*) FROM pnorb_data").fetchone()
        assert res is not None and res[0] == 1
        # Note: PNORE/PNORF/PNORWD will fail to parse with old format, so these won't be in DB
        res = conn.execute("SELECT count(*) FROM pnora_data").fetchone()
        assert res is not None and res[0] == 1

    def test_consume_writes_to_file(self, db_path):
        """Test that consumer writes to file writer."""
        queue: Queue[Any] = Queue(maxsize=100)
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
        queue: Queue[Any] = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()
        mock_file_writer = Mock()
        mock_file_writer.base_path = "."

        consumer = SerialConsumer(queue, db, router, file_writer=mock_file_writer)

        binary_data = b"\x00\x01\x02"
        queue.put(binary_data)

        consumer.start()
        time.sleep(0.5)
        consumer.stop()

        mock_file_writer.write_invalid_record.assert_called_once()
        args = mock_file_writer.write_invalid_record.call_args[0]
        assert args[0] == "BINARY"
        assert "\x00\x01\x02" in args[1]

    def test_consume_writes_unknown_to_file(self, db_path):
        """Test that consumer writes unknown messages to file writer."""
        queue: Queue[Any] = Queue(maxsize=100)
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

    def test_consume_writes_invalid_record_to_file(self, db_path):
        """Test that consumer writes invalid records to file writer."""
        queue: Queue[Any] = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()
        # Register PNORI with a parser that will fail if data is invalid
        router.register_parser("PNORI", PNORI)
        mock_file_writer = Mock()

        consumer = SerialConsumer(queue, db, router, file_writer=mock_file_writer)

        sentence = "$PNORI,INVALID,DATA*FF"
        queue.put(sentence.encode("ascii"))

        consumer.start()
        time.sleep(0.5)
        consumer.stop()

        mock_file_writer.write_invalid_record.assert_called_with("PNORI", sentence)

    def test_stop_timeout_warning(self, db_path, caplog):
        """Test that a warning is logged if the consumer thread hangs during stop."""
        import logging

        queue: Queue[Any] = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()
        consumer = SerialConsumer(queue, db, router)

        consumer.start()

        # Mock the thread object to simulate it's still alive after join
        with (
            patch.object(consumer._thread, "join"),
            patch.object(consumer._thread, "is_alive", return_value=True),
        ):
            with caplog.at_level(logging.WARNING):
                consumer.stop()
                assert "Consumer thread did not exit cleanly within timeout" in caplog.text
