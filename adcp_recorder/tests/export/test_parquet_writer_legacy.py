"""Tests for ParquetWriter legacy file merging and backfilling."""

import logging
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import polars as pl

from adcp_recorder.export.parquet_writer import ParquetWriter


class TestParquetWriterLegacy:
    """Tests for legacy file handling in ParquetWriter."""

    def test_merge_existing_and_legacy_files(self, tmp_path):
        """Test merging existing daily file and multiple legacy files."""
        writer = ParquetWriter(str(tmp_path))
        prefix = "TEST"
        record_date = date(2024, 1, 1)
        partition_dir = writer._get_partition_path(prefix, record_date)

        # 1. Create existing final file
        final_path = partition_dir / f"{prefix}.parquet"
        df_final = pl.DataFrame({"a": [1], "received_at": [datetime(2024, 1, 1, 10)]})
        df_final.write_parquet(final_path)

        # 2. Create legacy files
        legacy1_path = partition_dir / f"{prefix}_legacy1.parquet"
        df_legacy1 = pl.DataFrame({"a": [2], "received_at": [datetime(2024, 1, 1, 11)]})
        df_legacy1.write_parquet(legacy1_path)

        legacy2_path = partition_dir / f"{prefix}_legacy2.parquet"
        df_legacy2 = pl.DataFrame({"a": [3], "received_at": [datetime(2024, 1, 1, 12)]})
        df_legacy2.write_parquet(legacy2_path)

        # 3. New records
        new_records = [{"a": 4, "received_at": datetime(2024, 1, 1, 13)}]

        # Execute
        writer._write_to_parquet(prefix, record_date, new_records)

        # Verify merge
        result_df = pl.read_parquet(final_path)
        assert len(result_df) == 4
        assert sorted(result_df["a"].to_list()) == [1, 2, 3, 4]

        # Verify legacy files cleanup
        assert not legacy1_path.exists()
        assert not legacy2_path.exists()

    def test_read_parquet_exception_handling(self, tmp_path, caplog):
        """Test that read_parquet exceptions are caught and logged."""
        writer = ParquetWriter(str(tmp_path))
        prefix = "ERR"
        record_date = date(2024, 2, 2)
        partition_dir = writer._get_partition_path(prefix, record_date)

        # Create a file that we'll fail to read
        bad_path = partition_dir / f"{prefix}.parquet"
        bad_path.write_text("not a parquet file")

        # Also create a legacy file that we'll fail to read
        bad_legacy = partition_dir / f"{prefix}_legacy.parquet"
        bad_legacy.write_text("not a parquet file")

        with caplog.at_level(logging.WARNING):
            # Should not raise, just log warnings and write new records
            writer._write_to_parquet(prefix, record_date, [{"a": 1}])

            assert "Could not read existing Parquet" in caplog.text
            assert "Could not read legacy Parquet" in caplog.text

        # Verify final file contains at least the new record
        result_df = pl.read_parquet(bad_path)
        assert len(result_df) == 1
        assert result_df["a"][0] == 1

    def test_backfill_measurement_id(self, tmp_path):
        """Test backfilling measurement_id from date and time strings."""
        writer = ParquetWriter(str(tmp_path))
        prefix = "BACKFILL"
        record_date = date(2024, 3, 3)

        # Record with existing measurement_id (should be kept)
        rec1 = {
            "measurement_date": "010224",
            "measurement_time": "100000",
            "measurement_id": 123,
            "received_at": datetime(2024, 3, 3),
        }
        # Record missing measurement_id (should be backfilled)
        rec2 = {
            "measurement_date": "030324",  # DDMMYY
            "measurement_time": "120000",
            "received_at": datetime(2024, 3, 3),
        }

        # _write_to_parquet will use pl.from_dicts which might use different schemas
        # but here we pass them in a list.
        writer._write_to_parquet(prefix, record_date, [rec1, rec2])

        final_path = writer._get_partition_path(prefix, record_date) / f"{prefix}.parquet"
        result_df = pl.read_parquet(final_path)

        # rec1 kept 123
        row1 = result_df.filter(pl.col("measurement_id") == 123)
        assert len(row1) == 1

        # rec2 backfilled: 240303120000
        # measurement_date is MMDDYY (030324 -> March 3, 2024)
        # slice(4,2) -> 24
        # slice(0,2) -> 03
        # slice(2,2) -> 03
        row2 = result_df.filter(pl.col("measurement_id") == 240303120000)
        assert len(row2) == 1

    def test_legacy_cleanup_exception_handling(self, tmp_path, caplog):
        """Test that legacy file deletion errors are caught and logged."""
        writer = ParquetWriter(str(tmp_path))
        prefix = "DEL_ERR"
        record_date = date(2024, 4, 4)
        partition_dir = writer._get_partition_path(prefix, record_date)

        legacy_path = partition_dir / f"{prefix}_legacy.parquet"
        pl.DataFrame({"a": [1]}).write_parquet(legacy_path)

        with patch("pathlib.Path.unlink", side_effect=Exception("Permission denied")):
            with caplog.at_level(logging.WARNING):
                writer._write_to_parquet(prefix, record_date, [{"b": 2}])
                assert "Could not delete legacy file" in caplog.text

    def test_diagonal_concat_schema_evolution(self, tmp_path):
        """Test diagonal union handles mismatched columns."""
        writer = ParquetWriter(str(tmp_path))
        prefix = "SCHEMA"
        record_date = date(2024, 5, 5)
        partition_dir = writer._get_partition_path(prefix, record_date)

        # Existing file with column 'a'
        final_path = partition_dir / f"{prefix}.parquet"
        pl.DataFrame({"a": [1]}).write_parquet(final_path)

        # New records with column 'b'
        writer._write_to_parquet(prefix, record_date, [{"b": 2}])

        result_df = pl.read_parquet(final_path)
        assert "a" in result_df.columns
        assert "b" in result_df.columns
        assert len(result_df) == 2
        # Use filter for robust check
        assert result_df.filter(pl.col("a") == 1)["b"][0] is None
        assert result_df.filter(pl.col("b") == 2)["a"][0] is None

    def test_close(self, tmp_path):
        """Test that close flushes buffers and closes connection."""
        writer = ParquetWriter(str(tmp_path))
        writer.write_record("CLOSE_TEST", {"v": 1})
        assert len(writer._buffers["CLOSE_TEST"]) == 1

        writer.close()
        assert len(writer._buffers["CLOSE_TEST"]) == 0
        # Verify file exists
        files = list(Path(tmp_path).glob("**/*.parquet"))
        assert len(files) == 1

    def test_record_type_fallback(self, tmp_path):
        """Test that record_type is added if missing."""
        writer = ParquetWriter(str(tmp_path))
        prefix = "TYPE"
        record_date = date(2024, 6, 6)

        writer._write_to_parquet(prefix, record_date, [{"a": 1}])

        final_path = writer._get_partition_path(prefix, record_date) / f"{prefix}.parquet"
        df = pl.read_parquet(final_path)
        assert df["record_type"][0] == prefix
