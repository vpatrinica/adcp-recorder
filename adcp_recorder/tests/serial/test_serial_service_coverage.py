import itertools
import runpy
import signal
import threading
import time
from queue import Empty, Queue
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from adcp_recorder.config import RecorderConfig
from adcp_recorder.serial.consumer import MessageRouter, SerialConsumer
from adcp_recorder.serial.producer import SerialProducer
from adcp_recorder.service.supervisor import ServiceSupervisor, main


class TestSerialServiceCoverage:
    def test_consumer_loop_exceptions(self):
        """Cover SerialConsumer._consume_loop exception handling."""
        queue = Queue()
        db_manager = MagicMock()
        router = MessageRouter()

        consumer = SerialConsumer(queue, db_manager, router)

        # Test 1: Exception during _process_line (handled inside loop)
        # We need to test the OUTER exception handler in _consume_loop.
        # This catches things that happen in the loop but outside the inner try/except block.
        # e.g. self._update_heartbeat()

        # We patch _update_heartbeat to raise TWO exceptions.
        # The loop will catch them and log error.
        # We need to stop the loop eventually.
        # We'll run it for a bit then stop.

        with patch.object(consumer, "_update_heartbeat", side_effect=Exception("Outer Error")):
            # Setup queue to unblock get()
            queue.put(b"valid_bytes")

            t = threading.Thread(target=consumer._consume_loop, daemon=True)
            consumer._running = True
            t.start()

            time.sleep(0.1)
            consumer.stop()
            t.join(timeout=1.0)
            assert not t.is_alive()

    def test_consumer_decode_error_with_file_writer(self):
        """Cover SerialConsumer decode error logging to file writer."""
        queue = Queue()
        db_manager = MagicMock()
        router = MessageRouter()
        file_writer = MagicMock()

        consumer = SerialConsumer(queue, db_manager, router, file_writer=file_writer)

        # valid non-ascii mix that passes is_binary_data but fails decode
        bad_bytes = b"A" * 100 + b"\xff"
        queue.put(bad_bytes)

        t = threading.Thread(target=consumer._consume_loop, daemon=True)
        consumer._running = True
        t.start()

        time.sleep(0.1)
        consumer.stop()
        t.join(timeout=1.0)

        assert file_writer.write_error.called
        assert "Decode error" in file_writer.write_error.call_args[0][0]

    def test_producer_unicode_decode_error_double(self):
        """Cover SerialProducer unicode decode error handling with existing blob mode."""
        manager = MagicMock()
        queue = Queue()
        producer = SerialProducer(manager, queue)

        bad_bytes = b"A" * 100 + b"\xff"

        manager.is_connected.return_value = True
        # First chunk enters blob mode. Second chunk triggers line 152 (already blob mode).
        # Use simple list + loop mechanism or itertools to avoid StopIteration
        manager.read_line.side_effect = itertools.chain(
            [bad_bytes, bad_bytes, None], itertools.repeat(None)
        )

        t = threading.Thread(target=producer._read_loop, daemon=True)
        producer._running = True
        t.start()

        time.sleep(0.1)
        producer._running = False
        t.join(timeout=1.0)

        # Check queue
        items = []
        while not queue.empty():
            items.append(queue.get())

        assert len(items) >= 2
        assert items[0].start is True
        assert items[1].start is False  # Second chunk should not have start=True

    def test_service_supervisor_stop(self):
        """Cover ServiceSupervisor stops when recorder stops."""
        config = RecorderConfig()
        with patch("adcp_recorder.service.supervisor.AdcpRecorder") as mock_cls:
            mock_recorder = mock_cls.return_value
            type(mock_recorder).is_running = PropertyMock(side_effect=[True, False])

            sup = ServiceSupervisor(config)
            sup.run()

    def test_service_supervisor_producer_check(self):
        """Cover ServiceSupervisor producer thread check."""
        config = RecorderConfig()
        with patch("adcp_recorder.service.supervisor.AdcpRecorder") as mock_cls:
            mock_recorder = mock_cls.return_value
            # Always running
            type(mock_recorder).is_running = PropertyMock(return_value=True)

            # Producer dead
            mock_recorder.producer = MagicMock()
            mock_recorder.producer.is_running = False

            sup = ServiceSupervisor(config)
            # Make sleep trigger shutdown to exit loop
            with patch(
                "adcp_recorder.service.supervisor.time.sleep",
                side_effect=lambda x: sup._shutdown_event.set(),
            ):
                with patch("adcp_recorder.service.supervisor.logger") as mock_logger:
                    sup.run()
                    mock_logger.warning.assert_any_call("Producer thread is dead!")

    def test_service_supervisor_crash_and_signal(self):
        """Cover ServiceSupervisor crash / signal / shutdown exception."""
        config = RecorderConfig()

        # Crash test
        with patch("adcp_recorder.service.supervisor.AdcpRecorder") as mock_cls:
            mock_recorder = mock_cls.return_value
            mock_recorder.start.side_effect = Exception("Crash")
            mock_recorder.stop.side_effect = Exception(
                "Stop Error"
            )  # For shutdown exception coverage

            sup = ServiceSupervisor(config)
            with pytest.raises(SystemExit):
                sup.run()

            # Signal handling coverage
            sup._handle_signal(signal.SIGTERM, None)
            assert sup._shutdown_event.is_set()

    def test_service_main(self):
        """Cover main() function execution."""
        # Use runpy to cover __name__ == "__main__" block if we wanted,
        # but main() is explicitly defined.
        with patch("adcp_recorder.service.supervisor.RecorderConfig.load"):
            with patch("adcp_recorder.service.supervisor.ServiceSupervisor") as mock_sup_cls:
                main()
                mock_sup_cls.return_value.run.assert_called_once()

    def test_consumer_loop_unknown_exception(self):
        """Cover Consumer loop generic exception handler (lines 241-242)."""
        queue = MagicMock()
        db_manager = MagicMock()
        router = MessageRouter()

        consumer = SerialConsumer(queue, db_manager, router)

        def side_effect(*args, **kwargs):
            if not getattr(side_effect, "called", False):
                side_effect.called = True
                raise Exception("Generic Queue Error")
            consumer._running = False
            raise Empty

        queue.get.side_effect = side_effect
        consumer._running = True

        with patch("adcp_recorder.serial.consumer.logger") as mock_logger:
            consumer._consume_loop()

            mock_logger.error.assert_called_with(
                "Unexpected error getting from queue: Generic Queue Error", exc_info=True
            )

    def test_supervisor_entry_point(self):
        """Cover __name__ == '__main__' block in supervisor.py."""
        # Patch time.sleep to Break the infinite loop in supervisor.run()
        # The run() method catches exceptions and calls sys.exit(1)
        with patch("time.sleep", side_effect=Exception("Break Loop")):
            with pytest.raises(SystemExit) as excinfo:
                runpy.run_module("adcp_recorder.service.supervisor", run_name="__main__")
            assert excinfo.value.code == 1
