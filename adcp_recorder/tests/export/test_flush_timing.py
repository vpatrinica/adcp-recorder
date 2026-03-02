# Test Time-based Flush in ParquetWriter

import os
import shutil
from pathlib import Path

from adcp_recorder.export.parquet_writer import ParquetWriter


def test_time_based_flush():
    test_dir = "tmp_test_parquet"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)

    try:
        # Initialize with a large buffer so it doesn't flush by count
        writer = ParquetWriter(test_dir, buffer_size=100)

        prefix = "TEST"
        # 10/02/26 (MMDDYY) -> 2026-10-02
        record = {"value": 1, "measurement_date": "100226", "measurement_time": "200000"}

        # Write one record
        writer.write_record(prefix, record)

        # Verify no file exists yet (buffer size 100)
        partition_dir = Path(test_dir) / "parquet" / prefix / "date=2026-10-02"
        parquet_file = partition_dir / f"{prefix}.parquet"

        assert not parquet_file.exists(), "File should not exist yet"

        # Wait for more than the stale age (using a small age for testing if possible)
        # But we hardcoded 300 in the code for default.
        # Let's call flush_stale manually with a small age.

        writer.flush_stale(max_age_seconds=0)  # Force flush

        assert parquet_file.exists(), "File should exist after flush_stale"
        print("Success: Time-based flush verified.")

    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)


if __name__ == "__main__":
    test_time_based_flush()
