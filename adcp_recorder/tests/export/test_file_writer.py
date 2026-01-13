"""Tests for FileWriter."""

import os
from datetime import date, datetime
from unittest.mock import patch

import pytest

from adcp_recorder.export.file_writer import FileWriter


class TestFileWriter:
    """Test FileWriter."""

    @pytest.fixture
    def export_dir(self, tmp_path):
        """Create export directory."""
        return str(tmp_path / "export")

    def test_init_creates_directory(self, export_dir):
        """Test that initialization creates the directory."""
        assert not os.path.exists(export_dir)
        FileWriter(export_dir)
        assert os.path.exists(export_dir)

    def test_write_creates_file(self, export_dir):
        """Test writing creates a file."""
        writer = FileWriter(export_dir)
        writer.write("PNORI", "$PNORI,test*00")

        # Check file exists
        date_str = datetime.now().strftime("%Y%m%d")
        expected_file = os.path.join(export_dir, f"PNORI_{date_str}.nmea")
        assert os.path.exists(expected_file)

        # Check content
        with open(expected_file) as f:
            content = f.read()
        assert content == "$PNORI,test*00\n"

    def test_write_appends_newline(self, export_dir):
        """Test that write appends newline if missing."""
        writer = FileWriter(export_dir)
        writer.write("PNORI", "line1")
        writer.write("PNORI", "line2\n")

        date_str = datetime.now().strftime("%Y%m%d")
        expected_file = os.path.join(export_dir, f"PNORI_{date_str}.nmea")

        with open(expected_file) as f:
            lines = f.readlines()

        assert len(lines) == 2
        assert lines[0] == "line1\n"
        assert lines[1] == "line2\n"

    def test_write_multiple_prefixes(self, export_dir):
        """Test writing different prefixes to different files."""
        writer = FileWriter(export_dir)
        writer.write("PNORI", "data1")
        writer.write("PNORS", "data2")

        date_str = datetime.now().strftime("%Y%m%d")
        pnori_file = os.path.join(export_dir, f"PNORI_{date_str}.nmea")
        pnors_file = os.path.join(export_dir, f"PNORS_{date_str}.nmea")

        assert os.path.exists(pnori_file)
        assert os.path.exists(pnors_file)

    def test_rotation(self, export_dir):
        """Test file rotation on new day."""
        # Mock datetime in the module
        with patch("adcp_recorder.export.file_writer.datetime") as mock_datetime:
            # Day 1
            mock_datetime.now.return_value.date.return_value = date(2023, 1, 1)
            mock_datetime.now.return_value.strftime.side_effect = lambda fmt: datetime(
                2023, 1, 1
            ).strftime(fmt)

            writer = FileWriter(export_dir)
            writer.write("PNORI", "day1")

            # Verify day 1 file
            day1_file = os.path.join(export_dir, "PNORI_20230101.nmea")
            assert os.path.exists(day1_file)

            # Advance to day 2
            mock_datetime.now.return_value.date.return_value = date(2023, 1, 2)
            mock_datetime.now.return_value.strftime.side_effect = lambda fmt: datetime(
                2023, 1, 2
            ).strftime(fmt)

            writer.write("PNORI", "day2")

            # Verify day 2 file
            day2_file = os.path.join(export_dir, "PNORI_20230102.nmea")
            assert os.path.exists(day2_file)

            # Verify day 1 file content
            with open(day1_file) as f:
                content = f.read()
            assert content == "day1\n"

            # Verify day 2 file content
            with open(day2_file) as f:
                content = f.read()
            assert content == "day2\n"

    def test_write_error(self, export_dir):
        """Test writing errors."""
        writer = FileWriter(export_dir)
        writer.write_error("Something went wrong")

        date_str = datetime.now().strftime("%Y%m%d")
        error_file = os.path.join(export_dir, f"ERRORS_{date_str}.nmea")

        assert os.path.exists(error_file)
        with open(error_file) as f:
            content = f.read()

        assert "Something went wrong" in content

    def test_close_closes_files(self, export_dir):
        """Test close allows files to be deleted/reopened."""
        writer = FileWriter(export_dir)
        writer.write("PNORI", "test")

        date_str = datetime.now().strftime("%Y%m%d")
        filename = os.path.join(export_dir, f"PNORI_{date_str}.nmea")

        writer.close()

        # Should be able to append
        with open(filename, "a") as f:
            f.write("more")
