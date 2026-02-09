"""Resilience tests for serial consumer."""

import time
from queue import Queue
from typing import Any
from unittest.mock import Mock, patch

import pytest

from adcp_recorder.db import DatabaseManager
from adcp_recorder.parsers import PNORB
from adcp_recorder.serial import MessageRouter, SerialConsumer


class TestConsumerResilience:
    @pytest.fixture
    def db_path(self, tmp_path):
        return str(tmp_path / "test_resilience.db")

    def test_parquet_failure_does_not_block_db(self, db_path):
        """Test that a failure in Parquet export does not block Database insertion."""
        queue: Queue[Any] = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()
        router.register_parser("PNORB", PNORB)

        # Mock file writer that fails on write_record
        mock_file_writer = Mock()
        mock_file_writer.write_record.side_effect = Exception("Parquet export failed")
        mock_file_writer.base_path = "."

        consumer = SerialConsumer(queue, db, router, file_writer=mock_file_writer)

        # Add valid PNORB message
        sentence = "$PNORB,102115,090715,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*7C"
        queue.put(sentence.encode("ascii"))

        consumer.start()
        time.sleep(0.5)
        consumer.stop()

        # Check database - it should HAVE the data despite Parquet failure
        conn = db.get_connection()
        result = conn.execute("SELECT hm0 FROM pnorb_data").fetchone()
        assert result is not None
        assert float(result[0]) == pytest.approx(0.27)

    def test_db_failure_does_not_block_parquet(self, db_path):
        """Test that a failure in Database insertion does not block Parquet export."""
        from unittest.mock import ANY

        queue: Queue[Any] = Queue(maxsize=100)
        db = DatabaseManager(db_path)
        router = MessageRouter()
        router.register_parser("PNORB", PNORB)

        mock_file_writer = Mock()
        mock_file_writer.base_path = "."

        consumer = SerialConsumer(queue, db, router, file_writer=mock_file_writer)

        # Mock database insertion to fail - specifically insert_pnorb_data
        with patch(
            "adcp_recorder.serial.consumer.insert_pnorb_data", side_effect=Exception("DB failure")
        ):
            # Add valid PNORB message
            sentence = (
                "$PNORB,102115,090715,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*7C"
            )
            queue.put(sentence.encode("ascii"))

            consumer.start()
            time.sleep(0.5)
            consumer.stop()

        # Check file writer - it should have been called despite DB failure
        mock_file_writer.write_record.assert_any_call("PNORB", ANY)
