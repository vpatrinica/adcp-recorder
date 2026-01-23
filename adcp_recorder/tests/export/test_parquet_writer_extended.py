"""Extended tests for ParquetWriter to reach 100% coverage."""

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from adcp_recorder.export.parquet_writer import ParquetWriter


class TestParquetWriterExtended:
    """Extended tests for ParquetWriter."""

    def test_write_to_parquet_cleanup_success(self, tmp_path):
        """Test that temp file is unlinked on write error."""
        writer = ParquetWriter(str(tmp_path))

        # We need to trigger an exception in _write_to_parquet
        # but ensure the temp file exists so it tries to unlink it.

        with patch("polars.DataFrame.write_parquet") as mock_write:
            mock_write.side_effect = Exception("Write failed")

            # Mock temp_path.exists and temp_path.unlink
            # Since _write_to_parquet creates paths locally, we patch pathlib.Path.exists and unlink
            # or more reliably, patch the objects inside the method.

            with patch("adcp_recorder.export.parquet_writer.Path.exists", return_value=True):
                with patch("adcp_recorder.export.parquet_writer.Path.unlink") as mock_unlink:
                    with pytest.raises(Exception, match="Write failed"):
                        writer._write_to_parquet("TEST", date(2024, 1, 1), [{"a": 1}])

                    mock_unlink.assert_called_once()

    def test_write_to_parquet_cleanup_os_error_ignored(self, tmp_path):
        """Test that OSError during unlink is ignored (line 142)."""
        writer = ParquetWriter(str(tmp_path))

        with patch("polars.DataFrame.write_parquet", side_effect=Exception("Write failed")):
            with patch("adcp_recorder.export.parquet_writer.Path.exists", return_value=True):
                with patch(
                    "adcp_recorder.export.parquet_writer.Path.unlink",
                    side_effect=OSError("Unlink failed"),
                ):
                    # Should still raise the original Exception, but not the OSError
                    with pytest.raises(Exception, match="Write failed"):
                        writer._write_to_parquet("TEST", date(2024, 1, 1), [{"a": 1}])

    def test_ensure_base_path_already_exists(self, tmp_path):
        """Cover _ensure_base_path when it already exists."""
        parquet_dir = tmp_path / "parquet"
        parquet_dir.mkdir()

        # Should not raise
        ParquetWriter(str(tmp_path))

    def test_flush_all_prefixes(self, tmp_path):
        """Cover flush() without arguments."""
        writer = ParquetWriter(str(tmp_path))
        writer.write_record("A", {"v": 1})
        writer.write_record("B", {"v": 2})

        writer.flush()
        assert len(writer._buffers["A"]) == 0
        assert len(writer._buffers["B"]) == 0

        # Check files
        files = list(Path(tmp_path).glob("**/*.parquet"))
        assert len(files) == 2

    def test_get_partition_path_creation(self, tmp_path):
        """Cover OS path creation in _get_partition_path."""
        writer = ParquetWriter(str(tmp_path))
        p = writer._get_partition_path("NEW_TYPE", date(2024, 5, 20))
        assert p.exists()
        assert "NEW_TYPE" in str(p)
        assert "date=2024-05-20" in str(p)
