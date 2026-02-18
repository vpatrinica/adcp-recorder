"""Comprehensive coverage tests for DataLayer reaching 100%."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import duckdb
import pytest

from adcp_recorder.db.schema import ALL_SCHEMA_SQL
from adcp_recorder.ui.data_layer import ColumnMetadata, ColumnType, DataLayer, DataSource


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
        # Line 252 failure fallback
        assert data_layer.query_data("nonexistent") == []

        now = datetime.now()
        real_conn.execute(
            "INSERT INTO pnors_df100 (record_id, measurement_date, measurement_time, "
            "original_sentence, received_at) "
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
        # Line 310 failure fallback
        assert data_layer.query_time_series("nonexistent", ["col"]) == {
            "x": [],
            "series": {"col": []},
        }

        res = data_layer.query_time_series("pnors_df100", ["missing"])
        assert res["x"] == []

    def test_query_velocity_profile_missing_and_timestamp(self, data_layer, real_conn):
        """Line 364, 379-380, 429."""
        # Line 364 failure fallback
        assert data_layer.query_velocity_profile("nonexistent") == {"depths": [], "velocities": {}}

        now = datetime(2023, 1, 1, 12, 0, 0)
        real_conn.execute(
            "INSERT INTO pnorc_df100 (record_id, measurement_date, measurement_time, "
            "cell_index, original_sentence) "
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
            "coefficient_flag, measurement_date, measurement_time, spectrum_basis, "
            "num_frequencies, coefficients) "
            "VALUES (1, ?, 'PNORF', 'test', 'A1', '010123', '120000', 1, 1, '[0]')",
            [now],
        )
        res = data_layer.query_spectrum_data("pnorf_data")
        assert len(res) == 1

        real_conn.execute(
            "INSERT INTO pnore_data (record_id, received_at, sentence_type, original_sentence, "
            "measurement_date, measurement_time, spectrum_basis, start_frequency, "
            "step_frequency, num_frequencies, energy_densities) "
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
            "measurement_date, measurement_time, spectrum_basis, start_frequency, "
            "step_frequency, num_frequencies, energy_densities) "
            "VALUES (3, ?, 'PNORE', 'test', '010123', '120000', 1, 0.5, 0.1, 1, '[1]')",
            [now],
        )
        res = data_layer.query_directional_spectrum(timestamp=now)
        assert res["measurement_date"] == "010123"

    def test_column_stats_errors(self, data_layer):
        """Line 699, 703."""
        # Line 699 failure fallback
        assert data_layer.get_column_stats("nonexistent", "col") == {}

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
        # Function returns initialized velocity columns even when empty
        assert res == {"depths": [], "velocities": {"vel1": [], "vel2": [], "vel3": [], "vel4": []}}

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
            "measurement_date, measurement_time, spectrum_basis, num_frequencies, "
            "energy_densities) "
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
            "measurement_date, measurement_time, spectrum_basis, start_frequency, "
            "step_frequency, num_frequencies, energy_densities) "
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
            "INSERT INTO pnors_df100 (record_id, measurement_date, measurement_time, "
            "original_sentence, received_at, temperature) "
            "VALUES (20, '010123', '120000', 'test', ?, 25.0)",
            [now],
        )
        res = data_layer.aggregate_time_series("pnors_df100", "temperature", aggregation="UNKNOWN")
        assert len(res["y"]) == 1


class TestDataLayerCoverageFinalConsistently:
    """Extra tests to achieve 100% coverage."""

    @patch("duckdb.DuckDBPyConnection.execute")
    def test_execute_sql_exception(self, mock_execute, data_layer):
        """Line 292-293: execute_sql exception."""
        mock_execute.side_effect = Exception("SQL Error")
        assert data_layer.execute_sql("SELECT *") == []

    @patch("duckdb.DuckDBPyConnection.execute")
    def test_query_time_series_exception(self, mock_execute, data_layer):
        """Line 406-407: query_time_series execution exception."""
        source_name = "test_source"
        cols = [
            ColumnMetadata("ts", ColumnType.TIMESTAMP),
            ColumnMetadata("col1", ColumnType.NUMERIC),
            ColumnMetadata("col2", ColumnType.NUMERIC),
        ]
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource(source_name, "Test", cols, timestamp_column="ts")
            mock_execute.side_effect = Exception("Query Error")
            res = data_layer.query_time_series(source_name, ["col1", "col2"])
            assert res == {"x": [], "series": {"col1": [], "col2": []}}

    @patch("duckdb.DuckDBPyConnection.execute")
    def test_query_spectrum_data_exception(self, mock_execute, data_layer):
        """Line 572-573: query_spectrum_data exception."""
        source_name = "test_source"
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource(source_name, "Test", [])
            mock_execute.side_effect = Exception("Spectrum Error")
            assert data_layer.query_spectrum_data(source_name) == []

    @patch("duckdb.DuckDBPyConnection.execute")
    def test_get_available_bursts_exception(self, mock_execute, data_layer):
        """Line 633-634: get_available_bursts exception."""
        source_name = "test_source"
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource(source_name, "Test", [])
            mock_execute.side_effect = Exception("Burst Error")
            assert data_layer.get_available_bursts(source_name=source_name) == []

    @patch("duckdb.DuckDBPyConnection.execute")
    def test_query_wave_energy_exception(self, mock_execute, data_layer):
        """Line 667-668: query_wave_energy exception."""
        source_name = "test_source"
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource(source_name, "Test", [])
            mock_execute.side_effect = Exception("Energy Error")
            assert data_layer.query_wave_energy(source_name) == []

    @patch("duckdb.DuckDBPyConnection.execute")
    def test_query_velocity_profile_latest_success(self, mock_execute, data_layer):
        """Line 436: successful latest measurement lookup."""
        source_name = "test_source"
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource(source_name, "Test", [])
            mock_execute.return_value.fetchone.side_effect = [
                ("010126", "120000"),  # latest
                [],  # cells query result
            ]
            res = data_layer.query_velocity_profile(source_name)
            assert res == {
                "depths": [],
                "velocities": {"vel1": [], "vel2": [], "vel3": [], "vel4": []},
            }


class TestQueryWaveRoseData:
    """Tests for DataLayer.query_wave_rose_data (lines 931-959)."""

    @pytest.fixture
    def real_conn(self):
        conn = duckdb.connect(":memory:")
        for sql in ALL_SCHEMA_SQL:
            conn.execute(sql)
        return conn

    @pytest.fixture
    def data_layer(self, real_conn):
        return DataLayer(real_conn)

    def test_query_wave_rose_basic(self, data_layer, real_conn):
        """Test basic wave rose query returns data from pnorw_data."""
        now = datetime.now()
        real_conn.execute(
            "INSERT INTO pnorw_data (record_id, received_at, sentence_type, original_sentence, "
            "measurement_date, measurement_time, hm0, dir_tp, tp, main_dir) "
            "VALUES (1, ?, 'PNORW', 'test', '010126', '120000', 1.5, 90.0, 8.0, 85.0)",
            [now],
        )
        result = data_layer.query_wave_rose_data("pnorw_data", time_range="24h")
        assert len(result) == 1
        assert result[0]["hm0"] == 1.5
        assert result[0]["dir_tp"] == 90.0
        assert result[0]["tp"] == 8.0
        assert result[0]["main_dir"] == 85.0

    def test_query_wave_rose_filters_nulls(self, data_layer, real_conn):
        """Test wave rose query filters out rows with NULL hm0 or dir_tp."""
        now = datetime.now()
        real_conn.execute(
            "INSERT INTO pnorw_data (record_id, received_at, sentence_type, original_sentence, "
            "measurement_date, measurement_time, hm0, dir_tp) "
            "VALUES (1, ?, 'PNORW', 'test', '010126', '120000', NULL, 90.0)",
            [now],
        )
        real_conn.execute(
            "INSERT INTO pnorw_data (record_id, received_at, sentence_type, original_sentence, "
            "measurement_date, measurement_time, hm0, dir_tp) "
            "VALUES (2, ?, 'PNORW', 'test', '010126', '130000', 1.5, NULL)",
            [now],
        )
        result = data_layer.query_wave_rose_data("pnorw_data", time_range="24h")
        assert len(result) == 0

    def test_query_wave_rose_nonexistent_source(self, data_layer):
        """Test wave rose query with nonexistent source returns empty."""
        result = data_layer.query_wave_rose_data("nonexistent_table")
        assert result == []

    def test_query_wave_rose_from_pnorb(self, data_layer, real_conn):
        """Test wave rose query from pnorb_data (frequency bands)."""
        now = datetime.now()
        real_conn.execute(
            "INSERT INTO pnorb_data (record_id, received_at, sentence_type, original_sentence, "
            "measurement_date, measurement_time, spectrum_basis, processing_method, "
            "hm0, dir_tp, tp, main_dir) "
            "VALUES (1, ?, 'PNORB', 'test', '010126', '120000', 1, 1, 0.5, 45.0, 4.0, 40.0)",
            [now],
        )
        result = data_layer.query_wave_rose_data("pnorb_data", time_range="24h")
        assert len(result) == 1
        assert result[0]["hm0"] == 0.5
        assert result[0]["dir_tp"] == 45.0

    def test_query_wave_rose_with_time_range_all(self, data_layer, real_conn):
        """Test wave rose with 'all' time range (no time filter)."""
        now = datetime.now()
        real_conn.execute(
            "INSERT INTO pnorw_data (record_id, received_at, sentence_type, original_sentence, "
            "measurement_date, measurement_time, hm0, dir_tp, tp) "
            "VALUES (1, ?, 'PNORW', 'test', '010126', '120000', 2.0, 180.0, 12.0)",
            [now - timedelta(days=365)],
        )
        result = data_layer.query_wave_rose_data("pnorw_data", time_range="all")
        assert len(result) == 1

    @patch("duckdb.DuckDBPyConnection.execute")
    def test_query_wave_rose_exception(self, mock_execute, data_layer):
        """Test wave rose query exception returns empty list."""
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource(
                "pnorw_data", "Wave", [ColumnMetadata("received_at", ColumnType.TIMESTAMP)]
            )
            mock_execute.side_effect = Exception("DB Error")
            result = data_layer.query_wave_rose_data("pnorw_data")
            assert result == []


class TestQueryCurrentSpeedHeatmap:
    """Tests for DataLayer.query_current_speed_heatmap (lines 979-1089)."""

    @pytest.fixture
    def real_conn(self):
        conn = duckdb.connect(":memory:")
        for sql in ALL_SCHEMA_SQL:
            conn.execute(sql)
        return conn

    @pytest.fixture
    def data_layer(self, real_conn):
        return DataLayer(real_conn)

    def _insert_current_profile_12_data(self, conn, num_times=2, num_cells=3):
        """Insert sample data into pnors12 + pnorc12 to populate current_profile_12 view."""
        now = datetime.now()
        for t in range(num_times):
            time_str = f"12{t:02d}00"
            conn.execute(
                "INSERT INTO pnors12 (record_id, data_format, received_at, original_sentence, "
                "measurement_date, measurement_time, heading, pitch, roll, pressure, temperature) "
                "VALUES (?, 101, ?, 'test', '010126', ?, 10.0, 1.0, 0.5, 100.0, 15.0)",
                [100 + t, now - timedelta(minutes=t), time_str],
            )
            for c in range(num_cells):
                conn.execute(
                    "INSERT INTO pnorc12 (record_id, data_format, received_at, original_sentence, "
                    "measurement_date, measurement_time, cell_index, cell_distance, "
                    "vel1, vel2, vel3, vel4) "
                    "VALUES (?, 101, ?, 'test', '010126', ?, ?, ?, ?, ?, 0.0, 0.0)",
                    [
                        200 + t * num_cells + c,
                        now - timedelta(minutes=t),
                        time_str,
                        c,
                        float(c) * 2.0 + 0.5,
                        round(0.1 * (c + 1) + 0.01 * t, 4),
                        round(0.05 * (c + 1) + 0.005 * t, 4),
                    ],
                )

    def test_query_current_speed_heatmap_basic(self, data_layer, real_conn):
        """Test basic heatmap query from current_profile_12 view."""
        self._insert_current_profile_12_data(real_conn, num_times=2, num_cells=3)
        result = data_layer.query_current_speed_heatmap("current_profile_12", time_range="24h")
        assert "timestamps" in result
        assert "cell_indices" in result
        assert "speeds" in result
        assert len(result["timestamps"]) == 2
        assert len(result["cell_indices"]) == 3
        # speeds should be [cells][times]
        assert len(result["speeds"]) == 3
        assert len(result["speeds"][0]) == 2
        # current_profile_12 has vel1/vel2 but no speed/direction columns directly
        # So it should compute speed from vel1/vel2 via sqrt(vel1^2 + vel2^2)
        assert all(s is not None for row in result["speeds"] for s in row)

    def test_query_current_speed_heatmap_with_cell_distances(self, data_layer, real_conn):
        """Test heatmap query includes cell_distances when available."""
        self._insert_current_profile_12_data(real_conn, num_times=1, num_cells=2)
        result = data_layer.query_current_speed_heatmap("current_profile_12", time_range="24h")
        # current_profile_12 has cell_distance column
        assert result.get("cell_distances") is not None
        assert len(result["cell_distances"]) == 2

    def test_query_current_speed_heatmap_nonexistent_source(self, data_layer):
        """Test heatmap query with nonexistent source returns empty."""
        result = data_layer.query_current_speed_heatmap("nonexistent_table")
        assert result == {}

    def test_query_current_speed_heatmap_no_speed_cols(self, data_layer, real_conn):
        """Test heatmap query returns empty when no speed/vel columns exist."""
        # Create a table with no speed or vel columns
        real_conn.execute(
            "CREATE TABLE fake_current (received_at TIMESTAMP, measurement_date CHAR(6), "
            "measurement_time CHAR(6), cell_index INT)"
        )
        real_conn.execute(
            "INSERT INTO fake_current VALUES (current_timestamp, '010126', '120000', 0)"
        )
        result = data_layer.query_current_speed_heatmap("fake_current")
        assert result == {}

    def test_query_current_speed_heatmap_empty_data(self, data_layer, real_conn):
        """Test heatmap query with no rows returns empty."""
        result = data_layer.query_current_speed_heatmap("current_profile_12", time_range="24h")
        assert result == {}

    def test_query_current_speed_heatmap_time_range_all(self, data_layer, real_conn):
        """Test heatmap query with 'all' time range."""
        self._insert_current_profile_12_data(real_conn, num_times=1, num_cells=2)
        result = data_layer.query_current_speed_heatmap("current_profile_12", time_range="all")
        assert len(result["timestamps"]) == 1

    @patch("duckdb.DuckDBPyConnection.execute")
    def test_query_current_speed_heatmap_exception(self, mock_execute, data_layer):
        """Test heatmap query exception returns empty dict."""
        cols = [
            ColumnMetadata("received_at", ColumnType.TIMESTAMP),
            ColumnMetadata("vel1", ColumnType.NUMERIC),
            ColumnMetadata("vel2", ColumnType.NUMERIC),
            ColumnMetadata("cell_index", ColumnType.NUMERIC),
            ColumnMetadata("measurement_date", ColumnType.TEXT),
            ColumnMetadata("measurement_time", ColumnType.TEXT),
        ]
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource("current_profile_12", "Profile", cols)
            mock_execute.side_effect = Exception("DB Error")
            result = data_layer.query_current_speed_heatmap("current_profile_12")
            assert result == {}

    @patch("duckdb.DuckDBPyConnection.execute")
    def test_query_current_speed_heatmap_no_description(self, mock_execute, data_layer):
        """Test heatmap query returns empty when conn.description is None."""
        cols = [
            ColumnMetadata("received_at", ColumnType.TIMESTAMP),
            ColumnMetadata("vel1", ColumnType.NUMERIC),
            ColumnMetadata("vel2", ColumnType.NUMERIC),
            ColumnMetadata("cell_index", ColumnType.NUMERIC),
            ColumnMetadata("measurement_date", ColumnType.TEXT),
            ColumnMetadata("measurement_time", ColumnType.TEXT),
        ]
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource("current_profile_12", "Profile", cols)
            mock_conn = MagicMock()
            mock_conn.execute.return_value.fetchall.return_value = []
            mock_conn.description = None
            data_layer.conn = mock_conn
            result = data_layer.query_current_speed_heatmap("current_profile_12")
            assert result == {}

    def test_query_current_speed_heatmap_with_speed_direction_cols(self, data_layer, real_conn):
        """Test heatmap query from current_profile_34 with speed/direction columns.

        Covers lines 1009, 1014.
        """
        now = datetime.now()
        # Insert data into pnorh + pnors34 + pnorc34 to populate current_profile_34 view
        real_conn.execute(
            "INSERT INTO pnorh (record_id, data_format, received_at, original_sentence, "
            "measurement_date, measurement_time, error_code, status_code) "
            "VALUES (1, 103, ?, 'test', '010126', '120000', 0, '00000000')",
            [now],
        )
        real_conn.execute(
            "INSERT INTO pnors34 (record_id, data_format, received_at, original_sentence, "
            "measurement_date, measurement_time, heading, pitch, roll, pressure, temperature) "
            "VALUES (1, 103, ?, 'test', '010126', '120000', 10.0, 1.0, 0.5, 100.0, 15.0)",
            [now],
        )
        for c in range(2):
            real_conn.execute(
                "INSERT INTO pnorc34 (record_id, data_format, received_at, original_sentence, "
                "measurement_date, measurement_time, cell_index, cell_distance, speed, direction) "
                "VALUES (?, 103, ?, 'test', '010126', '120000', ?, ?, ?, ?)",
                [100 + c, now, c, float(c) * 2.0 + 0.5, 0.15 + c * 0.1, 90.0 + c * 45.0],
            )

        result = data_layer.query_current_speed_heatmap("current_profile_34", time_range="24h")
        assert len(result["timestamps"]) == 1
        assert len(result["cell_indices"]) == 2
        assert result["directions"] is not None
        # Should have actual speed/direction values
        assert result["speeds"][0][0] is not None
        assert result["directions"][0][0] is not None


class TestDetectCurrentProfileView:
    """Tests for DataLayer.detect_current_profile_view() auto-detection."""

    @pytest.fixture
    def real_conn(self):
        conn = duckdb.connect(":memory:")
        for sql in ALL_SCHEMA_SQL:
            conn.execute(sql)
        return conn

    @pytest.fixture
    def data_layer(self, real_conn):
        return DataLayer(real_conn)

    def test_returns_none_when_no_data(self, data_layer):
        """Return None when no current profile views have data."""
        result = data_layer.detect_current_profile_view()
        assert result is None

    def test_returns_highest_priority_view(self, data_layer):
        """Return current_profile_12 when it has data (highest priority)."""
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            # current_profile_12 has data, others don't
            def side_effect(name):
                if name == "current_profile_12":
                    return DataSource(name, "Profile 12", [], record_count=5)
                return None

            mock_meta.side_effect = side_effect
            result = data_layer.detect_current_profile_view()
            assert result == "current_profile_12"

    def test_skips_empty_views(self, data_layer):
        """Skip views with zero record count; return next with data."""
        with patch.object(data_layer, "get_source_metadata") as mock_meta:

            def side_effect(name):
                if name == "current_profile_12":
                    return DataSource(name, "Profile 12", [], record_count=0)
                if name == "current_profile_df100":
                    return DataSource(name, "DF100", [], record_count=3)
                return None

            mock_meta.side_effect = side_effect
            result = data_layer.detect_current_profile_view()
            assert result == "current_profile_df100"

    def test_falls_back_to_raw_tables(self, data_layer):
        """Fall back to pnorc12 when no joined views have data."""
        with patch.object(data_layer, "get_source_metadata") as mock_meta:

            def side_effect(name):
                if name == "pnorc12":
                    return DataSource(name, "PNORC12", [], record_count=10)
                if name in (
                    "current_profile_12",
                    "current_profile_df100",
                    "current_profile_34",
                ):
                    return DataSource(name, name, [], record_count=0)
                return None

            mock_meta.side_effect = side_effect
            result = data_layer.detect_current_profile_view()
            assert result == "pnorc12"

    def test_priority_order_is_correct(self, data_layer):
        """Verify the full priority order of candidates."""
        expected_order = [
            "current_profile_1",
            "current_profile_12",
            "current_profile_df100",
            "current_profile_34",
            "pnorc1",
            "pnorc12",
            "pnorc_df100",
            "pnorc34",
        ]
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            # All return None — capture the call order
            mock_meta.return_value = None
            data_layer.detect_current_profile_view()
            called_names = [call.args[0] for call in mock_meta.call_args_list]
            assert called_names == expected_order

    def test_stops_at_first_match(self, data_layer):
        """Stop checking after finding the first view with data."""
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            # All have data — should stop at first
            mock_meta.return_value = DataSource("any", "Any", [], record_count=1)
            result = data_layer.detect_current_profile_view()
            assert result == "current_profile_1"
            # Should only call get_source_metadata once
            assert mock_meta.call_count == 1

    def test_returns_pnorc34_as_last_resort(self, data_layer):
        """Return pnorc34 when it is the only source with data."""
        with patch.object(data_layer, "get_source_metadata") as mock_meta:

            def side_effect(name):
                if name == "pnorc34":
                    return DataSource(name, "PNORC34", [], record_count=2)
                return DataSource(name, name, [], record_count=0)

            mock_meta.side_effect = side_effect
            result = data_layer.detect_current_profile_view()
            assert result == "pnorc34"
