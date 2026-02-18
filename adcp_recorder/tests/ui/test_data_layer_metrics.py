"""Tests for data layer quality metrics and edge cases."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import duckdb
import pytest

from adcp_recorder.db.schema import ALL_SCHEMA_SQL
from adcp_recorder.ui.data_layer import (
    ColumnMetadata,
    ColumnType,
    DataLayer,
    DataSource,
)


@pytest.fixture
def real_conn():
    """Create a real in-memory DuckDB connection with schema."""
    conn = duckdb.connect(":memory:")
    for sql in ALL_SCHEMA_SQL:
        conn.execute(sql)
    return conn


@pytest.fixture
def data_layer(real_conn):
    return DataLayer(real_conn)


def test_get_quality_metrics_with_data(data_layer, real_conn):
    """Test quality metrics when data is present."""
    now = datetime.now()
    real_conn.execute(
        "INSERT INTO pnors_df100 (record_id, received_at, original_sentence, "
        "measurement_date, measurement_time) VALUES (1, ?, 'test', '010123', '120000')",
        [now],
    )
    real_conn.execute(
        "INSERT INTO parse_errors (error_id, received_at, raw_sentence, "
        "error_type, error_message) VALUES (1, ?, '$PNORI,...', 'CHECKSUM', 'bad')",
        [now],
    )

    metrics = data_layer.get_quality_metrics("24h")

    assert metrics["total_records"] >= 1
    assert metrics["error_count"] >= 1
    assert metrics["error_rate"] > 0
    assert "pnors_df100" in metrics["sources"]


def test_get_quality_metrics_no_sources():
    """Test quality metrics when no sources exist (mocked)."""
    mock_conn = MagicMock()
    layer = DataLayer(mock_conn)
    with (
        patch.object(layer, "get_available_sources", return_value=[]),
        patch.object(layer, "get_source_metadata", return_value=None),
    ):
        metrics = layer.get_quality_metrics("1h")
    assert metrics["total_records"] == 0
    assert metrics["error_rate"] == 0.0


def test_get_quality_metrics_error_table_skipped():
    """Test that sources with 'error' in name are skipped."""
    mock_conn = MagicMock()
    layer = DataLayer(mock_conn)

    error_source = DataSource(
        "parse_error_counts", "Parse Error Counts", [], 5, True, "received_at"
    )
    with (
        patch.object(layer, "get_available_sources", return_value=[error_source]),
        patch.object(layer, "get_source_metadata", return_value=None),
    ):
        metrics = layer.get_quality_metrics("24h")
    # Error tables should be skipped, so total_records = 0
    assert metrics["total_records"] == 0


def test_get_quality_metrics_count_exception():
    """Test quality metrics gracefully handles count exceptions."""
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = Exception("DB error")
    layer = DataLayer(mock_conn)

    source = DataSource("test_src", "Test", [], 0, True, "received_at")
    with (
        patch.object(layer, "get_available_sources", return_value=[source]),
        patch.object(layer, "get_source_metadata", return_value=None),
    ):
        metrics = layer.get_quality_metrics("24h")
    assert metrics["total_records"] == 0


def test_data_layer_sort_sources_df501(data_layer):
    """Test sort priority for df501 sources."""
    s1 = DataSource("df501_test", "DF501", [], 0, False, "")
    s2 = DataSource("unknown", "Unknown", [], 0, False, "")

    assert data_layer._sort_sources(s1)[0] == 3
    assert data_layer._sort_sources(s2)[0] == 99


def test_query_data_description_none():
    """Test query_data returns empty when description is None."""
    mock_conn = MagicMock()
    mock_conn.description = None
    layer = DataLayer(mock_conn)

    mock_source = DataSource("test", "Test", [], 1, False, "")
    with patch.object(layer, "get_source_metadata", return_value=mock_source):
        assert layer.query_data("test") == []


def test_query_directional_spectrum_energy_json_none():
    """Test directional spectrum returns empty when energy_densities JSON is None."""
    mock_conn = MagicMock()
    mock_conn.execute().fetchone.side_effect = [
        ("010126", "120000", datetime.now()),  # latest query
        (0.5, 0.1, 10, None, datetime.now()),  # energy_data with None densities
    ]
    layer = DataLayer(mock_conn)

    mock_source = DataSource(
        "pnore_data",
        "PNORE",
        [ColumnMetadata("received_at", ColumnType.TIMESTAMP, False)],
        1,
        True,
        "received_at",
    )
    with patch.object(layer, "get_source_metadata", side_effect=lambda name: mock_source):
        assert layer.query_directional_spectrum() == {}


def test_query_directional_spectrum_freq_none():
    """Test directional spectrum with None frequency values."""
    mock_conn = MagicMock()
    mock_conn.execute().fetchone.side_effect = [
        ("010126", "120000", datetime.now()),  # latest query
        (None, None, None, "[0.1]", datetime.now()),  # energy_data
        ("[180.0]",),  # md_data
        ("[10.0]",),  # ds_data
    ]
    layer = DataLayer(mock_conn)

    mock_source = DataSource(
        "pnore_data",
        "PNORE",
        [ColumnMetadata("received_at", ColumnType.TIMESTAMP, False)],
        1,
        True,
        "received_at",
    )

    def meta_side_effect(name):
        if name == "wave_measurement_full":
            return None
        return mock_source

    with patch.object(layer, "get_source_metadata", side_effect=meta_side_effect):
        result = layer.query_directional_spectrum()
    assert result["frequencies"] == []
