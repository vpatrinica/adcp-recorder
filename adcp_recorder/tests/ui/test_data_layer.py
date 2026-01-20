"""Unit tests for dashboard data layer."""

from datetime import datetime, timedelta

import duckdb
import pytest

from adcp_recorder.db.schema import ALL_SCHEMA_SQL
from adcp_recorder.ui.data_layer import (
    ColumnType,
    DataLayer,
    _format_display_name,
    _infer_column_type,
)


class TestColumnType:
    """Tests for column type inference."""

    def test_infer_numeric_types(self):
        """Test numeric type detection."""
        assert _infer_column_type("INTEGER") == ColumnType.NUMERIC
        assert _infer_column_type("DECIMAL(5,2)") == ColumnType.NUMERIC
        assert _infer_column_type("FLOAT") == ColumnType.NUMERIC

    def test_infer_timestamp_types(self):
        """Test timestamp type detection."""
        assert _infer_column_type("TIMESTAMP") == ColumnType.TIMESTAMP
        assert _infer_column_type("DATE") == ColumnType.TIMESTAMP

    def test_infer_boolean_types(self):
        """Test boolean type detection."""
        assert _infer_column_type("BOOLEAN") == ColumnType.BOOLEAN

    def test_infer_json_types(self):
        """Test JSON type detection."""
        assert _infer_column_type("JSON") == ColumnType.JSON

    def test_infer_text_types(self):
        """Test text type detection (fallback)."""
        assert _infer_column_type("VARCHAR") == ColumnType.TEXT


class TestFormatDisplayName:
    """Tests for display name formatting."""

    def test_basic_formatting(self):
        """Test basic table name formatting."""
        assert _format_display_name("pnors_df100") == "Pnors Df100"
        assert _format_display_name("raw_lines") == "Raw Lines"

    def test_small_words_uppercase(self):
        """Test capitalization behavior."""
        assert _format_display_name("pnori2") == "Pnori2"


@pytest.fixture
def real_conn():
    """Create a real in-memory DuckDB connection with schema."""
    conn = duckdb.connect(":memory:")
    for sql in ALL_SCHEMA_SQL:
        conn.execute(sql)
    return conn


