"""Unit tests for dashboard data layer."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from adcp_recorder.ui.data_layer import (
    COLUMN_UNITS,
    SOURCE_CATEGORIES,
    ColumnMetadata,
    ColumnType,
    DataLayer,
    DataSource,
    _format_display_name,
    _infer_column_type,
)


class TestColumnType:
    """Tests for column type inference."""

    def test_infer_numeric_types(self):
        """Test numeric type detection."""
        assert _infer_column_type("INTEGER") == ColumnType.NUMERIC
        assert _infer_column_type("BIGINT") == ColumnType.NUMERIC
        assert _infer_column_type("DECIMAL(5,2)") == ColumnType.NUMERIC
        assert _infer_column_type("DOUBLE") == ColumnType.NUMERIC
        assert _infer_column_type("FLOAT") == ColumnType.NUMERIC
        assert _infer_column_type("SMALLINT") == ColumnType.NUMERIC

    def test_infer_timestamp_types(self):
        """Test timestamp type detection."""
        assert _infer_column_type("TIMESTAMP") == ColumnType.TIMESTAMP
        assert _infer_column_type("DATE") == ColumnType.TIMESTAMP
        assert _infer_column_type("TIMESTAMP WITH TIME ZONE") == ColumnType.TIMESTAMP

    def test_infer_boolean_types(self):
        """Test boolean type detection."""
        assert _infer_column_type("BOOLEAN") == ColumnType.BOOLEAN
        assert _infer_column_type("BOOL") == ColumnType.BOOLEAN

    def test_infer_json_types(self):
        """Test JSON type detection."""
        assert _infer_column_type("JSON") == ColumnType.JSON

    def test_infer_text_types(self):
        """Test text type detection (fallback)."""
        assert _infer_column_type("VARCHAR") == ColumnType.TEXT
        assert _infer_column_type("TEXT") == ColumnType.TEXT
        assert _infer_column_type("CHAR(10)") == ColumnType.TEXT


class TestFormatDisplayName:
    """Tests for display name formatting."""

    def test_basic_formatting(self):
        """Test basic table name formatting."""
        assert _format_display_name("pnors_df100") == "Pnors Df100"
        assert _format_display_name("raw_lines") == "Raw Lines"
        assert (
            _format_display_name("echo_data") == "Echo Data"
        )  # Old name fallback or explicit check
        assert _format_display_name("pnore_data") == "Pnore Data"

    def test_small_words_uppercase(self):
        """Test capitalization behavior."""
        # The function uses title() which capitalizes first letter only
        assert _format_display_name("pnori2") == "Pnori2"


class TestColumnMetadata:
    """Tests for column metadata."""

    def test_column_with_unit(self):
        """Test column metadata with unit."""
        col = ColumnMetadata(
            name="temperature",
            column_type=ColumnType.NUMERIC,
            unit="°C",
        )
        assert col.name == "temperature"
        assert col.unit == "°C"

    def test_known_column_units(self):
        """Test known column units are defined."""
        assert COLUMN_UNITS["temperature"] == "°C"
        assert COLUMN_UNITS["pressure"] == "dbar"
        assert COLUMN_UNITS["heading"] == "°"
        assert COLUMN_UNITS["vel1"] == "m/s"


class TestDataSource:
    """Tests for DataSource class."""

    def test_get_column(self):
        """Test getting column by name."""
        cols = [
            ColumnMetadata("temp", ColumnType.NUMERIC),
            ColumnMetadata("name", ColumnType.TEXT),
        ]
        source = DataSource("test", "Test", cols)

        assert source.get_column("temp") is not None
        assert source.get_column("temp").column_type == ColumnType.NUMERIC
        assert source.get_column("nonexistent") is None

    def test_get_numeric_columns(self):
        """Test getting numeric column names."""
        cols = [
            ColumnMetadata("temp", ColumnType.NUMERIC),
            ColumnMetadata("name", ColumnType.TEXT),
            ColumnMetadata("pressure", ColumnType.NUMERIC),
        ]
        source = DataSource("test", "Test", cols)

        numeric = source.get_numeric_columns()
        assert len(numeric) == 2
        assert "temp" in numeric
        assert "pressure" in numeric
        assert "name" not in numeric

    def test_get_text_columns(self):
        """Test getting text column names."""
        cols = [
            ColumnMetadata("temp", ColumnType.NUMERIC),
            ColumnMetadata("name", ColumnType.TEXT),
            ColumnMetadata("label", ColumnType.TEXT),
        ]
        source = DataSource("test", "Test", cols)

        text = source.get_text_columns()
        assert len(text) == 2
        assert "name" in text


class TestSourceCategories:
    """Tests for source categorization."""

    def test_category_mapping(self):
        """Test source category mapping."""
        assert SOURCE_CATEGORIES["pnors_df100"] == "Sensor Data"
        assert SOURCE_CATEGORIES["pnorc12"] == "Velocity Data"
        assert SOURCE_CATEGORIES["pnore_data"] == "Wave Data"
        assert SOURCE_CATEGORIES["parse_errors"] == "Errors"


class TestDataLayer:
    """Tests for DataLayer class."""

    @pytest.fixture
    def mock_conn(self):
        """Create a mock DuckDB connection."""
        return MagicMock()

    @pytest.fixture
    def data_layer(self, mock_conn):
        """Create DataLayer with mock connection."""
        return DataLayer(mock_conn)

    def test_parse_time_range(self, data_layer):
        """Test time range parsing."""
        now = datetime.now()

        result = data_layer._parse_time_range("1h")
        assert result is not None
        assert (now - result) < timedelta(hours=1, seconds=5)

        result = data_layer._parse_time_range("24h")
        assert result is not None
        assert (now - result) < timedelta(hours=24, seconds=5)

        result = data_layer._parse_time_range("7d")
        assert result is not None
        assert (now - result) < timedelta(days=7, seconds=5)

        result = data_layer._parse_time_range("custom")
        assert result is None

    def test_get_source_metadata_caching(self, data_layer, mock_conn):
        """Test that source metadata is cached."""
        # Setup mock
        mock_conn.execute.return_value.fetchall.return_value = [
            ("col1", "INTEGER", "YES", None, None, None),
        ]

        # First call
        data_layer.get_source_metadata("test_table")

        # Second call - should use cache
        data_layer.get_source_metadata("test_table")

        # Execute should only be called for first fetch
        # (1 for DESCRIBE, 1 for COUNT)
        assert mock_conn.execute.call_count == 2

    def test_query_data_with_filters(self, data_layer, mock_conn):
        """Test query data with time filters."""
        # Setup mock
        mock_conn.execute.return_value.fetchall.return_value = [
            ("col1", "INTEGER", "YES", None, None, None),
            ("received_at", "TIMESTAMP", "YES", None, None, None),
        ]
        mock_conn.execute.return_value.fetchone.return_value = (100,)
        mock_conn.description = [("col1",), ("received_at",)]

        # Precache the source
        data_layer.get_source_metadata("test_table")

        # Query with time filter
        start = datetime.now() - timedelta(hours=1)
        data_layer.query_data(
            "test_table",
            columns=["col1"],
            start_time=start,
            limit=50,
        )

        # Verify query was executed
        assert mock_conn.execute.called
