import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from adcp_recorder.config import RecorderConfig
from adcp_recorder.core.nmea import compute_checksum
from adcp_recorder.core.recorder import AdcpRecorder
from adcp_recorder.db import DatabaseManager


def get_memory_usage_mb():
    """Get current process memory usage in MB (Linux only fallback)."""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except Exception:
        pass
    return 0.0


class BulkMockSerial:
    def __init__(self, sentences, delay=0):
        self.port = "MOCK"
        self.timeout = 1.0
        self.is_open = True
        self.sentences = sentences
        self._ptr = 0
        self.delay = delay

    def readline(self):
        if self._ptr < len(self.sentences):
            line = self.sentences[self._ptr]
            self._ptr += 1
            if self.delay > 0:
                time.sleep(self.delay)
            return line
        time.sleep(0.1)
        return b""

    def close(self):
        self.is_open = False


def test_throughput_performance():
    """Measure messages per second throughput using file-based DB."""
    # Generate 50 messages
    sentences = [
        b"$PNORI,4,1001,4,20,0.20,1.00,0*34\r\n",
        b"$PNORS,102115,090715,0,00000000,14.4,1523.0,275.9,15.7,2.3,0.0,22.45,0,0*3E\r\n",
    ]
    for i in range(1, 49):
        # PNORC: 19 fields
        # Added speed field (25.5) before direction (180.0)
        raw_content = (
            f"$PNORC,102115,090715,{i % 20 + 1},0.1,0.2,0.3,0.4,25.5,180.0,"
            "C,80,80,80,80,100,100,100,100"
        )
        cs = compute_checksum(raw_content)
        sentences.append(f"{raw_content}*{cs}\r\n".encode())

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "perf.duckdb"
        config = RecorderConfig(
            serial_port="/dev/ttyPerf", output_dir=str(tmp_dir), db_path=str(db_path)
        )

        with patch("serial.Serial", return_value=BulkMockSerial(sentences)):
            recorder = AdcpRecorder(config)

            start_time = time.time()
            recorder.start()

            # Wait for processing
            # Wait for processing
            db = DatabaseManager(str(db_path))
            try:
                conn = db.get_connection()

                max_wait = 10.0
                processed = False
                count = 0
                while time.time() - start_time < max_wait:
                    try:
                        count = conn.execute("SELECT count(*) FROM pnorc_df100").fetchone()[0]
                        if count >= 48:
                            processed = True
                            break
                    except Exception:
                        pass
                    time.sleep(0.5)

                end_time = time.time()
                recorder.stop()

                duration = end_time - start_time
                throughput = len(sentences) / duration

                if not processed:
                    raw_count = conn.execute("SELECT count(*) FROM raw_lines").fetchone()[0]
                    error_count = conn.execute("SELECT count(*) FROM parse_errors").fetchone()[0]
                    errors = conn.execute(
                        "SELECT error_type, error_message FROM parse_errors LIMIT 5"
                    ).fetchall()
                    print(
                        f"\nTarget count not reached. raw_lines={raw_count}, "
                        f"parse_errors={error_count}"
                    )
                    for e in errors:
                        print(f"Error: {e}")

                print(
                    f"\nThroughput: {throughput:.2f} messages/sec "
                    f"(Duration: {duration:.2f}s, Count: {count})"
                )
            finally:
                db.close()

            assert processed, f"Timed out after {max_wait}s. Only {count} records found."
            # Baseline expectation for individual commits: > 1 msg/s
            assert throughput > 1.0, f"Throughput too low: {throughput:.2f} msg/s"


def test_memory_stability():
    """Monitor memory usage during a sustained run."""
    # 500 messages (PNORC with 19 fields)
    sentences = []
    for _ in range(500):
        # Added speed field (25.5) before direction (180.0)
        raw_content = (
            "$PNORC,102115,090715,1,0.1,0.2,0.3,0.4,25.5,180.0,C,80,80,80,80,100,100,100,100"
        )
        cs = compute_checksum(raw_content)
        sentences.append(f"{raw_content}*{cs}\r\n".encode())

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "mem_test.duckdb"
        config = RecorderConfig(
            serial_port="/dev/ttyMem", output_dir=str(tmp_dir), db_path=str(db_path)
        )

        with patch("serial.Serial", return_value=BulkMockSerial(sentences)):
            recorder = AdcpRecorder(config)
            try:
                initial_mem = get_memory_usage_mb()
                recorder.start()

                # Monitor memory as it processes
                start_time = time.time()
                mem_readings = []
                while time.time() - start_time < 20.0:
                    mem_readings.append(get_memory_usage_mb())
                    time.sleep(2.0)

                recorder.stop()
                final_mem = get_memory_usage_mb()

                mem_growth = final_mem - initial_mem
                print(f"\nMemory growth: {mem_growth:.2f} MB")

                # Should stay within reasonable bounds (<200MB growth for 500 msgs)
                # Note: polars library loading adds ~100MB overhead, but this is a one-time cost
                assert mem_growth < 200.0, (
                    f"Significant memory growth detected: {mem_growth:.2f} MB"
                )
            finally:
                # Ensure recorder is fully stopped and all resources released
                recorder.stop()
                # On Windows, file handles may take time to release
                # Force garbage collection and wait longer for threads to fully exit
                import gc

                gc.collect()
                time.sleep(2.5)


def test_database_concurrency():
    """Verify that multiple threads can access the database simultaneously."""
    import threading

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "concurrency.duckdb"
        db_manager = DatabaseManager(str(db_path))
        db_manager.initialize_schema()

        def insert_worker(worker_id) -> None:
            try:
                conn = db_manager.get_connection()
                for i in range(50):
                    conn.execute(
                        "INSERT INTO raw_lines (line_id, raw_sentence, record_type) "
                        "VALUES (nextval('raw_lines_seq'), ?, ?)",
                        [f"worker {worker_id} line {i}", "TEST"],
                    )
                    conn.commit()
            finally:
                db_manager.close()

        try:
            threads = []
            for i in range(5):
                t = threading.Thread(target=insert_worker, args=(i,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()
        finally:
            db_manager.close()

        # Verify all records inserted
        conn = db_manager.get_connection()
        count = conn.execute("SELECT count(*) FROM raw_lines").fetchone()[0]
        db_manager.close()
        assert count == 250, f"Expected 250 records, got {count}"
