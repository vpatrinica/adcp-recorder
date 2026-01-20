"""Comprehensive coverage tests for DataLayer reaching 100%."""

import duckdb
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from adcp_recorder.ui.data_layer import DataLayer, ColumnType, ColumnMetadata, DataSource
from adcp_recorder.db.schema import ALL_SCHEMA_SQL


@pytest.fixture
def real_conn():
    conn = duckdb.connect(":memory:")
    for sql in ALL_SCHEMA_SQL:
        conn.execute(sql)
    return conn


@pytest.fixture
def data_layer(real_conn):
    return DataLayer(real_conn)


class TestDataLayerCompleteCoverage:
    """Tests designed to hit every remaining line in data_layer.py."""

    def test_datasource_helpers(self, data_layer):
        """Line 55, 59, 63."""
        meta = data_layer.get_source_metadata("pnors_df100")
        assert meta.get_column("nonexistent") is None
        assert "temperature" in meta.get_numeric_columns()
        assert "original_sentence" in meta.get_text_columns()

    def test_internal_table_filtering(self, data_layer, real_conn):
        """Line 167."""
        real_conn.execute("CREATE TABLE _internal_t (id INT)")
        sources = data_layer.get_available_sources()
        assert "_internal_t" not in [s.name for s in sources]

    def test_metadata_cache_hit(self, data_layer):
        """Line 193."""
        meta1 = data_layer.get_source_metadata("pnors_df100")
        meta2 = data_layer.get_source_metadata("pnors_df100")
        assert meta1 is meta2

    def test_query_data_missing_and_invalid(self, data_layer, real_conn):
        """Line 252, 257-261, 272-274, 281-282."""
        with pytest.raises(ValueError, match="Unknown data source"):
            data_layer.query_data("nonexistent")

        now = datetime.now()
        real_conn.execute(
            "INSERT INTO pnors_df100 (record_id, measurement_date, measurement_time, original_sentence, received_at) "
            "VALUES (1, '010123', '120000', 'test', ?)",
            [now],
        )
        # Invalid columns fallback
        data = data_layer.query_data("pnors_df100", columns=["missing"])
        assert "record_id" in data[0]

        # Filters and end_time
        data = data_layer.query_data(
            "pnors_df100", filters={"record_id": 1}, end_time=now + timedelta(seconds=1)
        )
        assert len(data) == 1

    def test_query_time_series_missing_and_invalid(self, data_layer):
        """Line 310, 323."""
        with pytest.raises(ValueError, match="Unknown data source"):
            data_layer.query_time_series("nonexistent", ["col"])

        res = data_layer.query_time_series("pnors_df100", ["missing"])
        assert res["x"] == []

    def test_query_velocity_profile_missing_and_timestamp(self, data_layer, real_conn):
        """Line 364, 379-380, 429."""
        with pytest.raises(ValueError, match="Unknown data source"):
            data_layer.query_velocity_profile("nonexistent")

        now = datetime(2023, 1, 1, 12, 0, 0)
        real_conn.execute(
            "INSERT INTO pnorc_df100 (record_id, measurement_date, measurement_time, cell_index, original_sentence) "
            "VALUES (1, '010123', '120000', 1, 'test')"
        )
        res = data_layer.query_velocity_profile("pnorc_df100", timestamp=now)
        assert len(res["depths"]) == 1

        # Multi-profile list branch
        res_list = data_layer.query_velocity_profiles("pnorc_df100", timestamps=[now])
        assert len(res_list) == 1

    def test_spectrum_and_energy_data(self, data_layer, real_conn):
        """Line 483-503, 563-582."""
        now = datetime.now()
        real_conn.execute(
            "INSERT INTO pnorf_data (record_id, received_at, sentence_type, original_sentence, "
            "coefficient_flag, measurement_date, measurement_time, spectrum_basis, num_frequencies, coefficients) "
            "VALUES (1, ?, 'PNORF', 'test', 'A1', '010123', '120000', 1, 1, '[0]')",
            [now],
        )
        res = data_layer.query_spectrum_data("pnorf_data")
        assert len(res) == 1

        real_conn.execute(
            "INSERT INTO pnore_data (record_id, received_at, sentence_type, original_sentence, "
            "measurement_date, measurement_time, spectrum_basis, start_frequency, step_frequency, num_frequencies, energy_densities) "
            "VALUES (2, ?, 'PNORE', 'test', '010123', '120000', 1, 0.5, 0.1, 1, '[1]')",
            [now],
        )
        res = data_layer.query_wave_energy("pnore_data")
        assert len(res) == 1

    def test_directional_spectrum_timestamp_fallback(self, data_layer, real_conn):
        """Line 617-620."""
        now = datetime.now()
        real_conn.execute(
            "INSERT INTO pnore_data (record_id, received_at, sentence_type, original_sentence, "
            "measurement_date, measurement_time, spectrum_basis, start_frequency, step_frequency, num_frequencies, energy_densities) "
            "VALUES (3, ?, 'PNORE', 'test', '010123', '120000', 1, 0.5, 0.1, 1, '[1]')",
            [now],
        )
        res = data_layer.query_directional_spectrum(timestamp=now)
        assert res["measurement_date"] == "010123"

    def test_column_stats_errors(self, data_layer):
        """Line 699, 703."""
        with pytest.raises(ValueError, match="Unknown data source"):
            data_layer.get_column_stats("nonexistent", "col")

        res = data_layer.get_column_stats("pnors_df100", "original_sentence")
        assert res == {}

    def test_aggregate_time_series_errors(self, data_layer, real_conn):
        """Line 750."""
        real_conn.execute("CREATE TABLE no_ts_table (id INT)")
        res = data_layer.aggregate_time_series("no_ts_table", "id")
        assert res["x"] == []

    @patch("duckdb.DuckDBPyConnection.execute")
    def test_mocked_error_paths(self, mock_execute, data_layer):
        """Precisely hit lines 186, 224, 635, 653, 723."""
        # 186: View exception
        mock_execute.side_effect = [
            MagicMock(fetchall=lambda: [("table1",)]),  # tables
            Exception("Views missing"),  # views
        ]
        with patch.object(data_layer, "get_source_metadata", return_value=DataSource("t", "T", [])):
            sources = data_layer.get_available_sources()
            assert len(sources) == 1

        # 224: Count exception
        mock_execute.side_effect = [
            MagicMock(fetchall=lambda: [("c", "INT", "YES", None, None, None)]),  # DESCRIBE
            Exception("Count fail"),  # COUNT
        ]
        data_layer._source_cache = {}  # Clear cache
        meta = data_layer.get_source_metadata("t")
        assert meta.record_count == 0

        # 635: No latest measurement in directional spectrum
        mock_execute.side_effect = [MagicMock(fetchone=lambda: None)]
        assert data_layer.query_directional_spectrum() == {}

        # 653: Second fetch fail in directional spectrum
        mock_execute.side_effect = [
            MagicMock(fetchone=lambda: ("010123", "120000", datetime.now())),  # latest
            MagicMock(fetchone=lambda: None),  # energy_data fail
        ]
        assert data_layer.query_directional_spectrum() == {}

        # 723: Stats query returns None
        mock_execute.side_effect = [MagicMock(fetchone=lambda: None)]
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource("t", "T", [ColumnMetadata("c", ColumnType.NUMERIC)])
            assert data_layer.get_column_stats("t", "c") == {}

    def test_query_velocity_profile_empty(self, real_conn):
        """Line 376."""
        # Use a fresh connection with no data
        conn = duckdb.connect(":memory:")
        for sql in ALL_SCHEMA_SQL:
            conn.execute(sql)
        dl = DataLayer(conn)
        res = dl.query_velocity_profile("pnorc_df100")
        assert res == {"depths": [], "velocities": {}}

    def test_query_velocity_profiles_none(self, data_layer):
        """Line 423."""
        # timestamps=None hits line 423
        res = data_layer.query_velocity_profiles("pnorc_df100", timestamps=None)
        assert len(res) == 1

    def test_get_available_bursts_with_end_time(self, data_layer, real_conn):
        """Line 538-539."""
        now = datetime.now()
        real_conn.execute(
            "INSERT INTO pnore_data (record_id, received_at, sentence_type, original_sentence, "
            "measurement_date, measurement_time, spectrum_basis, num_frequencies, energy_densities) "
            "VALUES (10, ?, 'PNORE', 'test', '010123', '120000', 1, 1, '[0]')",
            [now],
        )
        # We must provide start_time to ensure conditions has items and we reach 538
        res = data_layer.get_available_bursts(
            start_time=now - timedelta(days=1), end_time=now + timedelta(days=1)
        )
        assert len(res) >= 1

    def test_directional_spectrum_fallback(self, data_layer, real_conn):
        """Line 614-615."""
        # Data exists with date/time, but received_at is slightly different
        now = datetime(2023, 1, 1, 12, 0, 0)
        real_conn.execute(
            "INSERT INTO pnore_data (record_id, received_at, sentence_type, original_sentence, "
            "measurement_date, measurement_time, spectrum_basis, start_frequency, step_frequency, num_frequencies, energy_densities) "
            "VALUES (11, ?, 'PNORE', 'test', '010123', '120000', 1, 0.5, 0.1, 1, '[1]')",
            [now + timedelta(milliseconds=1)],  # Different received_at
        )
        # Querying with 'now' will fail at 610, hitting fallback at 614
        res = data_layer.query_directional_spectrum(timestamp=now)
        assert res["measurement_date"] == "010123"

    def test_parse_time_range_and_agg_fallback(self, data_layer, real_conn):
        """Line 737, 757."""
        assert data_layer._parse_time_range("nonexistent-range") is None

        # Aggregation fallback
        now = datetime.now()
        real_conn.execute(
            "INSERT INTO pnors_df100 (record_id, measurement_date, measurement_time, original_sentence, received_at, temperature) "
            "VALUES (20, '010123', '120000', 'test', ?, 25.0)",
            [now],
        )
        res = data_layer.aggregate_time_series("pnors_df100", "temperature", aggregation="UNKNOWN")
        assert len(res["y"]) == 1
