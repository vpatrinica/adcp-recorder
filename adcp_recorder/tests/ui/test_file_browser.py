"""Tests for the file browser component.

Tests cover directory selector, record type selector, date range picker,
and file tree rendering functionality.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

# Standard import
from adcp_recorder.ui.components.file_browser import (
    FileSelection,
    get_selection_summary,
    render_date_range_selector,
    render_directory_selector,
    render_file_browser,
    render_file_tree,
    render_record_type_selector,
)
from adcp_recorder.ui.parquet_data_layer import ParquetDirectory


class MockSessionState(dict):
    """Mock session state allowing attribute access."""

    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value


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
    """Tests for render_directory_selector."""

    @patch("adcp_recorder.ui.components.file_browser.st")
    def test_render_directory_selector_basic(self, mock_st):
        """Test basic rendering."""
        mock_st.text_input.return_value = "/path/to/data"
        mock_st.button.return_value = False
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        result = render_directory_selector(default_path="/default")

        assert result == "/path/to/data"
        mock_st.text_input.assert_called_with(
            "Parquet data directory",
            value="/default",
            key="data_dir_input",
            help="Path to directory containing Parquet files",
        )

    @patch("adcp_recorder.ui.components.file_browser.st")
    def test_render_directory_selector_refresh(self, mock_st):
        """Test refresh button interaction."""
        mock_st.text_input.return_value = "/path"
        mock_st.button.return_value = True
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Mock session state
        mock_st.session_state = MockSessionState({"parquet_data_layer": MagicMock()})

        render_directory_selector()

        mock_st.session_state["parquet_data_layer"].refresh.assert_called_once()

    def test_no_streamlit(self):
        """Test fallback when streamlit is not present."""
        with patch("adcp_recorder.ui.components.file_browser.HAS_STREAMLIT", False):
            assert render_directory_selector(default_path="/abc") == "/abc"


class TestRenderRecordTypeSelector:
    """Tests for render_record_type_selector."""

    @patch("adcp_recorder.ui.components.file_browser.st")
    def test_render_basic(self, mock_st):
        """Test basic rendering with subset selection."""
        mock_st.checkbox.return_value = False
        mock_st.multiselect.return_value = ["A"]

        result = render_record_type_selector(["A", "B"])
        assert result == ["A"]

    @patch("adcp_recorder.ui.components.file_browser.st")
    def test_select_all(self, mock_st):
        """Test select all checkbox."""
        mock_st.checkbox.return_value = True

        result = render_record_type_selector(["A", "B"])
        assert result == ["A", "B"]
        mock_st.multiselect.assert_not_called()

    @patch("adcp_recorder.ui.components.file_browser.st")
    def test_empty_types(self, mock_st):
        """Test with empty available types."""
        result = render_record_type_selector([])
        assert result == []
        mock_st.info.assert_called_with("No record types available. Check the data directory.")

    def test_no_streamlit(self):
        """Test no streamlit fallback."""
        with patch("adcp_recorder.ui.components.file_browser.HAS_STREAMLIT", False):
            assert render_record_type_selector(["A"]) == ["A"]


class TestRenderDateRangeSelector:
    """Tests for render_date_range_selector."""

    @patch("adcp_recorder.ui.components.file_browser.st")
    def test_render_basic(self, mock_st):
        """Test basic rendering."""
        d1 = date(2026, 1, 1)
        d2 = date(2026, 1, 2)
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.date_input.side_effect = [d1, d2]

        start, end = render_date_range_selector([d1, d2])
        assert start == d1
        assert end == d2

    @patch("adcp_recorder.ui.components.file_browser.st")
    def test_empty_dates(self, mock_st):
        """Test with empty dates."""
        start, end = render_date_range_selector([])
        assert start is None
        assert end is None
        mock_st.info.assert_called_with("No dates available.")

    def test_no_streamlit(self):
        """Test no streamlit fallback."""
        d1 = date(2026, 1, 1)
        with patch("adcp_recorder.ui.components.file_browser.HAS_STREAMLIT", False):
            assert render_date_range_selector([d1]) == (d1, d1)
            assert render_date_range_selector([]) == (None, None)


class TestRenderFileTree:
    """Tests for render_file_tree."""

    @patch("adcp_recorder.ui.components.file_browser.st")
    def test_render_tree(self, mock_st):
        """Test file tree rendering."""
        mock_st.expander.return_value.__enter__.return_value = MagicMock()
        mock_st.multiselect.return_value = [date(2026, 1, 1)]

        structure = MagicMock(spec=ParquetDirectory)
        structure.record_types = {"PNORS": {date(2026, 1, 1): ["file1"]}}

        result = render_file_tree(structure)
        assert result == {"PNORS": [date(2026, 1, 1)]}
        mock_st.expander.assert_called()

    @patch("adcp_recorder.ui.components.file_browser.st")
    def test_empty_structure(self, mock_st):
        """Test empty structure."""
        structure = MagicMock(spec=ParquetDirectory)
        structure.record_types = {}

        result = render_file_tree(structure)
        assert result == {}
        mock_st.info.assert_called()

    def test_no_streamlit(self):
        """Test no streamlit fallback."""
        with patch("adcp_recorder.ui.components.file_browser.HAS_STREAMLIT", False):
            assert render_file_tree(MagicMock()) == {}


class TestRenderFileBrowser:
    """Tests for complete file browser."""

    @patch("adcp_recorder.ui.components.file_browser.st")
    @patch("adcp_recorder.ui.components.file_browser.render_directory_selector")
    def test_render_browser_no_dir(self, mock_dir_sel, mock_st):
        """Test when no directory is selected."""
        mock_dir_sel.return_value = ""
        mock_st.session_state = MockSessionState()

        result = render_file_browser(MagicMock())
        assert result is None
        mock_st.warning.assert_called()

    @patch("adcp_recorder.ui.components.file_browser.st")
    @patch("adcp_recorder.ui.components.file_browser.render_directory_selector")
    def test_render_browser_no_files(self, mock_dir_sel, mock_st):
        """Test when directory has no files."""
        mock_dir_sel.return_value = "/data"
        mock_st.session_state = MockSessionState()

        layer = MagicMock()
        layer.get_file_structure.return_value = None

        result = render_file_browser(layer)
        assert result is None
        mock_st.error.assert_called()

    @patch("adcp_recorder.ui.components.file_browser.st")
    @patch("adcp_recorder.ui.components.file_browser.render_directory_selector")
    @patch("adcp_recorder.ui.components.file_browser.render_record_type_selector")
    @patch("adcp_recorder.ui.components.file_browser.render_date_range_selector")
    def test_render_browser_load_success(self, mock_dates, mock_types, mock_dir, mock_st):
        """Test successful loading flow."""
        mock_dir.return_value = "/data"
        mock_types.return_value = ["PNORS"]
        mock_dates.return_value = (None, None)

        mock_st.session_state = MockSessionState()
        mock_st.button.return_value = True  # Load clicked

        layer = MagicMock()
        structure = MagicMock()
        structure.record_types = {"PNORS": {}}
        structure.get_all_dates.return_value = []
        layer.get_file_structure.return_value = structure
        layer.load_data.return_value = {"PNORS": 100}

        result = render_file_browser(layer)

        assert isinstance(result, FileSelection)
        mock_st.success.assert_called()
        layer.load_data.assert_called_with(record_types=["PNORS"], start_date=None, end_date=None)

    @patch("adcp_recorder.ui.components.file_browser.st")
    @patch("adcp_recorder.ui.components.file_browser.render_directory_selector")
    @patch("adcp_recorder.ui.components.file_browser.render_record_type_selector")
    @patch("adcp_recorder.ui.components.file_browser.render_date_range_selector")
    def test_render_browser_load_empty(self, mock_dates, mock_types, mock_dir, mock_st):
        """Test load yielding no results."""
        mock_dir.return_value = "/data"
        mock_types.return_value = ["PNORS"]
        mock_dates.return_value = (None, None)

        mock_st.session_state = MockSessionState()
        mock_st.button.return_value = True

        layer = MagicMock()
        structure = MagicMock()
        structure.record_types = {"PNORS": {}}
        structure.get_all_dates.return_value = []
        layer.get_file_structure.return_value = structure
        layer.load_data.return_value = {}  # Empty result

        render_file_browser(layer)

        mock_st.warning.assert_called_with("No data loaded. Check your selection.")

    @patch("adcp_recorder.ui.components.file_browser.st")
    @patch("adcp_recorder.ui.components.file_browser.render_directory_selector")
    @patch("adcp_recorder.ui.components.file_browser.render_record_type_selector")
    @patch("adcp_recorder.ui.components.file_browser.render_date_range_selector")
    def test_render_browser_load_errors(self, mock_dates, mock_types, mock_dir, mock_st):
        """Test various load error scenarios."""
        mock_dir.return_value = "/data"
        mock_types.return_value = ["PNORS"]
        mock_dates.return_value = (None, None)
        mock_st.session_state = MockSessionState()
        mock_st.button.return_value = True

        layer = MagicMock()
        structure = MagicMock()
        structure.record_types = {"PNORS": {}}
        structure.get_all_dates.return_value = []
        layer.get_file_structure.return_value = structure

        # Test generic error
        layer.load_data.side_effect = Exception("Generic Error")
        render_file_browser(layer)
        mock_st.error.assert_called()
        assert "Load failed" in mock_st.error.call_args[0][0]

        # Test lock error
        layer.load_data.side_effect = Exception("Database is locked")
        render_file_browser(layer)
        assert "File is locked" in mock_st.error.call_args[0][0]

        # Test permission error
        layer.load_data.side_effect = Exception("Permission denied")
        render_file_browser(layer)
        assert "Permission denied" in mock_st.error.call_args[0][0]

    def test_no_streamlit(self):
        """Test no streamlit fallback for main browser."""
        with patch("adcp_recorder.ui.components.file_browser.HAS_STREAMLIT", False):
            assert render_file_browser(MagicMock()) is None
