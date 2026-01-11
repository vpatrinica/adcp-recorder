import time
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
import os

import pytest
import serial

from adcp_recorder.config import RecorderConfig
from adcp_recorder.core.recorder import AdcpRecorder
from adcp_recorder.db import DatabaseManager

def get_memory_usage_mb():
    """Get current process memory usage in MB (Linux only fallback)."""
    try:
        with open('/proc/self/status') as f:
            for line in f:
                if line.startswith('VmRSS:'):
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
        return b""

    def close(self):
        self.is_open = False

def test_throughput_performance():
    """Measure messages per second throughput using file-based DB."""
    # Generate 50 messages
    sentences = [
        b"$PNORI,4,PerfTest,4,20,0.20,1.00,0*34\r\n",
        b"$PNORS,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,2.3,0.000,22.45,0,0*3E\r\n",
    ]
    for i in range(1, 49):
        sentences.append(f"$PNORC,102115,090715,{i % 20 + 1},0.1,0.2,0.3*33\r\n".encode())

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "perf.duckdb"
        config = RecorderConfig(
            serial_port="/dev/ttyPerf",
            output_dir=str(tmp_dir),
            db_path=str(db_path)
        )
        
        with patch("serial.Serial", return_value=BulkMockSerial(sentences)):
            recorder = AdcpRecorder(config)
            
            start_time = time.time()
            recorder.start()
            
            # Wait for processing
            db = DatabaseManager(str(db_path))
            conn = db.get_connection()
            
            max_wait = 120.0 # High timeout for slow disk I/O with individual commits
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
                time.sleep(1.0)
            
            end_time = time.time()
            recorder.stop()
            
            duration = end_time - start_time
            throughput = len(sentences) / duration
            
            print(f"\nThroughput: {throughput:.2f} messages/sec (Duration: {duration:.2f}s, Count: {count})")
            
            assert processed, f"Timed out after {max_wait}s. Only {count} records found."
            # Baseline expectation for individual commits: > 1 msg/s
            assert throughput > 1.0, f"Throughput too low: {throughput:.2f} msg/s"

def test_memory_stability():
    """Monitor memory usage during a sustained run."""
    # 500 messages
    sentences = [f"$PNORC,102115,090715,1,0.1,0.2,0.3*33\r\n".encode() for _ in range(500)]
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "mem_test.duckdb"
        config = RecorderConfig(
            serial_port="/dev/ttyMem",
            output_dir=str(tmp_dir),
            db_path=str(db_path)
        )
        
        with patch("serial.Serial", return_value=BulkMockSerial(sentences)):
            recorder = AdcpRecorder(config)
            
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
            
            # Should stay within reasonable bounds (< 50MB growth for 500 msgs)
            assert mem_growth < 50.0, f"Significant memory growth detected: {mem_growth:.2f} MB"

def test_database_concurrency():
    """Verify that multiple threads can access the database simultaneously."""
    import threading
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "concurrency.duckdb"
        db_manager = DatabaseManager(str(db_path))
        db_manager.initialize_schema()
        
        def insert_worker(worker_id):
            conn = db_manager.get_connection()
            for i in range(50):
                conn.execute(
                    "INSERT INTO raw_lines (line_id, raw_sentence, record_type) VALUES (nextval('raw_lines_seq'), ?, ?)",
                    [f"worker {worker_id} line {i}", "TEST"]
                )
                conn.commit()
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=insert_worker, args=(i,))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        # Verify all records inserted
        conn = db_manager.get_connection()
        count = conn.execute("SELECT count(*) FROM raw_lines").fetchone()[0]
        assert count == 250, f"Expected 250 records, got {count}"
