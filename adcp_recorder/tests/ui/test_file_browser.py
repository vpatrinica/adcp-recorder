"""Tests for the file browser component.

Tests cover directory selector, record type selector, date range picker,
and file tree rendering functionality.
"""

import importlib.util
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# Import file_browser directly without going through components/__init__.py
# This avoids numpy import conflicts with coverage instrumentation
def _import_file_browser():
    """Import file_browser module directly to avoid __init__.py chain."""
    spec = importlib.util.spec_from_file_location(
        "file_browser",
        Path(__file__).parent.parent.parent / "ui" / "components" / "file_browser.py",
    )
    if spec is None or spec.loader is None:
        raise ImportError("Could not load file_browser module")
    module = importlib.util.module_from_spec(spec)
    sys.modules["file_browser_direct"] = module
    spec.loader.exec_module(module)
    return module


_fb = _import_file_browser()
FileSelection = _fb.FileSelection
get_selection_summary = _fb.get_selection_summary
render_date_range_selector = _fb.render_date_range_selector
render_directory_selector = _fb.render_directory_selector
render_record_type_selector = _fb.render_record_type_selector

from adcp_recorder.ui.parquet_data_layer import ParquetDirectory, ParquetFileInfo  # noqa: E402


class TestFileSelection:
    """Tests for FileSelection dataclass."""

    def test_creation(self):
        """Test FileSelection creation."""
        selection = FileSelection(
            data_directory="/data/parquet",
            selected_record_types=["PNORS", "PNORC"],
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
        )

        assert selection.data_directory == "/data/parquet"
        assert len(selection.selected_record_types) == 2
        assert selection.start_date is not None
        assert selection.end_date is not None

    def test_creation_with_none_dates(self):
        """Test FileSelection with None dates."""
        selection = FileSelection(
            data_directory="/data",
            selected_record_types=["PNORS"],
            start_date=None,
            end_date=None,
        )

        assert selection.start_date is None
        assert selection.end_date is None


class TestGetSelectionSummary:
    """Tests for get_selection_summary function."""

    def test_summary_with_dates(self):
        """Test summary with all fields set."""
        today = date.today()
        selection = FileSelection(
            data_directory="/data/parquet",
            selected_record_types=["PNORS", "PNORC"],
            start_date=today - timedelta(days=7),
            end_date=today,
        )

        summary = get_selection_summary(selection)

        assert summary["data_directory"] == "/data/parquet"
        assert summary["record_types"] == ["PNORS", "PNORC"]
        assert summary["start_date"] is not None
        assert summary["end_date"] == today.isoformat()

    def test_summary_with_none_dates(self):
        """Test summary with None dates."""
        selection = FileSelection(
            data_directory="/data",
            selected_record_types=["PNORS"],
            start_date=None,
            end_date=None,
        )

        summary = get_selection_summary(selection)

        assert summary["start_date"] is None
        assert summary["end_date"] is None


class TestRenderDirectorySelector:
    """Tests for render_directory_selector without Streamlit."""

    def test_returns_default_when_no_streamlit(self):
        """Test that default path is returned when Streamlit is not available."""
        # The function should return default_path when HAS_STREAMLIT is False
        # We patch HAS_STREAMLIT to ensure consistent behavior
        with patch.object(_fb, "HAS_STREAMLIT", False):
            result = render_directory_selector(default_path="/default/path")
            assert result == "/default/path"

    def test_returns_empty_default(self):
        """Test with empty default path."""
        with patch.object(_fb, "HAS_STREAMLIT", False):
            result = render_directory_selector()
            assert result == ""


class TestRenderRecordTypeSelector:
    """Tests for render_record_type_selector without Streamlit."""

    def test_returns_all_types_when_no_streamlit(self):
        """Test that all types are returned when Streamlit is not available."""
        with patch.object(_fb, "HAS_STREAMLIT", False):
            types = ["PNORS", "PNORC", "PNORI"]
            result = render_record_type_selector(types)
            assert result == types

    def test_returns_empty_list_for_empty_input(self):
        """Test with empty types list."""
        with patch.object(_fb, "HAS_STREAMLIT", False):
            result = render_record_type_selector([])
            assert result == []


