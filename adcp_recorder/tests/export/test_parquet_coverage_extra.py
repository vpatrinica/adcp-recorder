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


def test_write_to_parquet_retries_and_succeeds(tmp_path, mocker):
    """Cover lines 304-312 (retry logic) by mocking os.replace to fail once."""
    import os
    from unittest.mock import MagicMock

    writer = ParquetWriter(str(tmp_path))
    prefix = "RETRY_OK"
    record = {"data": 1, "measurement_date": "010124", "measurement_time": "120000"}

    # Mock os.replace to fail once and then succeed
    mock_replace = MagicMock(side_effect=[OSError("Locked"), None])

    mocker.patch("os.replace", mock_replace)
    # We also need to mock time.sleep to speed up the test
    mocker.patch("time.sleep", return_value=None)

    # We need to mock os.path.exists to return True ONLY for the final_path
    # so it enters the retry loop's replace branch
    original_exists = os.path.exists

    def side_effect_exists(path):
        if "RETRY_OK.parquet" in str(path) and not str(path).endswith(".writing"):
            return True
        return original_exists(path)

    mocker.patch("os.path.exists", side_effect=side_effect_exists)

    writer.write_record(prefix, record)
    writer.flush(prefix)

    assert mock_replace.call_count == 2


def test_write_to_parquet_retries_and_fails(tmp_path, mocker):
    """Cover lines 306-311 (retry exhaustion) by mocking os.replace to always fail."""
    import os
    from unittest.mock import MagicMock

    writer = ParquetWriter(str(tmp_path))
    prefix = "RETRY_FAIL"
    record = {"data": 1, "measurement_date": "010124", "measurement_time": "120000"}

    # Mock os.replace to always fail
    mock_replace = MagicMock(side_effect=OSError("Persistent Lock"))

    mocker.patch("os.replace", mock_replace)
    mocker.patch("time.sleep", return_value=None)

    # Mock os.path.exists to return True ONLY for the final_path
    original_exists = os.path.exists

    def side_effect_exists(path):
        if "RETRY_FAIL.parquet" in str(path) and not str(path).endswith(".writing"):
            return True
        return original_exists(path)

    mocker.patch("os.path.exists", side_effect=side_effect_exists)

    # flush() swallows the exception after logging it, so we don't expect a raise here
    writer.write_record(prefix, record)
    writer.flush(prefix)

    # Max retries is 5
    assert mock_replace.call_count == 5
