import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest
import serial

from adcp_recorder.config import RecorderConfig
from adcp_recorder.core.recorder import AdcpRecorder
from adcp_recorder.db import DatabaseManager


class MockSerial:
    def __init__(self, *args, **kwargs):
        self.port = kwargs.get("port")
        self.timeout = kwargs.get("timeout", 1.0)
        self.is_open = True
        self.lines = []
        self._ptr = 0

    def readline(self):
        if self._ptr < len(self.lines):
            line = self.lines[self._ptr]
            self._ptr += 1
            # Small delay to simulate realistic serial port behavior
            time.sleep(0.01)
            return line
        # After all lines are read, simulate timeout or empty
        time.sleep(0.1)
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

    # Valid NMEA sentences
    # Note: PNORI checksum 2E is valid for the example in test_pnori.py
    # PNORS/PNORC checksums XX are placeholders that might fail if strict validation is on.
    # Actually, NMEA parser in this project might skip validation or handle XX.
    # Let's use valid checksums or ensure validation is not an issue.
    # Looking at test_pnori.py: "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E"

    sentences = [
        b"$PNORI,4,1001,4,20,0.20,1.00,0*1D\r\n",
        b"$PNORS,102115,090715,0,00000000,12.5,1500.0,0.0,0.0,0.0,0.0,20.0,0,0*0E\r\n",
        b"$PNORC,102115,090715,1,0.5,0.1,0.2,0.3,0.4,180.0,C,80,80,80,80,100,100,100,100*76\r\n",
        b"\xff\xfe BINARY DATA \xff\r\n",  # Binary/Invalid
    ]

    with patch("serial.Serial") as mock_serial_class:
        # Side effect to inject lines into the created mock instance
        def create_mock(**kwargs):
            m = MockSerial(**kwargs)
            m.lines = sentences
            return m

        mock_serial_class.side_effect = create_mock

        recorder = AdcpRecorder(config)
        try:
            recorder.start()

            # Wait for processing with a loop
            max_wait = 20.0  # Increased
            start_time = time.time()
            db = DatabaseManager(str(db_path))

            found_all = False
            last_err = None
            while time.time() - start_time < max_wait:
                conn = db.get_connection()
                try:
                    # Force a refresh of the connection state on Windows
                    conn.rollback()
                except Exception:
                    pass

                try:
                    # We expect 3 successfully parsed messages in their tables
                    count_pnori = conn.execute("SELECT count(*) FROM pnori").fetchone()[0]
                    count_pnors = conn.execute("SELECT count(*) FROM pnors_df100").fetchone()[0]
                    count_pnorc = conn.execute("SELECT count(*) FROM pnorc_df100").fetchone()[0]
                    count_errors = conn.execute("SELECT count(*) FROM parse_errors").fetchone()[0]

                    if (
                        count_pnori >= 1
                        and count_pnors >= 1
                        and count_pnorc >= 1
                        and count_errors >= 1
                    ):
                        found_all = True
                        break
                except Exception as e:
                    last_err = str(e)

                # Close connection and reopen next time to avoid stale state on Windows
                db.close()
                time.sleep(0.5)

            if not found_all:
                # Diagnostics: check raw_lines and parse_errors
                conn = db.get_connection()
                try:
                    raw_lines = conn.execute(
                        "SELECT record_type, parse_status, error_message FROM raw_lines"
                    ).fetchall()
                    errors = conn.execute(
                        "SELECT error_type, error_message FROM parse_errors"
                    ).fetchall()
                    pnori = conn.execute("SELECT count(*) FROM pnori").fetchone()[0]
                    pnors = conn.execute("SELECT count(*) FROM pnors_df100").fetchone()[0]
                    pnorc = conn.execute("SELECT count(*) FROM pnorc_df100").fetchone()[0]
                finally:
                    db.close()

                recorder.stop()
                pytest.fail(
                    f"E2E wait timeout. Found_all={found_all}. Last Error: {last_err}.\n"
                    f"Counts: PNORI={pnori}, PNORS={pnors}, PNORC={pnorc}\n"
                    f"Raw lines: {raw_lines}. Errors: {errors}"
                )
        finally:
            recorder.stop()

    # Final verifications
    db = DatabaseManager(str(db_path))
    conn = db.get_connection()
    try:
        res = conn.execute("SELECT head_id FROM pnori").fetchall()
        assert res[0][0] == "1001"

        res = conn.execute("SELECT heading FROM pnors_df100").fetchall()
        assert float(res[0][0]) == 0.0

        res = conn.execute("SELECT vel1, speed FROM pnorc_df100").fetchall()
        assert float(res[0][0]) == 0.5
        assert float(res[0][1]) == 0.4

        # Check Error Table (for binary data)
        res = conn.execute("SELECT error_type FROM parse_errors").fetchall()
        assert any("BINARY" in r[0] for r in res)
    finally:
        db.close()

        # --- File Export Verification (Phase 7) ---
        # Verify that files were created for each message type and errors
        from datetime import datetime

        today_str = datetime.now().strftime("%Y%m%d")
        error_today_str = datetime.now().strftime("%d%m%y")

        # Helper to check file existence and content
        def verify_export_file(prefix, partial_content, is_error=False):
            if is_error:
                expected_filename = f"ERRORR_{error_today_str}.nmea"
                file_path = temp_recorder_dir / "errors" / prefix / expected_filename
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

        def readline(self):
            self.read_count += 1
            if self.instance_id == 1:
                if self.read_count == 1:
                    # First instance, first read: success
                    return b"$PNORI,4,2001,4,20,0.20,1.00,0*1C\r\n"
                else:
                    # First instance, subsequent read: fail
                    self.is_open = False
                    raise serial.SerialException("Simulated connection loss")
            else:
                # Subsequent instances (reconnections)
                if self.read_count == 1:
                    return b"$PNORI,4,AfterReconnect,4,20,0.20,1.00,0*33\r\n"
                return b""

        def close(self):
            self.is_open = False

    instances = []

    # We want to mock sleep for the reconnection logic but NOT for the test's wait loop.
    # The SerialConnectionManager uses time.sleep(wait_time).

    with patch(
        "serial.Serial", side_effect=lambda **kwargs: StatefulMockSerial(instances, **kwargs)
    ):
        # Target sleep mock to adcp_recorder.serial.port_manager to avoid hitting the test's loop
        with patch("adcp_recorder.serial.port_manager.time.sleep", return_value=None):
            recorder = AdcpRecorder(config)
            try:
                recorder.start()

                # Use DatabaseManager to check results
                db = DatabaseManager(str(db_path))

                # Wait for processing
                max_wait = 20.0  # Increased timeout
                start_time = time.time()
                found = False
                last_err = None
                while time.time() - start_time < max_wait:
                    conn = db.get_connection()
                    try:
                        # Check both messages
                        res = conn.execute("SELECT head_id FROM pnori").fetchall()
                        if len(res) >= 2:
                            found = True
                            break
                    except Exception as e:
                        last_err = str(e)

                    db.close()
                    time.sleep(0.5)

                if not found:
                    # Get diagnostics if failed
                    conn = db.get_connection()
                    try:
                        raw = conn.execute("SELECT * FROM raw_lines").fetchall()
                        errors = conn.execute("SELECT * FROM parse_errors").fetchall()
                        pnori = conn.execute("SELECT head_id FROM pnori").fetchall()
                    finally:
                        db.close()

                    recorder.stop()
                    print(f"DEBUG: last_err={last_err}")
                    print(f"DEBUG: pnori_table={pnori}")
                    print(f"DEBUG: raw_lines={raw}")
                    print(f"DEBUG: parse_errors={errors}")
                    print(f"DEBUG: instances={len(instances)}")
                    assert found, "Did not find both records after reconnection"

                # Double check content
                conn = db.get_connection()
                try:
                    res = conn.execute("SELECT head_id FROM pnori ORDER BY head_id").fetchall()
                    ids = [r[0] for r in res]
                    assert "2001" in ids
                    assert "AfterReconnect" in ids
                finally:
                    db.close()
            finally:
                recorder.stop()


# I'll implement a more robust version of reconnect test in the file.