class TestDataLayerReal:
    """Tests for DataLayer class using real DuckDB."""

    @pytest.fixture
    def data_layer(self, real_conn):
        return DataLayer(real_conn)

    def test_get_available_sources(self, data_layer):
        """Test listing available sources."""
        sources = data_layer.get_available_sources(include_views=True)
        source_names = [s.name for s in sources]
        assert "pnori" in source_names
        assert "pnors12" in source_names
        # Should also have views
        assert "wave_measurement" in source_names

    def test_get_source_metadata_not_found(self, data_layer):
        """Test getting metadata for non-existent table."""
        assert data_layer.get_source_metadata("nonexistent") is None

    def test_query_data_filter_time(self, data_layer, real_conn):
        """Test query data with time filters."""
        now = datetime.now()
        real_conn.execute(
            "INSERT INTO pnors_df100 (record_id, received_at, original_sentence, "
            "measurement_date, measurement_time) VALUES (1, ?, 'test', '010123', '120000')",
            [now],
        )
        real_conn.execute(
            "INSERT INTO pnors_df100 (record_id, received_at, original_sentence, "
            "measurement_date, measurement_time) VALUES (2, ?, 'test', '010123', '130000')",
            [now - timedelta(hours=2)],
        )

        data = data_layer.query_data("pnors_df100", start_time=now - timedelta(hours=1))
        assert len(data) == 1
        assert data[0]["record_id"] == 1

    def test_query_time_series(self, data_layer, real_conn):
        """Test time series query."""
        now = datetime.now()
        for i in range(5):
            real_conn.execute(
                "INSERT INTO pnors_df100 (record_id, received_at, original_sentence, "
                "measurement_date, measurement_time, temperature) VALUES (?, ?, 'test', "
                "'010123', '120000', ?)",
                [i, now - timedelta(minutes=i), float(i)],
            )

        ts_data = data_layer.query_time_series("pnors_df100", ["temperature"], time_range="1h")
        assert len(ts_data["x"]) == 5
        assert len(ts_data["series"]["temperature"]) == 5

    def test_query_velocity_profile(self, data_layer, real_conn):
        """Test velocity profile query."""
        real_conn.execute(
            "INSERT INTO pnorc_df100 (record_id, original_sentence, measurement_date, "
            "measurement_time, cell_index, vel1) VALUES (1, 'test', '010123', '120000', 1, 1.0)"
        )
        real_conn.execute(
            "INSERT INTO pnorc_df100 (record_id, original_sentence, measurement_date, "
            "measurement_time, cell_index, vel1) VALUES (2, 'test', '010123', '120000', 2, 1.1)"
        )

        profile = data_layer.query_velocity_profile(
            "pnorc_df100", cell_size=2.0, blanking_distance=0.5
        )
        assert len(profile["depths"]) == 2
        assert profile["depths"] == [2.5, 4.5]
        # Decimal comparison
        assert [float(v) for v in profile["velocities"]["vel1"]] == [1.0, 1.1]

    def test_query_amplitude_heatmap(self, data_layer, real_conn):
        """Test amplitude heatmap query."""
        now = datetime.now()
        real_conn.execute(
            "INSERT INTO pnorc12 (record_id, received_at, data_format, original_sentence, "
            "measurement_date, measurement_time, cell_index, amp1, amp2, amp3, amp4) "
            "VALUES (1, ?, 101, 'test', '010123', '120000', 1, 10, 20, 30, 40)",
            [now],
        )

        heatmap = data_layer.query_amplitude_heatmap("pnorc12")
        assert len(heatmap) == 1
        assert heatmap[0]["amplitudes"] == [25.0]

    def test_query_directional_spectrum(self, data_layer, real_conn):
        """Test directional spectrum query."""
        now = datetime.now()
        date_str = now.strftime("%d%m%y")
        time_str = now.strftime("%H%M%S")

        real_conn.execute(
            "INSERT INTO pnore_data (record_id, received_at, sentence_type, original_sentence, "
            "measurement_date, measurement_time, spectrum_basis, start_frequency, "
            "step_frequency, num_frequencies, energy_densities) VALUES (1, ?, 'PNORE', "
            "'test', ?, ?, 1, 0.5, 0.1, 2, '[1.0, 2.0]')",
            [now, date_str, time_str],
        )
        real_conn.execute(
            "INSERT INTO pnorwd_data (record_id, received_at, sentence_type, original_sentence, "
            "measurement_date, measurement_time, spectrum_basis, start_frequency, "
            "step_frequency, num_frequencies, direction_type, values) VALUES (1, ?, 'PNORWD', "
            "'test', ?, ?, 1, 0.5, 0.1, 2, 'MD', '[180.0, 190.0]')",
            [now, date_str, time_str],
        )
        real_conn.execute(
            "INSERT INTO pnorwd_data (record_id, received_at, sentence_type, original_sentence, "
            "measurement_date, measurement_time, spectrum_basis, start_frequency, "
            "step_frequency, num_frequencies, direction_type, values) VALUES (2, ?, 'PNORWD', "
            "'test', ?, ?, 1, 0.5, 0.1, 2, 'DS', '[10.0, 15.0]')",
            [now, date_str, time_str],
        )

        spec = data_layer.query_directional_spectrum()
        assert spec["energy"] == [1.0, 2.0]
        assert spec["directions"] == [180.0, 190.0]
        assert spec["spreads"] == [10.0, 15.0]

    def test_get_column_stats(self, data_layer, real_conn):
        """Test column stats query."""
        for i in range(1, 11):
            real_conn.execute(
                "INSERT INTO pnors_df100 (record_id, original_sentence, measurement_date, "
                "measurement_time, temperature) VALUES (?, 'test', '010123', '120000', ?)",
                [i, float(i)],
            )

        stats = data_layer.get_column_stats("pnors_df100", "temperature")
        assert stats["min"] == 1.0
        assert stats["max"] == 10.0
        assert float(stats["avg"]) == 5.5
        assert stats["count"] == 10

    def test_aggregate_time_series(self, data_layer, real_conn):
        """Test time series aggregation."""
        now = datetime.now()
        for i in range(10):
            real_conn.execute(
                "INSERT INTO pnors_df100 (record_id, received_at, original_sentence, "
                "measurement_date, measurement_time, temperature) VALUES (?, ?, 'test', "
                "'010123', '120000', 10.0)",
                [i, now - timedelta(minutes=i)],
            )

        agg = data_layer.aggregate_time_series("pnors_df100", "temperature", bucket_minutes=5)
        assert len(agg["x"]) >= 2
        assert all(float(y) == 10.0 for y in agg["y"])

    def test_get_available_bursts(self, data_layer, real_conn):
        """Test get_available_bursts."""
        now = datetime.now()
        real_conn.execute(
            "INSERT INTO pnore_data (record_id, received_at, sentence_type, original_sentence, "
            "measurement_date, measurement_time, spectrum_basis, num_frequencies, "
            "energy_densities) VALUES (1, ?, 'PNORE', 'test', '010123', '120000', 1, 1, '[0]')",
            [now],
        )

        bursts = data_layer.get_available_bursts(time_range="24h")
        assert len(bursts) == 1
        assert bursts[0]["measurement_date"] == "010123"
        assert bursts[0]["measurement_time"] == "120000"
