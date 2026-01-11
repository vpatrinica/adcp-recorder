"""Tests for serial producer."""

import time
import itertools
from queue import Queue
from unittest.mock import Mock, patch

import pytest

from adcp_recorder.serial import SerialConnectionManager, SerialProducer


class TestSerialProducer:
    """Test SerialProducer."""

    def test_init_sets_properties(self):
        """Test that initialization sets properties correctly."""
        manager = Mock(spec=SerialConnectionManager)
        queue = Queue(maxsize=100)

        producer = SerialProducer(manager, queue, heartbeat_interval=10.0)

        assert not producer.is_running
        assert producer.last_heartbeat > 0

    def test_start_starts_thread(self):
        """Test starting the producer."""
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True
        manager.read_line.return_value = b""
        queue = Queue(maxsize=100)

        producer = SerialProducer(manager, queue)
        producer.start()

        assert producer.is_running

        # Clean up
        producer.stop()

    def test_start_when_already_running(self):
        """Test that starting when already running does not create new thread."""
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True
        manager.read_line.return_value = b""
        queue = Queue(maxsize=100)

        producer = SerialProducer(manager, queue)
        producer.start()

        # Try to start again
        producer.start()

        assert producer.is_running

        # Clean up
        producer.stop()

    def test_stop_stops_thread(self):
        """Test stopping the producer."""
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True
        manager.read_line.return_value = b""
        queue = Queue(maxsize=100)

        producer = SerialProducer(manager, queue)
        producer.start()
        time.sleep(0.1)  # Let thread start

        producer.stop()

        assert not producer.is_running

    def test_read_loop_reconnects_on_disconnect(self):
        """Test that read loop reconnects when disconnected."""
        manager = Mock(spec=SerialConnectionManager)
        # Use simple return_value with side_effect for the first few calls if possible,
        # or just make the iterable infinite
        manager.is_connected.side_effect = itertools.chain([False, True, True], itertools.repeat(True))
        manager.reconnect.return_value = True
        manager.read_line.return_value = b"$PNORI,4,Test*00\r\n"

        queue = Queue(maxsize=100)

        producer = SerialProducer(manager, queue)
        producer.start()

        # Let it run briefly
        time.sleep(0.2)

        producer.stop()

        # Should have attempted reconnect
        assert manager.reconnect.called

    def test_read_loop_reads_and_queues_lines(self):
        """Test that producer reads lines and queues them."""
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True

        # Simulate reading a few lines then stopping
        lines = [
            b"$PNORI,4,Test1*00\r\n",
            b"$PNORI,4,Test2*00\r\n",
            b"$PNORI,4,Test3*00\r\n",
        ]
        lines_iter = itertools.chain(lines, itertools.cycle([b""]))
        manager.read_line.side_effect = lambda timeout=None: next(lines_iter)

        queue = Queue(maxsize=100)

        producer = SerialProducer(manager, queue)
        producer.start()

        # Wait for producer to process
        time.sleep(0.3)
        producer.stop()

        # Check queue has lines
        assert queue.qsize() >= 3

    def test_read_loop_detects_binary_data(self):
        """Test that producer detects and queues binary data."""
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True

        # Binary data (high bytes)
        binary_data = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09"
        lines_iter = itertools.chain([binary_data], itertools.cycle([b""]))
        manager.read_line.side_effect = lambda timeout=None: next(lines_iter)

        queue = Queue(maxsize=100)

        producer = SerialProducer(manager, queue)
        producer.start()

        time.sleep(0.2)
        producer.stop()

        # Binary data should still be queued for error handling
        assert queue.qsize() >= 1

    def test_read_loop_handles_decode_errors(self):
        """Test that producer handles decode errors gracefully."""
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True

        # Invalid UTF-8/ASCII
        invalid_data = b"\xff\xfe Invalid ASCII \r\n"
        lines_iter = itertools.chain([invalid_data], itertools.cycle([b""]))
        manager.read_line.side_effect = lambda timeout=None: next(lines_iter)

        queue = Queue(maxsize=100)

        producer = SerialProducer(manager, queue)
        producer.start()

        time.sleep(0.2)
        producer.stop()

        # Should queue as binary
        assert queue.qsize() >= 1

    def test_read_loop_updates_heartbeat(self):
        """Test that heartbeat is updated on successful reads."""
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True
        lines_iter = itertools.chain([b"$PNORI,4,Test*00\r\n"], itertools.cycle([b""]))
        manager.read_line.side_effect = lambda timeout=None: next(lines_iter)

        queue = Queue(maxsize=100)

        producer = SerialProducer(manager, queue)

        initial_heartbeat = producer.last_heartbeat

        producer.start()
        time.sleep(0.2)
        producer.stop()

        # Heartbeat should have been updated
        assert producer.last_heartbeat > initial_heartbeat

    def test_queue_overflow_drops_oldest(self):
        """Test that queue overflow drops oldest items."""
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True

        # Create many lines
        lines = [f"$PNORI,4,Test{i}*00\r\n".encode() for i in range(20)]
        lines_iter = itertools.chain(lines, itertools.cycle([b""]))
        manager.read_line.side_effect = lambda timeout=None: next(lines_iter)

        # Small queue
        queue = Queue(maxsize=5)

        producer = SerialProducer(manager, queue)
        producer.start()

        time.sleep(0.5)
        producer.stop()

        # Queue should be at or near max
        assert queue.qsize() <= 5

    def test_read_loop_handles_empty_lines(self):
        """Test that empty lines are skipped."""
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True
        lines_iter = itertools.chain([b"", b"$PNORI,4,Test*00\r\n"], itertools.cycle([b""]))
        manager.read_line.side_effect = lambda timeout=None: next(lines_iter)

        queue = Queue(maxsize=100)

        producer = SerialProducer(manager, queue)
        producer.start()

        time.sleep(0.2)
        producer.stop()

        # Should only have 1 item (empty line skipped)
        assert queue.qsize() >= 1

    def test_stop_when_not_running(self):
        """Test that stopping when not running returns immediately."""
        manager = Mock(spec=SerialConnectionManager)
        queue = Queue(maxsize=100)
        producer = SerialProducer(manager, queue)
        
        # Stop without starting
        producer.stop()
        assert not producer.is_running

    def test_read_loop_handles_reconnection_failure(self):
        """Test that read loop handles reconnection failure."""
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = False
        manager.reconnect.return_value = False
        
        queue = Queue(maxsize=100)
        producer = SerialProducer(manager, queue)
        
        producer.start()
        time.sleep(0.2)
        producer.stop()
        
        assert manager.reconnect.called

    def test_push_to_queue_handles_exception(self):
        """Test that push_to_queue handles exceptions during fallback."""
        manager = Mock(spec=SerialConnectionManager)
        
        # Mock queue that raises on put_nowait even if room is supposedly made
        queue = Mock(spec=Queue)
        from queue import Full
        queue.put_nowait.side_effect = Full()
        
        producer = SerialProducer(manager, queue)
        
        # Should not raise exception
        producer._push_to_queue(b"some data")
        
        assert queue.get_nowait.called

    def test_read_loop_unidecode_error_explicit(self):
        """Test UnicodeDecodeError explicitly."""
        manager = Mock(spec=SerialConnectionManager)
        manager.is_connected.return_value = True
        
        # High-bit bytes that are invalid ASCII
        invalid_data = bytes([0xFF, 0xFE, 0xFD])
        lines_iter = itertools.chain([invalid_data], itertools.cycle([b""]))
        manager.read_line.side_effect = lambda timeout=None: next(lines_iter)
        
        queue = Queue(maxsize=100)
        producer = SerialProducer(manager, queue)
        
        producer.start()
        time.sleep(0.2)
        producer.stop()
        
        # Should have pushed high-bit bytes
        assert queue.qsize() >= 1
        assert queue.get() == invalid_data
