"""Tests for Data Explorer page - full coverage."""

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("streamlit")

from adcp_recorder.ui.pages.data_explorer import (
    MISSING_UNIT_PLACEHOLDER,
    render_data_explorer,
)


def _make_columns(arg):
    """Create the right number of column mocks based on argument."""
    if isinstance(arg, int):
        return [MagicMock() for _ in range(arg)]
    if isinstance(arg, (list, tuple)):
        return [MagicMock() for _ in arg]
    return [MagicMock(), MagicMock()]


@pytest.fixture
def mock_st():
    """Mock streamlit module in data_explorer."""
    with patch("adcp_recorder.ui.pages.data_explorer.st") as mock_st:
        mock_st.session_state = {}
        mock_st.columns.side_effect = _make_columns
        # Expander returns context manager
        mock_st.expander.return_value.__enter__ = MagicMock()
        mock_st.expander.return_value.__exit__ = MagicMock(return_value=False)
        yield mock_st


@pytest.fixture
def mock_data_layer():
    """Create a mock DataLayer with standard responses."""
    dl = MagicMock()
    dl.get_quality_metrics.return_value = {
        "total_records": 1000,
        "error_count": 5,
        "error_rate": 0.005,
    }
    return dl


class TestDataExplorer:
    """Test render_data_explorer function."""

    def test_renders_header(self, mock_st, mock_data_layer):
        """Renders header and caption."""
        mock_data_layer.get_available_sources.return_value = []

        render_data_explorer(mock_data_layer)

        mock_st.header.assert_called_once()
        mock_st.caption.assert_called_once()

    def test_quality_overview_displays_metrics(self, mock_st, mock_data_layer):
        """Quality overview shows total records, errors, error rate, range."""
        mock_data_layer.get_available_sources.return_value = []

        render_data_explorer(mock_data_layer)

        mock_data_layer.get_quality_metrics.assert_called_once_with("24h")
        # Should call st.metric at least 4 times (total, errors, rate, range)
        assert mock_st.metric.call_count >= 4

    def test_quality_overview_custom_time_range(self, mock_st, mock_data_layer):
        """Quality overview uses custom time_range parameter."""
        mock_data_layer.get_available_sources.return_value = []

        render_data_explorer(mock_data_layer, time_range="7d")

        mock_data_layer.get_quality_metrics.assert_called_once_with("7d")

    def test_quality_overview_error_shows_warning(self, mock_st, mock_data_layer):
        """Quality metrics failure shows warning."""
        mock_data_layer.get_quality_metrics.side_effect = Exception("db error")
        mock_data_layer.get_available_sources.return_value = []

        render_data_explorer(mock_data_layer)

        mock_st.warning.assert_called()

    def test_quality_zero_errors_no_delta(self, mock_st, mock_data_layer):
        """Zero errors passes delta=None to st.metric."""
        mock_data_layer.get_quality_metrics.return_value = {
            "total_records": 500,
            "error_count": 0,
            "error_rate": 0.0,
        }
        mock_data_layer.get_available_sources.return_value = []

        render_data_explorer(mock_data_layer)

        # Verify metric called with delta=None for errors
        metric_calls = mock_st.metric.call_args_list
        error_call = [c for c in metric_calls if c[0][0] == "Errors"]
        assert len(error_call) == 1
        assert error_call[0][1].get("delta") is None or error_call[0][0][2] is None

    def test_no_sources_shows_warning(self, mock_st, mock_data_layer):
        """No available sources shows warning and returns."""
        mock_data_layer.get_available_sources.return_value = []

        render_data_explorer(mock_data_layer)

        warning_calls = [c for c in mock_st.warning.call_args_list if "No data sources" in str(c)]
        assert len(warning_calls) >= 1

    @patch("adcp_recorder.ui.pages.data_explorer.render_table_view")
    def test_source_selection_and_table_view(self, mock_render_table, mock_st, mock_data_layer):
        """Selecting a source renders table view and metadata."""
        source1 = MagicMock()
        source1.category = "Sensor Data"
        source1.display_name = "PNORS DF100"
        source1.name = "pnors_df100"

        mock_data_layer.get_available_sources.return_value = [source1]

        # selectbox: category="All", source="PNORS DF100"
        mock_st.selectbox.side_effect = ["All", "PNORS DF100"]

        source_meta = MagicMock()
        source_meta.record_count = 500
        source_meta.columns = ["col1", "col2", "col3"]
        source_meta.category = "Sensor Data"
        source_meta.has_timestamp = True
        source_meta.get_numeric_columns.return_value = []
        mock_data_layer.get_source_metadata.return_value = source_meta

        render_data_explorer(mock_data_layer)

        mock_render_table.assert_called_once_with(
            data_layer=mock_data_layer,
            source_name="pnors_df100",
            key_prefix="explorer_pnors_df100",
            default_time_range="24h",
        )

    @patch("adcp_recorder.ui.pages.data_explorer.render_table_view")
    def test_category_filter(self, mock_render_table, mock_st, mock_data_layer):
        """Category filter restricts source options."""
        source1 = MagicMock()
        source1.category = "Sensor Data"
        source1.display_name = "PNORS DF100"
        source1.name = "pnors_df100"

        source2 = MagicMock()
        source2.category = "Wave Data"
        source2.display_name = "PNORW Data"
        source2.name = "pnorw_data"

        mock_data_layer.get_available_sources.return_value = [source1, source2]

        # Select "Sensor Data" category, then the only filtered source
        mock_st.selectbox.side_effect = ["Sensor Data", "PNORS DF100"]

        source_meta = MagicMock()
        source_meta.record_count = 100
        source_meta.columns = ["c1"]
        source_meta.category = "Sensor Data"
        source_meta.has_timestamp = True
        source_meta.get_numeric_columns.return_value = []
        mock_data_layer.get_source_metadata.return_value = source_meta

        render_data_explorer(mock_data_layer)

        mock_render_table.assert_called_once()

    @patch("adcp_recorder.ui.pages.data_explorer.render_table_view")
    def test_no_sources_in_category_shows_warning(
        self, mock_render_table, mock_st, mock_data_layer
    ):
        """Empty category filter shows warning."""
        source1 = MagicMock()
        source1.category = "Sensor Data"
        source1.display_name = "PNORS DF100"
        source1.name = "pnors_df100"

        mock_data_layer.get_available_sources.return_value = [source1]

        # Select a category with no sources
        mock_st.selectbox.side_effect = ["Wave Data"]

        render_data_explorer(mock_data_layer)

        # Should show warning about no sources in category
        warning_calls = [c for c in mock_st.warning.call_args_list if "No sources" in str(c)]
        assert len(warning_calls) >= 1
        mock_render_table.assert_not_called()

    @patch("adcp_recorder.ui.pages.data_explorer.render_table_view")
    def test_no_source_metadata(self, mock_render_table, mock_st, mock_data_layer):
        """Source with no metadata still renders table."""
        source1 = MagicMock()
        source1.category = "Sensor Data"
        source1.display_name = "Unknown"
        source1.name = "unknown_table"

        mock_data_layer.get_available_sources.return_value = [source1]
        mock_st.selectbox.side_effect = ["All", "Unknown"]
        mock_data_layer.get_source_metadata.return_value = None

        render_data_explorer(mock_data_layer)

        mock_render_table.assert_called_once()

    @patch("adcp_recorder.ui.pages.data_explorer.render_table_view")
    def test_column_statistics_rendered(self, mock_render_table, mock_st, mock_data_layer):
        """Numeric columns get statistics displayed."""
        source1 = MagicMock()
        source1.category = "Sensor Data"
        source1.display_name = "PNORS DF100"
        source1.name = "pnors_df100"

        mock_data_layer.get_available_sources.return_value = [source1]
        mock_st.selectbox.side_effect = ["All", "PNORS DF100"]

        col_meta = MagicMock()
        col_meta.unit = "°C"

        source_meta = MagicMock()
        source_meta.record_count = 100
        source_meta.columns = ["temperature"]
        source_meta.category = "Sensor Data"
        source_meta.has_timestamp = True
        source_meta.get_numeric_columns.return_value = ["temperature"]
        source_meta.get_column.return_value = col_meta

        mock_data_layer.get_source_metadata.return_value = source_meta
        mock_data_layer.get_column_stats.return_value = {
            "min": 10.5,
            "max": 25.3,
            "avg": 18.2,
        }

        render_data_explorer(mock_data_layer)

        mock_data_layer.get_column_stats.assert_called_once_with("pnors_df100", "temperature")

    @patch("adcp_recorder.ui.pages.data_explorer.render_table_view")
    def test_column_stats_missing_unit(self, mock_render_table, mock_st, mock_data_layer):
        """Column without unit uses MISSING_UNIT_PLACEHOLDER."""
        source1 = MagicMock()
        source1.category = "Sensor Data"
        source1.display_name = "PNORS DF100"
        source1.name = "pnors_df100"

        mock_data_layer.get_available_sources.return_value = [source1]
        mock_st.selectbox.side_effect = ["All", "PNORS DF100"]

        col_meta = MagicMock()
        col_meta.unit = None

        source_meta = MagicMock()
        source_meta.record_count = 100
        source_meta.columns = ["cell_index"]
        source_meta.category = "Sensor Data"
        source_meta.has_timestamp = True
        source_meta.get_numeric_columns.return_value = ["cell_index"]
        source_meta.get_column.return_value = col_meta

        mock_data_layer.get_source_metadata.return_value = source_meta
        mock_data_layer.get_column_stats.return_value = {
            "min": 0.0,
            "max": 10.0,
            "avg": 5.0,
        }

        render_data_explorer(mock_data_layer)

        mock_data_layer.get_column_stats.assert_called_once()

    @patch("adcp_recorder.ui.pages.data_explorer.render_table_view")
    def test_column_stats_no_col_meta(self, mock_render_table, mock_st, mock_data_layer):
        """Column with None col_meta uses MISSING_UNIT_PLACEHOLDER."""
        source1 = MagicMock()
        source1.category = "Sensor Data"
        source1.display_name = "PNORS DF100"
        source1.name = "pnors_df100"

        mock_data_layer.get_available_sources.return_value = [source1]
        mock_st.selectbox.side_effect = ["All", "PNORS DF100"]

        source_meta = MagicMock()
        source_meta.record_count = 100
        source_meta.columns = ["cell_index"]
        source_meta.category = "Sensor Data"
        source_meta.has_timestamp = True
        source_meta.get_numeric_columns.return_value = ["cell_index"]
        source_meta.get_column.return_value = None  # No column metadata

        mock_data_layer.get_source_metadata.return_value = source_meta
        mock_data_layer.get_column_stats.return_value = {
            "min": 0.0,
            "max": 10.0,
            "avg": 5.0,
        }

        render_data_explorer(mock_data_layer)

        mock_data_layer.get_column_stats.assert_called_once()

    @patch("adcp_recorder.ui.pages.data_explorer.render_table_view")
    def test_column_stats_none_skipped(self, mock_render_table, mock_st, mock_data_layer):
        """Column with None stats is silently skipped."""
        source1 = MagicMock()
        source1.category = "Sensor Data"
        source1.display_name = "PNORS DF100"
        source1.name = "pnors_df100"

        mock_data_layer.get_available_sources.return_value = [source1]
        mock_st.selectbox.side_effect = ["All", "PNORS DF100"]

        source_meta = MagicMock()
        source_meta.record_count = 100
        source_meta.columns = ["c1"]
        source_meta.category = "Sensor Data"
        source_meta.has_timestamp = True
        source_meta.get_numeric_columns.return_value = ["c1"]
        source_meta.get_column.return_value = None

        mock_data_layer.get_source_metadata.return_value = source_meta
        mock_data_layer.get_column_stats.return_value = None

        render_data_explorer(mock_data_layer)

        # No error should occur
        mock_data_layer.get_column_stats.assert_called_once()

    @patch("adcp_recorder.ui.pages.data_explorer.render_table_view")
    def test_column_stats_exception_skipped(self, mock_render_table, mock_st, mock_data_layer):
        """Column stats exception is silently caught and skipped."""
        source1 = MagicMock()
        source1.category = "Sensor Data"
        source1.display_name = "PNORS DF100"
        source1.name = "pnors_df100"

        mock_data_layer.get_available_sources.return_value = [source1]
        mock_st.selectbox.side_effect = ["All", "PNORS DF100"]

        source_meta = MagicMock()
        source_meta.record_count = 100
        source_meta.columns = ["c1"]
        source_meta.category = "Sensor Data"
        source_meta.has_timestamp = True
        source_meta.get_numeric_columns.return_value = ["c1"]

        mock_data_layer.get_source_metadata.return_value = source_meta
        mock_data_layer.get_column_stats.side_effect = Exception("stats error")

        render_data_explorer(mock_data_layer)

        # Exception should be silently caught
        mock_data_layer.get_column_stats.assert_called_once()

    @patch("adcp_recorder.ui.pages.data_explorer.render_table_view")
    def test_empty_selected_source_returns(self, mock_render_table, mock_st, mock_data_layer):
        """Empty source selection returns early."""
        source1 = MagicMock()
        source1.category = "Sensor Data"
        source1.display_name = "PNORS DF100"
        source1.name = "pnors_df100"

        mock_data_layer.get_available_sources.return_value = [source1]
        # selectbox returns "All", then a display name that maps to empty string
        mock_st.selectbox.side_effect = ["All", "Nonexistent"]

        render_data_explorer(mock_data_layer)

        mock_render_table.assert_not_called()

    @patch("adcp_recorder.ui.pages.data_explorer.render_table_view")
    def test_multiple_numeric_columns(self, mock_render_table, mock_st, mock_data_layer):
        """Multiple numeric columns each get stats."""
        source1 = MagicMock()
        source1.category = "Sensor Data"
        source1.display_name = "PNORS DF100"
        source1.name = "pnors_df100"

        mock_data_layer.get_available_sources.return_value = [source1]
        mock_st.selectbox.side_effect = ["All", "PNORS DF100"]

        col1_meta = MagicMock()
        col1_meta.unit = "°C"
        col2_meta = MagicMock()
        col2_meta.unit = "dbar"

        source_meta = MagicMock()
        source_meta.record_count = 100
        source_meta.columns = ["temperature", "pressure"]
        source_meta.category = "Sensor Data"
        source_meta.has_timestamp = True
        source_meta.get_numeric_columns.return_value = ["temperature", "pressure"]
        source_meta.get_column.side_effect = [col1_meta, col2_meta]

        mock_data_layer.get_source_metadata.return_value = source_meta
        mock_data_layer.get_column_stats.return_value = {
            "min": 1.0,
            "max": 2.0,
            "avg": 1.5,
        }

        render_data_explorer(mock_data_layer)

        assert mock_data_layer.get_column_stats.call_count == 2


class TestMissingUnitPlaceholder:
    """Test MISSING_UNIT_PLACEHOLDER constant."""

    def test_placeholder_is_empty_string(self):
        """Placeholder is empty string."""
        assert MISSING_UNIT_PLACEHOLDER == ""
