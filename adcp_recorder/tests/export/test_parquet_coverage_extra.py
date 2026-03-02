"""Extra coverage tests for ParquetWriter."""

from datetime import datetime

from adcp_recorder.export.parquet_writer import ParquetWriter


def test_flush_without_partition_date(tmp_path):
    """Cover lines 147-148 in parquet_writer.py.

    This happens when a record in the buffer is missing the '_partition_date' key.
    """
    writer = ParquetWriter(str(tmp_path))
    prefix = "TEST"

    # Manually inject a record into the buffer without _partition_date
    # We also need to ensure it has 'received_at' or it will fall back to now().date()
    # which is also covered by the same logic.
    writer._buffers[prefix] = [{"data": 1, "received_at": datetime(2024, 1, 1, 12, 0, 0)}]

    writer.flush(prefix)

    # Verify that the file was written to the correct partition
    expected_path = tmp_path / "parquet" / prefix / "date=2024-01-01" / f"{prefix}.parquet"
    assert expected_path.exists()


def test_flush_without_partition_date_or_received_at(tmp_path):
    """Cover line 148 fallback to now().date()."""
    writer = ParquetWriter(str(tmp_path))
    prefix = "TEST_NOW"

    # Manually inject a record without _partition_date and without received_at
    writer._buffers[prefix] = [{"data": 2}]

    writer.flush(prefix)

    today = datetime.now().date().isoformat()
    expected_path = tmp_path / "parquet" / prefix / f"date={today}" / f"{prefix}.parquet"
    assert expected_path.exists()
