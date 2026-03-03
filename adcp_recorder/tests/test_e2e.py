import logging
import tempfile
import threading
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import serial

from adcp_recorder.config import RecorderConfig
from adcp_recorder.core.recorder import AdcpRecorder

logger = logging.getLogger(__name__)


class MockSerial:
    """Mock serial port that signals when all lines have been consumed."""

    def __init__(self, *args, **kwargs):
        self.port = kwargs.get("port")
        self.timeout = kwargs.get("timeout", 1.0)
        self.is_open = True
        self.lines: list[bytes] = []
        self._ptr = 0
        self.done = threading.Event()

    def readline(self):
        if self._ptr < len(self.lines):
            line = self.lines[self._ptr]
            self._ptr += 1
            time.sleep(0.01)
            return line
        # Signal that all lines have been consumed
        self.done.set()
        # Block briefly to avoid CPU spinning; producer will stop us
        time.sleep(0.5)
        return b""

    def close(self):
        self.is_open = False


@pytest.fixture
def temp_recorder_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


def test_full_pipeline_e2e(temp_recorder_dir):
    db_path = temp_recorder_dir / "test_e2e.duckdb"
    config = RecorderConfig(
        serial_port="/dev/ttyMock", output_dir=str(temp_recorder_dir), db_path=str(db_path)
    )

    sentences = [
        b"$PNORI,4,1001,4,20,0.20,1.00,0*57\r\n",
        b"$PNORS,102115,090715,0,00000000,12.5,1500.0,0.0,0.0,0.0,0.0,20.0,0,0*5E\r\n",
        b"$PNORC,102115,090715,1,0.5,0.1,0.2,0.3,0.4,180.0,C,80,80,80,80,100,100,100,100*36\r\n",
        b"\xff\xfe BINARY DATA \xff\r\n",  # Binary/Invalid
    ]

    mock_instance: MockSerial | None = None

    with patch("serial.Serial") as mock_serial_class:

        def create_mock(**kwargs):
            nonlocal mock_instance
            m = MockSerial(**kwargs)
            m.lines = sentences
            mock_instance = m
            return m

        mock_serial_class.side_effect = create_mock

        recorder = AdcpRecorder(config)
        try:
            recorder.start()

            # Wait for the mock serial to signal that all lines have been read
            assert mock_instance is not None or True  # instance created after start
            # Give a moment for the producer thread to create the mock
            for _ in range(50):
                if mock_instance is not None:
                    break
                time.sleep(0.1)
            assert mock_instance is not None, "MockSerial was never instantiated"

            # Wait for all lines to be consumed by the producer
            assert mock_instance.done.wait(timeout=10), "MockSerial lines were never fully consumed"

            # Use the recorder's own db_manager to avoid DuckDB write-lock contention
            db = recorder.db_manager
            conn = db.get_connection()

            # Poll for data visibility (robust for slow CI/Windows)
            max_wait = 30.0
            poll_start = time.time()
            found = False
            while time.time() - poll_start < max_wait:
                try:
                    # Periodically refresh connection to ensure snapshot visibility
                    db.close()
                    conn = db.get_connection()

                    # Rollback before query to refresh snapshot
                    #  - wrap in try to avoid 'no transaction active'
                    try:
                        conn.rollback()
                    except Exception:
                        pass

                    # Check for ALL expected records in a single query
                    counts = conn.execute("""
                        SELECT
                            (SELECT count(*) FROM pnori),
                            (SELECT count(*) FROM pnors_df100),
                            (SELECT count(*) FROM pnorc_df100),
                            (SELECT count(*) FROM parse_errors)
                    """).fetchone()

                    if counts and all(c >= 1 for c in counts):
                        found = True
                        break
                except Exception:
                    pass
                time.sleep(0.5)

            # Stopping recorder before final check/assertions
            recorder.stop()
            # Give consumer time to finish final commit
            time.sleep(1.0)

            # Get a fresh connection as stop() closed the test thread's old one
            conn = db.get_connection()

            # Verification logic
            # Refresh counts for final assertions - use FORCE CHECKPOINT now that writer is gone
            try:
                conn.execute("FORCE CHECKPOINT;")
            except Exception:
                pass

            # Final verify counts
            counts = conn.execute("""
                SELECT
                    (SELECT count(*) FROM pnori),
                    (SELECT count(*) FROM pnors_df100),
                    (SELECT count(*) FROM pnorc_df100),
                    (SELECT count(*) FROM parse_errors)
            """).fetchone()

            count_pnori = counts[0] if counts else 0
            count_pnors = counts[1] if counts else 0
            count_pnorc = counts[2] if counts else 0
            count_errors = counts[3] if counts else 0

            if not found:
                print(
                    f"\nFinal counts: pnori={count_pnori}, pnors={count_pnors}, "
                    f"pnorc={count_pnorc}, errors={count_errors}"
                )

            assert count_pnori >= 1, f"Expected PNORI records, got {count_pnori}"
            assert count_pnors >= 1, f"Expected PNORS records, got {count_pnors}"
            assert count_pnorc >= 1, f"Expected PNORC records, got {count_pnorc}"
            assert count_errors >= 1, f"Expected parse_errors records, got {count_errors}"

            # Content assertions
            res = conn.execute("SELECT head_id FROM pnori").fetchall()
            assert res[0][0] == "1001"

            res = conn.execute("SELECT heading FROM pnors_df100").fetchall()
            assert float(res[0][0]) == 0.0

            res = conn.execute("SELECT vel1, speed FROM pnorc_df100").fetchall()
            assert float(res[0][0]) == 0.5
            assert float(res[0][1]) == 0.4

            res = conn.execute("SELECT error_type FROM parse_errors").fetchall()
            assert any("BINARY" in r[0] for r in res)
        finally:
            recorder.stop()
            # Give Windows extra time to release file locks before fixture cleanup
            time.sleep(1.0)

    # --- File Export Verification ---
    from datetime import datetime

    today_str = datetime.now().strftime("%Y%m%d")
    error_today_str = datetime.now().strftime("%d%m%y")

    def verify_export_file(prefix, partial_content, is_error=False) -> None:
        if is_error:
            expected_filename = f"ERROR_{error_today_str}.nmea"
            file_path = temp_recorder_dir / "errors" / "nmea" / expected_filename
        else:
            expected_filename = f"{prefix}_{today_str}.nmea"
            file_path = temp_recorder_dir / "nmea" / prefix / expected_filename

        assert file_path.exists(), f"Export file {file_path} not found"
        content = file_path.read_text()
        assert partial_content in content, f"Expected '{partial_content}' in {file_path}"

    verify_export_file("PNORI", "$PNORI")
    verify_export_file("PNORS", "$PNORS")
    verify_export_file("PNORC", "$PNORC")
    verify_export_file("BINARY", "BINARY DATA", is_error=True)


