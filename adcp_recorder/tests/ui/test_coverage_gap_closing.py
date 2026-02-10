"""Targeted tests to close coverage gaps for 100% coverage."""

from unittest.mock import MagicMock, patch

import pytest

from adcp_recorder.ui.components.table_view import render_table_view
from adcp_recorder.ui.data_layer import ColumnMetadata, ColumnType, DataSource
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