class TestRenderDateRangeSelector:
    """Tests for render_date_range_selector without Streamlit."""

    def test_returns_date_range_when_no_streamlit(self):
        """Test that date range is returned when Streamlit is not available."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        dates = [today, yesterday]

        with patch.object(_fb, "HAS_STREAMLIT", False):
            start, end = render_date_range_selector(dates)
            assert start == yesterday
            assert end == today

    def test_returns_none_for_empty_dates(self):
        """Test with empty dates list."""
        with patch.object(_fb, "HAS_STREAMLIT", False):
            start, end = render_date_range_selector([])
            assert start is None
            assert end is None


class TestFileBrowserIntegration:
    """Integration tests for file browser components."""

    @pytest.fixture
    def sample_directory(self):
        """Create a sample ParquetDirectory for testing."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        file1 = ParquetFileInfo(
            path=Path("/data/PNORS/test1.parquet"),
            record_type="PNORS",
            file_date=today,
            size_bytes=1000,
            modified_at=today,
        )
        file2 = ParquetFileInfo(
            path=Path("/data/PNORS/test2.parquet"),
            record_type="PNORS",
            file_date=yesterday,
            size_bytes=2000,
            modified_at=yesterday,
        )
        file3 = ParquetFileInfo(
            path=Path("/data/PNORC/test3.parquet"),
            record_type="PNORC",
            file_date=today,
            size_bytes=1500,
            modified_at=today,
        )

        return ParquetDirectory(
            base_path=Path("/data"),
            record_types={
                "PNORS": {today: [file1], yesterday: [file2]},
                "PNORC": {today: [file3]},
            },
        )

    def test_directory_structure(self, sample_directory):
        """Test directory structure is correct."""
        assert len(sample_directory.record_types) == 2
        assert "PNORS" in sample_directory.record_types
        assert "PNORC" in sample_directory.record_types

    def test_get_all_dates(self, sample_directory):
        """Test getting all dates."""
        dates = sample_directory.get_all_dates()
        assert len(dates) == 2

    def test_get_files_for_selection(self, sample_directory):
        """Test getting files for selection."""
        files = sample_directory.get_files_for_selection(record_types=["PNORS"])
        assert len(files) == 2

        files = sample_directory.get_files_for_selection(record_types=["PNORC"])
        assert len(files) == 1


class TestFileBrowserMockedStreamlit:
    """Tests for file browser with mocked Streamlit."""

    def test_render_directory_selector_with_mock_st(self):
        """Test directory selector with mocked Streamlit."""
        mock_st = MagicMock()
        mock_st.text_input.return_value = "/user/selected/path"
        mock_st.button.return_value = False
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        with (
            patch.object(_fb, "HAS_STREAMLIT", True),
            patch.object(_fb, "st", mock_st),
        ):
            result = render_directory_selector(default_path="/default")

            assert result == "/user/selected/path"
            mock_st.subheader.assert_called_once()

    def test_render_record_type_selector_with_mock_st(self):
        """Test record type selector with mocked Streamlit."""
        mock_st = MagicMock()
        mock_st.checkbox.return_value = True  # Select all checked

        with (
            patch.object(_fb, "HAS_STREAMLIT", True),
            patch.object(_fb, "st", mock_st),
        ):
            types = ["PNORS", "PNORC"]
            result = render_record_type_selector(types)

            # When select_all is True, should return all types
            assert result == types

    def test_render_record_type_selector_select_subset(self):
        """Test record type selector with subset selection."""
        mock_st = MagicMock()
        mock_st.checkbox.return_value = False  # Select all not checked
        mock_st.multiselect.return_value = ["PNORS"]

        with (
            patch.object(_fb, "HAS_STREAMLIT", True),
            patch.object(_fb, "st", mock_st),
        ):
            types = ["PNORS", "PNORC"]
            result = render_record_type_selector(types)

            assert result == ["PNORS"]

    def test_render_date_range_selector_with_mock_st(self):
        """Test date range selector with mocked Streamlit."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        mock_st = MagicMock()
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.date_input.side_effect = [yesterday, today]

        with (
            patch.object(_fb, "HAS_STREAMLIT", True),
            patch.object(_fb, "st", mock_st),
        ):
            dates = [today, yesterday]
            start, end = render_date_range_selector(dates)

            assert start == yesterday
            assert end == today

    def test_render_record_type_selector_empty_with_mock_st(self):
        """Test record type selector with empty list."""
        mock_st = MagicMock()

        with (
            patch.object(_fb, "HAS_STREAMLIT", True),
            patch.object(_fb, "st", mock_st),
        ):
            result = render_record_type_selector([])

            assert result == []
            mock_st.info.assert_called_once()

    def test_render_date_range_empty_with_mock_st(self):
        """Test date range selector with empty dates."""
        mock_st = MagicMock()

        with (
            patch.object(_fb, "HAS_STREAMLIT", True),
            patch.object(_fb, "st", mock_st),
        ):
            start, end = render_date_range_selector([])

            assert start is None
            assert end is None
            mock_st.info.assert_called_once()