def test_reconnect_scenario(temp_recorder_dir):
    db_path = temp_recorder_dir / "test_reconnect.duckdb"
    config = RecorderConfig(
        serial_port="/dev/ttyMockReconnect", output_dir=str(temp_recorder_dir), db_path=str(db_path)
    )

    class StatefulMockSerial:
        def __init__(self, instance_container, **kwargs):
            instance_container.append(self)
            self.instance_id = len(instance_container)
            self.timeout = 1.0
            self.is_open = True
            self.read_count = 0

        def readline(self) -> bytes:
            # Simulate some hardware latency
            time.sleep(0.1)
            self.read_count += 1
            if self.instance_id == 1:
                if self.read_count == 1:
                    # First instance, first read: success
                    return b"$PNORI,4,2001,4,20,0.20,1.00,0*54\r\n"
                # First instance, subsequent read: fail
                self.is_open = False
                raise serial.SerialException("Simulated connection loss")
            # Subsequent instances (reconnections)
            if self.read_count == 1:
                return b"$PNORI,4,AfterReconnect,4,20,0.20,1.00,0*5A\r\n"
            return b""

        def close(self) -> None:
            self.is_open = False

    instances: list[Any] = []

    # We want to mock sleep for the reconnection logic but NOT for the test's wait loop.
    # The SerialConnectionManager uses time.sleep(wait_time).

    with patch(
        "serial.Serial", side_effect=lambda **kwargs: StatefulMockSerial(instances, **kwargs)
    ):
        # Only patch reconnection sleep to avoid slowing down tests, but allow other sleeps
        # to prevent GIL starvation
        with patch("adcp_recorder.serial.port_manager.time.sleep", return_value=None):
            recorder = AdcpRecorder(config)
            try:
                recorder.start()
                # Give threads time to start and complete reconnect cycle
                time.sleep(1.0)

                # Wait for processing
                max_wait = 20.0
                start_time = time.time()
                found = False

                # Use the recorder's DatabaseManager to check results
                db = recorder.db_manager
                conn = db.get_connection()

                while time.time() - start_time < max_wait:
                    try:
                        # Periodically refresh connection to ensure snapshot visibility
                        db.close()
                        conn = db.get_connection()

                        # Rollback before query to refresh snapshot
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                        res = conn.execute("SELECT head_id FROM pnori").fetchall()
                        if len(res) >= 2:
                            found = True
                            break
                    except Exception:
                        pass

                    time.sleep(0.5)

                if not found:
                    # Stop first, then check
                    recorder.stop()
                    time.sleep(1.0)
                    # Re-acquire connection after stop()
                    conn = db.get_connection()
                    try:
                        conn.execute("FORCE CHECKPOINT;")
                    except Exception:
                        pass
                    # Fresh connections don't need rollback
                    pnori = conn.execute("SELECT * FROM pnori").fetchall()
                    pnori_count = len(pnori)
                    assert found, (
                        f"Reconnection failed. Found only {pnori_count} pnori records: {pnori}. "
                        f"Instances created: {len(instances)}"
                    )

                # Stop recorder before final double check
                recorder.stop()
                time.sleep(1.0)
                # Re-acquire connection after stop()
                conn = db.get_connection()

                # Double check content
                try:
                    conn.execute("FORCE CHECKPOINT;")
                except Exception:
                    pass
                # Fresh connections don't need rollback
                res = conn.execute("SELECT head_id FROM pnori ORDER BY head_id").fetchall()
                ids = [r[0] for r in res]
                assert "2001" in ids
                assert "AfterReconnect" in ids
            finally:
                recorder.stop()
                # Give some extra time for Windows to release file locks before fixture cleanup
                time.sleep(1.0)


# I'll implement a more robust version of reconnect test in the file.
