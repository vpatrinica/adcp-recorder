"""Targeted tests to close coverage gaps for 100% coverage."""

from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest

from adcp_recorder.ui.components.table_view import render_table_view
from adcp_recorder.ui.data_layer import (
    ColumnMetadata,
    ColumnType,
    DataLayer,
    DataSource,
)
from adcp_recorder.ui.parquet_data_layer import ParquetDataLayer

# ============================================================================
# table_view.py Gaps
# ============================================================================


@pytest.fixture
def mock_st_module():
    """Mock streamlit module."""
    # Patch the module where render_table_view is defined
    with patch("adcp_recorder.ui.components.table_view.st") as mock:
        # Mock columns to return a list of mocks when called
        mock.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]
        yield mock


@pytest.fixture
def mock_data_layer():
    """Mock DataLayer."""
    return MagicMock()


def test_table_view_complex_timestamp_selection(mock_st_module, mock_data_layer):
    """Cover multiple timestamp columns selection logic."""
    print(f"DEBUG: mock_st type: {type(mock_st_module)}")
    print(f"DEBUG: selectbox type: {type(mock_st_module.selectbox)}")

    source = DataSource(
        "test_src",
        "Test",
        [
            ColumnMetadata("received_at", ColumnType.TIMESTAMP, False),
            ColumnMetadata("measurement_datetime", ColumnType.TIMESTAMP, False),
            ColumnMetadata("other", ColumnType.TIMESTAMP, False),
        ],
        10,
        True,
        "other",
    )
    mock_data_layer.get_source_metadata.return_value = source
    mock_data_layer.query_data.return_value = []

    # Mock selectbox to choose 'received_at'
    mock_st_module.selectbox.return_value = "received_at"

    render_table_view(mock_data_layer, "test_src")

    print(f"DEBUG: selectbox call count: {mock_st_module.selectbox.call_count}")
    print(f"DEBUG: calls: {mock_st_module.selectbox.call_args_list}")

    assert mock_st_module.selectbox.call_count >= 1


def test_pdl_load_source_timestamp_fallback():
    """Cover fallback to received_at (Line 1023)."""
    mock_conn = MagicMock()
    with patch("adcp_recorder.ui.parquet_data_layer.duckdb.connect") as mock_connect:
        mock_connect.return_value = mock_conn
        pdl = ParquetDataLayer(None)

        pdl._loaded_views.add("pq_test")

        mock_conn.execute.return_value.fetchall.return_value = [
            ("received_at", "VARCHAR", "YES", None, None, None),
            ("other_col", "INTEGER", "YES", None, None, None),
        ]
        mock_conn.execute.return_value.fetchone.return_value = (10,)

        source = pdl.get_source_metadata("pq_test")
        assert source is not None
    assert source.timestamp_column == "received_at"


def test_get_quality_metrics_parse_errors_exception():
    """Exercise the except: pass branch when counting parse_errors fails."""
    # Create DataLayer with mock connection
    mock_conn = MagicMock()
    dl: Any = DataLayer(mock_conn)

    # Patch get_available_sources to return a single source
    src = DataSource(
        name="test_src",
        display_name="Test",
        columns=[ColumnMetadata("received_at", ColumnType.TIMESTAMP)],
        record_count=5,
        has_timestamp=False,
        category="test",
    )
    dl.get_available_sources = MagicMock(return_value=[src])

    # Ensure get_source_metadata('parse_errors') returns a truthy value so code attempts to count
    dl.get_source_metadata = MagicMock(side_effect=lambda n: src if n == "parse_errors" else src)

    # Define execute behavior: raise on parse_errors count, otherwise return count 5
    def exec_side(sql, params=None):
        sql_str = sql if isinstance(sql, str) else str(sql)
        m = MagicMock()
        if "FROM parse_errors" in sql_str:
            raise Exception("DB failure on parse_errors")
        m.fetchone.return_value = (5,)
        m.fetchall.return_value = []
        return m

    mock_conn.execute.side_effect = exec_side

    metrics = dl.get_quality_metrics()
    # Should not raise and should contain total_records from the single source
    assert metrics["total_records"] >= 0
    # Since parse_errors counting raised, error_count should not be present
    assert "error_count" not in metrics


def test_table_view_timestamp_selection_and_default_range_none(mock_st_module, mock_data_layer):
    """Cover case where available timestamp columns list is empty and default_time_range is invalid.

    This triggers the branch that sets selected_ts_col to source.timestamp_column
    and the exception handler that falls back default_idx = 2 when default_time_range
    doesn't support .lower().
    """
    from adcp_recorder.ui.components.table_view import render_table_view
    from adcp_recorder.ui.data_layer import ColumnMetadata, ColumnType, DataSource

    # Create a source with a timestamp column that is neither received_at nor measurement_datetime
    src = DataSource(
        name="ts_src",
        display_name="TS Source",
        columns=[
            ColumnMetadata("other_ts", ColumnType.TIMESTAMP),
            ColumnMetadata("vel1", ColumnType.NUMERIC),
        ],
        record_count=10,
        has_timestamp=True,
        timestamp_column="other_ts",
        category="test",
    )

    mock_data_layer.get_source_metadata.return_value = src
    mock_data_layer.query_data.return_value = []

    # Call render_table_view with default_time_range set to None to raise AttributeError in .lower()
    render_table_view(mock_data_layer, "ts_src", default_time_range=cast(str, None))

    # Verify query_data was called with timestamp_col set to the source timestamp column
    called = False
    for call in mock_data_layer.query_data.call_args_list:
        kwargs = call.kwargs
        if kwargs.get("timestamp_col") == "other_ts":
            called = True
            break
    assert called
