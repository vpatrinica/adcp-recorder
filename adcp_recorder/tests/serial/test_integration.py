"""End-to-end integration tests for serial communication."""

import time
from queue import Queue
from unittest.mock import Mock

import pytest

from adcp_recorder.db import DatabaseManager
from adcp_recorder.parsers import PNORI
from adcp_recorder.serial import (
    MessageRouter,
    SerialConnectionManager,
    SerialConsumer,
    SerialProducer,
)


class TestIntegration:
    """End-to-end integration tests."""

    @pytest.fixture
    def db_path(self, tmp_path):
        return str(tmp_path / "test_integration.db")

    def test_producer_to_consumer_pipeline(self, db_path):
        """Test complete producer -> queue -> consumer pipeline."""
        # Setup
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True

        # Provide NMEA sentences
        sentences = [
            b"$PNORI,4,Device1,4,20,0.20,1.00,0*5E\r\n",
            b"$PNORI,4,Device2,4,25,0.30,1.50,1*5D\r\n",
            b"$PNORI,4,Device3,4,30,0.40,2.00,2*5A\r\n",
        ]
        # Prevent StopIteration by feeding empty bytes after sentences exhausted
        import itertools

        manager.read_line.side_effect = itertools.chain(sentences, itertools.cycle([b""]))

        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)

        router = MessageRouter()
        router.register_parser("PNORI", PNORI)

        try:
            # Start producer and consumer
            producer = SerialProducer(manager, queue)
            consumer = SerialConsumer(queue, db, router)

            producer.start()
            consumer.start()

            # Let them run with polling
            start_time = time.time()
            max_wait = 10.0
            while time.time() - start_time < max_wait:
                conn = db.get_connection()
                count = conn.execute("SELECT count(*) FROM raw_lines").fetchone()[0]
                if count >= 3:
                    break
                time.sleep(0.1)

            # Stop
            producer.stop()
            consumer.stop()

            # Verify database
            conn = db.get_connection()
            configs = conn.execute("SELECT head_id FROM pnori ORDER BY head_id").fetchall()

            assert len(configs) >= 3
            devices = sorted([c[0] for c in configs])
            assert "Device1" in devices
            assert "Device2" in devices
            assert "Device3" in devices
        finally:
            db.close()

    def test_binary_data_end_to_end(self, db_path):
        """Test binary data handling through entire pipeline."""
        # Setup
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True

        # Provide binary data
        sentences = [
            b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09",
            None,
        ]
        import itertools

        manager.read_line.side_effect = itertools.chain(sentences, itertools.cycle([b""]))

        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)

        router = MessageRouter()

        try:
            # Start producer and consumer
            producer = SerialProducer(manager, queue)
            consumer = SerialConsumer(queue, db, router)

            producer.start()
            consumer.start()

            # Let them run
            time.sleep(0.5)

            # Stop
            producer.stop()
            consumer.stop()

            # Verify error logging
            conn = db.get_connection()
            errors = conn.execute("SELECT error_type FROM parse_errors").fetchall()

            assert len(errors) >= 1
            assert errors[0][0] == "BINARY_DATA"
        finally:
            db.close()

    def test_unknown_message_type_end_to_end(self, db_path):
        """Test unknown message type handling through entire pipeline."""
        # Setup
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True

        # Provide unknown message type
        sentences = [
            b"$UNKNOWN,1,2,3*00\r\n",
            None,
        ]
        import itertools

        manager.read_line.side_effect = itertools.chain(sentences, itertools.cycle([b""]))

        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)

        router = MessageRouter()
        # Don't register parser for UNKNOWN

        try:
            # Start producer and consumer
            producer = SerialProducer(manager, queue)
            consumer = SerialConsumer(queue, db, router)

            producer.start()
            consumer.start()

            # Let them run
            time.sleep(0.5)

            # Stop
            producer.stop()
            consumer.stop()

            # Verify raw_lines
            conn = db.get_connection()
            raw = conn.execute("SELECT parse_status, record_type FROM raw_lines").fetchone()

            assert raw is not None
            assert raw[0] == "PENDING"
            assert raw[1] == "UNKNOWN"
        finally:
            db.close()

    def test_malformed_message_end_to_end(self, db_path):
        """Test malformed message handling through entire pipeline."""
        # Setup
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True

        # Provide malformed PNORI
        sentences = [
            b"$PNORI,INVALID,DATA*FF\r\n",
            None,
        ]
        import itertools

        manager.read_line.side_effect = itertools.chain(sentences, itertools.cycle([b""]))

        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)

        router = MessageRouter()
        router.register_parser("PNORI", PNORI)

        try:
            # Start producer and consumer
            producer = SerialProducer(manager, queue)
            consumer = SerialConsumer(queue, db, router)

            producer.start()
            consumer.start()

            # Let them run
            time.sleep(0.5)

            # Stop
            producer.stop()
            consumer.stop()

            # Verify error logging
            conn = db.get_connection()
            errors = conn.execute(
                "SELECT error_type, attempted_prefix FROM parse_errors"
            ).fetchone()

            assert errors is not None
            assert errors[0] == "PARSE_ERROR"
            assert errors[1] == "PNORI"
        finally:
            db.close()

    def test_graceful_shutdown(self, db_path):
        """Test that producer and consumer shutdown gracefully."""
        # Setup
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True

        # Keep providing data
        manager.read_line.return_value = b"$PNORI,4,Test,4,20,0.20,1.00,0*2E\r\n"

        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)

        router = MessageRouter()
        router.register_parser("PNORI", PNORI)

        # Start producer and consumer
        producer = SerialProducer(manager, queue)
        consumer = SerialConsumer(queue, db, router)

        producer.start()
        consumer.start()

        # Run briefly
        time.sleep(0.2)

        # Stop both
        producer.stop()
        consumer.stop()

        # Both should be stopped
        assert not producer.is_running
        assert not consumer.is_running

    def test_heartbeat_monitoring(self, db_path):
        """Test that heartbeats are updated during operation."""
        # Setup
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True
        manager.read_line.return_value = b"$PNORI,4,Test,4,20,0.20,1.00,0*2E\r\n"

        queue = Queue(maxsize=100)
        db = DatabaseManager(db_path)

        router = MessageRouter()
        router.register_parser("PNORI", PNORI)

        # Start producer and consumer
        producer = SerialProducer(manager, queue)
        consumer = SerialConsumer(queue, db, router)

        producer_initial_hb = producer.last_heartbeat
        consumer_initial_hb = consumer.last_heartbeat
        time.sleep(0.01)

        producer.start()
        consumer.start()

        # Run
        time.sleep(0.5)

        # Stop
        producer.stop()
        consumer.stop()

        # Heartbeats should have been updated
        assert producer.last_heartbeat > producer_initial_hb
        assert consumer.last_heartbeat > consumer_initial_hb
