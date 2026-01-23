"""Tests for interactive table view component."""

from datetime import date, datetime, time
from unittest.mock import ANY, MagicMock, patch

import pytest

from adcp_recorder.ui.components.table_view import render_column_selector, render_table_view
from adcp_recorder.ui.data_layer import ColumnMetadata, ColumnType, DataSource


class TestTableView:
    """Test suite for table view component."""

    @pytest.fixture
    def mock_data_layer(self):
        """Mock DataLayer."""
        return MagicMock()

    @pytest.fixture
    def mock_st(self):
        """Mock Streamlit."""
        with patch("adcp_recorder.ui.components.table_view.st") as mock_st:
            # Setup session state mock
            mock_st.session_state = {}

            # Smart mock for columns
            def mock_columns(n):
                if isinstance(n, int):
                    return [MagicMock() for _ in range(n)]
                return [MagicMock() for _ in range(len(n))]

            mock_st.columns.side_effect = mock_columns

            # Mock expander to be a context manager
            mock_st.expander.return_value.__enter__.return_value = MagicMock()
            mock_st.container.return_value.__enter__.return_value = MagicMock()

            # Default mocks
            mock_st.button.return_value = False
            mock_st.number_input.return_value = 100
            mock_st.date_input.return_value = date.today()
            mock_st.time_input.return_value = time(12, 0)
            mock_st.selectbox.return_value = "24h"
            mock_st.multiselect.return_value = ["received_at", "vel1"]
            mock_st.text_input.return_value = ""

            yield mock_st

    @pytest.fixture
    def sample_source(self):
        """Create sample DataSource metadata."""
        cols = [
            ColumnMetadata(name="received_at", column_type=ColumnType.TIMESTAMP),
            ColumnMetadata(name="vel1", column_type=ColumnType.NUMERIC),
            ColumnMetadata(name="record_type", column_type=ColumnType.TEXT),
        ]
        return DataSource(
            name="test_source",
            display_name="Test Source",
            columns=cols,
            record_count=1000,
            has_timestamp=True,
            category="test",
        )

    def test_render_table_view_basic(self, mock_data_layer, mock_st, sample_source):
        """Test basic rendering of table view."""
        mock_data_layer.get_source_metadata.return_value = sample_source

        mock_data_layer.query_data.return_value = [
            {"received_at": datetime(2026, 1, 23, 12, 0), "vel1": 1.5, "record_type": "TEST"}
        ]
        mock_data_layer._parse_time_range.return_value = datetime(2026, 1, 22, 12, 0)

        render_table_view(mock_data_layer, "test_source")

        mock_data_layer.query_data.assert_called()
        mock_st.dataframe.assert_called()

    def test_render_table_view_filtering(self, mock_data_layer, mock_st, sample_source):
        """Test client-side filtering logic."""
        mock_data_layer.get_source_metadata.return_value = sample_source

        mock_st.multiselect.return_value = ["record_type"]

        # Only return filter if it's for record_type
        def mock_text_input(label, **kwargs):
            if "record_type" in label:
                return "MATCH"
            return ""

        mock_st.text_input.side_effect = mock_text_input

        mock_data_layer.query_data.return_value = [
            {"record_type": "MATCH_THIS"},
            {"record_type": "OTHER"},
        ]

        render_table_view(mock_data_layer, "test_source")

        # Verify result was filtered
        found_rows_loaded_1 = False
        for call_args in mock_st.metric.call_args_list:
            if call_args.args[0] == "Rows Loaded" and call_args.args[1] == 1:
                found_rows_loaded_1 = True
                break
        assert found_rows_loaded_1

    def test_render_table_view_custom_time(self, mock_data_layer, mock_st, sample_source):
        """Test custom time range selection."""
        mock_data_layer.get_source_metadata.return_value = sample_source

        def mock_selectbox(label, options=None, **kwargs):
            if "Time range" in label:
                return "Custom"
            return "24h"

        mock_st.selectbox.side_effect = mock_selectbox

        render_table_view(mock_data_layer, "test_source")

        mock_data_layer.query_data.assert_called_with(
            source_name="test_source",
            columns=ANY,
            start_time=datetime.combine(date.today(), time(12, 0)),
            end_time=datetime.combine(date.today(), time(12, 0)),
            limit=ANY,
        )

    def test_render_table_view_export(self, mock_data_layer, mock_st, sample_source):
        """Test CSV export functionality."""
        mock_data_layer.get_source_metadata.return_value = sample_source
        mock_data_layer.query_data.return_value = [{"col1": "val1"}]

        def mock_button(label, **kwargs):
            if "Export CSV" in label:
                return True
            return False

        mock_st.button.side_effect = mock_button

        render_table_view(mock_data_layer, "test_source")

        mock_st.download_button.assert_called()

    def test_render_table_view_not_found(self, mock_data_layer, mock_st):
        """Test handling of missing data source."""
        mock_data_layer.get_source_metadata.return_value = None
        render_table_view(mock_data_layer, "missing")
        mock_st.error.assert_called_with("Data source not found: missing")

    def test_render_column_selector(self, mock_st, sample_source):
        """Test standalone column selector."""
        mock_st.multiselect.side_effect = None
        mock_st.multiselect.return_value = ["vel1"]
        result = render_column_selector(sample_source)
        assert result == ["vel1"]
        mock_st.multiselect.assert_called_once()

    def test_render_table_view_error(self, mock_data_layer, mock_st, sample_source):
        """Test error handling during query."""
        mock_data_layer.get_source_metadata.return_value = sample_source
        mock_data_layer.query_data.side_effect = Exception("Query Failed")
        render_table_view(mock_data_layer, "test_source")
        mock_st.error.assert_called_with("Error loading data: Query Failed")

    def test_render_table_view_defaults(self, mock_data_layer, mock_st):
        """Test default column selection fallback."""
        # Create a source WITHOUT mandatory columns (record_type, raw_sentence)
        # to ensure selected_columns stays empty until the fallback logic.
        cols = [
            ColumnMetadata(name="vel1", column_type=ColumnType.NUMERIC),
        ]
        source = DataSource(
            name="minimal_source",
            display_name="Minimal Source",
            columns=cols,
            record_count=100,
            has_timestamp=False,
            category="test",
        )
        mock_data_layer.get_source_metadata.return_value = source

        # Mock multiselect to return empty list first (to trigger fallback)
        mock_st.multiselect.return_value = []

        # Ensure query_data returns data so dataframe is called
        mock_data_layer.query_data.return_value = [{"vel1": 1.0}]

        render_table_view(mock_data_layer, "minimal_source")

        # Verify that query_data was still called (with default columns)
        mock_data_layer.query_data.assert_called()
        # Verify dataframe was called
        mock_st.dataframe.assert_called()

    def test_render_table_view_invalid_column_meta(self, mock_data_layer, mock_st, sample_source):
        """Test skipping columns with missing metadata in filter loop."""
        mock_data_layer.get_source_metadata.return_value = sample_source
        mock_st.multiselect.return_value = ["vel1"]

        # Mock get_column to return None for vel1
        sample_source.get_column = MagicMock(return_value=None)

        render_table_view(mock_data_layer, "test_source")

        # Should not have attempted to render filter widget for vel1
        # (text_input is used for text filters, vel1 is numeric but logic checks meta first)
        # In this specific code path, it continues if col_meta is None
        mock_data_layer.query_data.assert_called()

    def test_render_table_view_clear_filter(self, mock_data_layer, mock_st, sample_source):
        """Test clearing a filter from session state."""
        mock_data_layer.get_source_metadata.return_value = sample_source
        mock_st.multiselect.return_value = ["record_type"]

        # Simulate existing filter in state
        state_key = "table_filter_state_record_type"
        mock_st.session_state[state_key] = ("contains", "OLD_VAL")

        # Simulate empty input from widget
        def mock_text_input(label, **kwargs):
            return ""

        mock_st.text_input.side_effect = mock_text_input

        render_table_view(mock_data_layer, "test_source")

        # Verify filter was removed from state
        assert state_key not in mock_st.session_state
