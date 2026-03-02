"""Tests for ParquetWriter date partitioning logic."""

from datetime import date

from adcp_recorder.export.parquet_writer import ParquetWriter


def test_parquet_partitioning_by_measurement_date(tmp_path):
    """Verify that records are partitioned by their measurement date, not received_at.

    This test simulates receiving a record 'today' that actually belongs to 'yesterday'
    according to its internal date fields.
    """
    base_path = tmp_path
    writer = ParquetWriter(str(base_path))

    # 1. Create a record that says it's from yesterday (MMDDYY format used in PNOR*)
    yesterday = date(2026, 3, 1)
    yesterday_str = yesterday.strftime("%m%d%y")

    record = {
        "date": yesterday_str,
        "time": "235500",
        "hm0": 1.5,
        "tp": 8.0,
    }

    # Write the record today
    writer.write_record("PNORB", record)
    writer.close()

    # 2. Check the directory structure
    parquet_base = base_path / "parquet" / "PNORB"
    yesterday_partition = parquet_base / f"date={yesterday.isoformat()}"
    today_partition = parquet_base / f"date={date(2026, 3, 2).isoformat()}"

    # The record is from yesterday, but ParquetWriter currently uses today's date (received_at)
    today = date(2026, 3, 2)
    today_partition = parquet_base / f"date={today.isoformat()}"

    # Asserting the fix: it should be in yesterday's partition, not today's
    assert yesterday_partition.exists(), f"Partition for {yesterday.isoformat()} should exist"
    assert (yesterday_partition / "PNORB.parquet").exists()
    assert not today_partition.exists(), (
        "Should NOT have created a partition for today if record is from yesterday"
    )


def test_parquet_measurement_id_consistency(tmp_path):
    """Verify that measurement_id is generated consistently from measurement date/time."""
    base_path = tmp_path
    writer = ParquetWriter(str(base_path))

    # March 1, 2026 23:55:00
    # measurement_id should be 260301235500
    record = {"measurement_date": "030126", "measurement_time": "235500", "val": 10.0}

    writer.write_record("TEST", record)
    writer.flush()

    # Read back to check measurement_id
    # It should now be in yesterday's partition
    yesterday_val = date(2026, 3, 1).isoformat()
    import polars as pl

    df = pl.read_parquet(
        str(base_path / "parquet" / "TEST" / f"date={yesterday_val}" / "TEST.parquet")
    )

    assert df["measurement_id"][0] == 260301235500
