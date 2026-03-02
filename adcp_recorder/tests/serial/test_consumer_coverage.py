"""Targeted coverage tests for SerialConsumer."""

import logging
from queue import Queue
from typing import Any
from unittest.mock import Mock

from adcp_recorder.serial import MessageRouter, SerialConsumer


def test_consume_loop_checkpoint_failure(caplog):
    """Test the exception path in _consume_loop when CHECKPOINT fails."""
    queue: Queue[Any] = Queue()
    # Use mocks to trigger the exception in the finally block
    mock_db_manager = Mock()
    mock_conn = Mock()
    mock_db_manager.get_connection.return_value = mock_conn

    # Configure mock_conn.execute to raise error ONLY on CHECKPOINT
    def side_effect(sql, *args, **kwargs):
        if "CHECKPOINT" in sql:
            raise Exception("Simulated checkpoint failure")
        return Mock()

    mock_conn.execute.side_effect = side_effect
    router = MessageRouter()

    consumer = SerialConsumer(queue, mock_db_manager, router)

    # We need the loop to run and then exit
    # The loop exits when self._running is False and queue is empty
    consumer.start()
    # It will immediately try to get from queue, then we stop it
    consumer.stop()

    # Check that the warning was logged
    assert any(
        "Failed to checkpoint on exit: Simulated checkpoint failure" in record.message
        for record in caplog.records
        if record.levelno == logging.WARNING
    )
