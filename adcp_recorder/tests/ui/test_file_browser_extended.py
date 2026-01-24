"""Extended tests for file_browser component."""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import adcp_recorder.ui.components.file_browser as fb
from adcp_recorder.ui.parquet_data_layer import ParquetDirectory, ParquetFileInfo


class TestFileBrowserExtended:
    """Extended tests for file_browser component."""

    @pytest.fixture
    def mock_st(self):
        """Provides a mocked streamlit object."""
        with patch.object(fb, "HAS_STREAMLIT", True):
            with patch.object(fb, "st", MagicMock()) as mock_st:
                # Mock session_state to support both attr and dict access
                class MockSessionState(dict):
                    def __getattr__(self, key):
                        try:
                            return self[key]
                        except KeyError:
                            raise AttributeError(key)

                    def __setattr__(self, key, value):
                        self[key] = value

                mock_st.session_state = MockSessionState()
                mock_st.columns.return_value = [MagicMock(), MagicMock()]
                mock_st.expander.return_value.__enter__.return_value = MagicMock()
                yield mock_st

    def test_render_directory_selector_refresh(self, mock_st):
        """Cover lines 64-65 (refresh button)."""
        mock_st.button.return_value = True
        mock_layer = MagicMock()
        mock_st.session_state["parquet_data_layer"] = mock_layer

        fb.render_directory_selector()
        mock_layer.refresh.assert_called_once()

    def test_render_file_tree_logic(self, mock_st):
        """Cover lines 179-208 (file tree rendering)."""
        today = date.today()
        from datetime import datetime

        info = ParquetFileInfo(Path("f.pq"), "T", today, 0, datetime.now())
        structure = ParquetDirectory(Path("/"), {"T": {today: [info]}})

        mock_st.multiselect.return_value = [today]

        selection = fb.render_file_tree(structure)
        assert selection == {"T": [today]}

        # Test empty structure
        structure_empty = ParquetDirectory(Path("/"), {})
        assert fb.render_file_tree(structure_empty) == {}
        mock_st.info.assert_called()

    def test_render_file_browser_full_flow(self, mock_st):
        """Cover lines 225-314 (full browser logic)."""
        mock_layer = MagicMock()
        today = date.today()
        mock_layer.get_file_structure.return_value = ParquetDirectory(Path("/"), {"T": {today: []}})
        mock_st.text_input.return_value = "/data"
        mock_st.button.return_value = True  # For Load Data button

        # Mock load_data result
        mock_layer.load_data.return_value = {"view": 100}

        fb.render_file_browser(mock_layer)
        mock_st.success.assert_called()

    def test_render_file_browser_errors(self, mock_st):
        """Cover error handling in load_data (lines 300-312)."""
        mock_layer = MagicMock()
        today = date.today()
        mock_layer.get_file_structure.return_value = ParquetDirectory(Path("/"), {"T": {today: []}})
        mock_st.text_input.return_value = "/data"
        mock_st.button.return_value = True  # Trigger load

        # Case 1: Lock error
        mock_layer.load_data.side_effect = Exception("Database is locked")
        fb.render_file_browser(mock_layer)
        mock_st.error.assert_any_call(AnyStringMatching(".*locked.*"))

        # Case 2: Permission error
        mock_st.error.reset_mock()
        mock_layer.load_data.side_effect = Exception("Permission denied")
        fb.render_file_browser(mock_layer)
        mock_st.error.assert_any_call(AnyStringMatching(".*Permission.*"))

        # Case 3: Other error
        mock_st.error.reset_mock()
        mock_layer.load_data.side_effect = Exception("Random error")
        fb.render_file_browser(mock_layer)
        mock_st.error.assert_any_call("❌ **Load failed:** Random error")

    def test_render_file_browser_empty_inputs(self, mock_st):
        """Cover cases with missing data or dir."""
        mock_layer = MagicMock()

        # No data_dir
        mock_st.text_input.return_value = ""
        assert fb.render_file_browser(mock_layer) is None
        mock_st.warning.assert_called_with("Please enter a data directory path.")

        # Directory change logic
        mock_st.text_input.return_value = "/new"
        mock_st.session_state["browser_current_data_dir"] = "/old"
        mock_layer.get_file_structure.return_value = None
        fb.render_file_browser(mock_layer)
        mock_layer.set_data_directory.assert_called_with("/new")

        # Empty structure case (record_types empty)
        mock_st.text_input.return_value = "/valid"
        mock_layer.get_file_structure.return_value = ParquetDirectory(Path("/"), {})
        assert fb.render_file_browser(mock_layer) is None
        mock_st.error.assert_called()

    def test_render_file_browser_empty_load_result(self, mock_st):
        """Cover line 298 (warning on empty load result)."""
        mock_layer = MagicMock()
        mock_layer.get_file_structure.return_value = ParquetDirectory(
            Path("/"), {"T": {date.today(): []}}
        )
        mock_st.text_input.return_value = "/data"
        mock_st.button.return_value = True
        mock_layer.load_data.return_value = {}  # Empty result

        fb.render_file_browser(mock_layer)
        mock_st.warning.assert_called_with("No data loaded. Check your selection.")

    def test_import_failure_no_streamlit(self):
        """Cover lines 15-17 (import failure simulation)."""
        import importlib
        import sys

        # Save original streamlit
        orig_st = sys.modules.get("streamlit")

        try:
            # Force ImportError on next import
            with patch.dict(sys.modules, {"streamlit": None}):
                # Reload module to trigger the except block
                importlib.reload(fb)

                assert fb.HAS_STREAMLIT is False
                assert fb.st is None

                # Test functions in no-streamlit mode
                assert fb.render_directory_selector(default_path="/d") == "/d"
                assert fb.render_record_type_selector(["A"]) == ["A"]
                assert fb.render_date_range_selector([]) == (None, None)
                assert fb.render_file_tree(MagicMock()) == {}
                assert fb.render_file_browser(MagicMock()) is None
        finally:
            # Restore original state
            if orig_st:
                sys.modules["streamlit"] = orig_st
            else:
                sys.modules.pop("streamlit", None)
            importlib.reload(fb)


# Helper for string matching in assert
class AnyStringMatching:
    def __init__(self, pattern):
        import re

        self.pattern = re.compile(pattern, re.IGNORECASE | re.DOTALL)

    def __eq__(self, other):
        return isinstance(other, str) and self.pattern.match(other)
