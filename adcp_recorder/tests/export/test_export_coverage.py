"""Comprehensive coverage tests for export modules."""

import os
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from adcp_recorder.export.binary_writer import BinaryBlobWriter
from adcp_recorder.export.file_writer import FileWriter
from adcp_recorder.export.parquet_writer import ParquetWriter


class TestBinaryBlobWriterCoverage:
    """Coverage tests for BinaryBlobWriter."""

    def test_binary_writer_identifier_increment(self, tmp_path):
        """Test that identifier increments when multiple blobs start in same second."""
        writer = BinaryBlobWriter(str(tmp_path))

        # Patch datetime to return same second
        fixed_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        with patch("adcp_recorder.export.binary_writer.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now

            path1 = writer.start_blob(b"chunk1")
            assert "20230101_120000_bin_001.dat" in path1

            path2 = writer.start_blob(b"chunk2")
            assert "20230101_120000_bin_002.dat" in path2

            writer.finish_blob()

    def test_binary_writer_append_to_open(self, tmp_path):
        """Test appending to an already open blob."""
        writer = BinaryBlobWriter(str(tmp_path))
        writer.start_blob(b"start")
        writer.append_chunk(b"extra")
        path = writer.finish_blob()
        with open(path, "rb") as f:
            assert f.read() == b"startextra"

    def test_finish_blob_none(self, tmp_path):
        """Test finish_blob when no file is open."""
        writer = BinaryBlobWriter(str(tmp_path))
        assert writer.finish_blob() is None

    def test_start_blob_closes_previous(self, tmp_path):
        """Test that start_blob closes previous open blob."""
        writer = BinaryBlobWriter(str(tmp_path))
        writer.start_blob(b"one")
        assert writer._current_file is not None

        # This should call finish_blob internaly
        writer.start_blob(b"two")
        assert writer._current_file is not None
        writer.finish_blob()

    def test_append_chunk_starts_blob_if_none(self, tmp_path):
        """Test append_chunk starts a new blob if none is open."""
        writer = BinaryBlobWriter(str(tmp_path))
        assert writer._current_file is None

        writer.append_chunk(b"orphan_chunk")
        assert writer._current_file is not None
        writer.finish_blob()

    def test_close_finishes_blob(self, tmp_path):
        """Test close call finishes current blob."""
        writer = BinaryBlobWriter(str(tmp_path))
        writer.start_blob(b"data")
        writer.close()
        assert writer._current_file is None


class TestFileWriterCoverage:
    """Coverage tests for FileWriter."""

    def test_write_empty_data(self, tmp_path):
        """Test write with empty prefix or data does nothing."""
        writer = FileWriter(str(tmp_path))
        writer.write("", "data")
        writer.write("PNORI", "")
        # No files should be created
        assert not os.path.exists(os.path.join(tmp_path, "nmea"))

    def test_write_invalid_record_empty(self, tmp_path):
        """Test write_invalid_record with empty prefix or data."""
        writer = FileWriter(str(tmp_path))
        writer.write_invalid_record("", "data")
        writer.write_invalid_record("PNORI", "")
        assert not os.path.exists(os.path.join(tmp_path, "errors"))

    def test_write_exception_logging(self, tmp_path):
        """Test exception handling in write method."""
        writer = FileWriter(str(tmp_path))
        with patch.object(writer, "_get_file_handle", side_effect=Exception("Disk full")):
            with patch("adcp_recorder.export.file_writer.logger") as mock_logger:
                writer.write("PNORI", "data")
                mock_logger.error.assert_called()

    def test_write_record_exception_logging(self, tmp_path):
        """Test exception handling in write_record."""
        writer = FileWriter(str(tmp_path))
        with patch.object(
            writer.parquet_writer, "write_record", side_effect=Exception("Parquet Error")
        ):
            with patch("adcp_recorder.export.file_writer.logger") as mock_logger:
                writer.write_record("PNORI", {"val": 1})
                mock_logger.error.assert_called()

    def test_write_invalid_record_exception_logging(self, tmp_path):
        """Test exception handling in write_invalid_record."""
        writer = FileWriter(str(tmp_path))
        # Trigger exception by passing an invalid path-like object or similar
        with patch("os.makedirs", side_effect=Exception("Permission denied")):
            with patch("adcp_recorder.export.file_writer.logger") as mock_logger:
                writer.write_invalid_record("PNORI", "data")
                mock_logger.error.assert_called()

    def test_close_exception_logging(self, tmp_path):
        """Test exception handling in close."""
        writer = FileWriter(str(tmp_path))
        mock_file = MagicMock()
        mock_file.close.side_effect = Exception("Close failed")
        writer._files["TEST"] = mock_file

        with patch.object(
            writer.parquet_writer, "close", side_effect=Exception("Parquet close failed")
        ):
            with patch("adcp_recorder.export.file_writer.logger") as mock_logger:
                writer.close()
                assert mock_logger.error.call_count >= 2


class TestParquetWriterCoverage:
    """Coverage tests for ParquetWriter."""

    def test_parquet_writer_full_flow(self, tmp_path):
        """Test successful parquet write and buffer rotation."""
        writer = ParquetWriter(str(tmp_path), buffer_size=2)
        writer.write_record("TEST", {"a": 1})
        assert len(writer._buffers["TEST"]) == 1

        # This should trigger flush
        writer.write_record("TEST", {"a": 2})
        assert len(writer._buffers["TEST"]) == 0

        # Check if file exists
        parquet_files = list(Path(tmp_path).glob("**/*.parquet"))
        assert len(parquet_files) == 1

    def test_flush_empty_buffer(self, tmp_path):
        """Test flushing an empty or nonexistent buffer."""
        writer = ParquetWriter(str(tmp_path))
        writer.flush("NONEXISTENT")  # Should not fail
        writer._buffers["EMPTY"] = []
        writer.flush("EMPTY")  # Should not fail

    def test_flush_exception_logging(self, tmp_path):
        """Test exception handling in flush."""
        writer = ParquetWriter(str(tmp_path))
        writer.write_record("PNORS", {"temp": 20})

        with patch.object(writer, "_write_to_parquet", side_effect=Exception("Flush failure")):
            with patch("adcp_recorder.export.parquet_writer.logger") as mock_logger:
                writer.flush()
                mock_logger.error.assert_called()

    def test_write_to_parquet_exception_rethrows(self, tmp_path):
        """Test that _write_to_parquet rethrows after logging."""
        writer = ParquetWriter(str(tmp_path))
        with patch("polars.DataFrame", side_effect=Exception("Polars error")):
            with patch("adcp_recorder.export.parquet_writer.logger") as mock_logger:
                with pytest.raises(Exception, match="Polars error"):
                    writer._write_to_parquet("PNORS", date(2023, 1, 1), [{"test": 1}])
                mock_logger.error.assert_called()
