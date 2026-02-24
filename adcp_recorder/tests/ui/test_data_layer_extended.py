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

    def test_column_stats_success(self, data_layer, real_conn):
        """Lines 1022-1027."""
        real_conn.execute(
            "INSERT INTO pnors_df100 (record_id, measurement_date, measurement_time, "
            "original_sentence, temperature) "
            "VALUES (1, '010123', '120000', 'test', 25.0)"
        )
        res = data_layer.get_column_stats("pnors_df100", "temperature")
        assert res["avg"] == 25.0
        assert res["count"] == 1

    def test_column_stats_errors(self, data_layer):
        """Line 1002, 1006, 1028-1029."""
        # Line 1002 failure fallback
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

        # Stats query returns None
        mock_execute.side_effect = [MagicMock(fetchone=lambda: None)]
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource("t", "T", [ColumnMetadata("c", ColumnType.NUMERIC)])
            assert data_layer.get_column_stats("t", "c") == {}

        # get_column_info exception
        mock_execute.side_effect = Exception("Describe fail")
        assert data_layer.get_column_info("t") == []

        # query_time_series exception (430-431)
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource(
                "t",
                "T",
                [
                    ColumnMetadata("ts", ColumnType.TIMESTAMP),
                    ColumnMetadata("v", ColumnType.NUMERIC),
                ],
                has_timestamp=True,
                timestamp_column="ts",
            )
            mock_execute.side_effect = Exception("Time series fail")
            assert data_layer.query_time_series("t", ["v"])["x"] == []

        # query_spectrum_data exception (640-641)
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource("pnore_data", "Nodes", [])
            mock_execute.side_effect = Exception("Spectrum fail")
            assert data_layer.query_spectrum_data("pnore_data") == []

        # get_available_bursts exception (702-703)
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource("pnore_data", "Nodes", [], timestamp_column="ts")
            mock_execute.side_effect = Exception("Bursts fail")
            assert data_layer.get_available_bursts() == []

        # query_wave_energy exception (737-738)
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource("pnore_data", "Nodes", [])
            mock_execute.side_effect = Exception("Energy fail")
            assert data_layer.query_wave_energy("pnore_data") == []

        # query_directional_spectrum view exception (848-850)
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.side_effect = lambda name: (
                DataSource(name, name, []) if name == "wave_measurement_full" else None
            )
            mock_execute.side_effect = Exception("View query fail")
            # Should fall back and return empty or hit secondary fallback
            assert data_layer.query_directional_spectrum() == {}

        # execute_sql exception
        mock_execute.side_effect = Exception("SQL fail")
        assert data_layer.execute_sql("SELECT 1") == []

    def test_execute_sql_success(self, data_layer):
        """Lines 307-308."""
        res = data_layer.execute_sql("SELECT 1 as val")
        assert res == [{"val": 1}]

    def test_execute_sql_no_description(self, data_layer):
        """Lines 305-306."""
        mock_conn = MagicMock()
        data_layer.conn = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = []
        mock_conn.description = None
        assert data_layer.execute_sql("SELECT 1") == []

    def test_query_value_error(self, data_layer):
        """Lines 267-268."""
        with pytest.raises(ValueError, match="Unknown data source"):
            data_layer.query("nonexistent")

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

    def test_directional_spectrum_complex_fallbacks(self, data_layer, real_conn):
        """Lines 896-897, 905, 922-923, 927-944, 949-950, 976."""
        # Ensure wave_measurement_full doesn't exist to trigger fallback
        real_conn.execute("DROP VIEW IF EXISTS wave_measurement_full")
        data_layer._source_cache = {}

        # 921: No latest measurement
        assert data_layer.query_directional_spectrum() == {}

        # 905: Timestamp not found
        assert data_layer.query_directional_spectrum(timestamp=datetime.now()) == {}

        # Setup data for deeper fallback lines
        now = datetime(2023, 1, 1, 12, 0, 0)
        real_conn.execute(
            "INSERT INTO pnore_data (record_id, received_at, sentence_type, "
            "original_sentence, measurement_date, measurement_time, spectrum_basis, "
            "start_frequency, step_frequency, num_frequencies, energy_densities) "
            "VALUES (100, ?, 'PNORE', 'test', '010123', '120000', 1, 0.5, 0.1, 1, '[1.0]')",
            [now],
        )
        # Also need pnorwd_data for the latest query join (MD/DS)
        real_conn.execute(
            "INSERT INTO pnorwd_data (record_id, sentence_type, original_sentence, "
            "measurement_date, measurement_time, direction_type, values, spectrum_basis, "
            "num_frequencies) "
            "VALUES (101, 'PNORWD', 'test', '010123', '120000', 'MD', '[90.0]', 1, 1)"
        )
        real_conn.execute(
            "INSERT INTO pnorwd_data (record_id, sentence_type, original_sentence, "
            "measurement_date, measurement_time, direction_type, values, spectrum_basis, "
            "num_frequencies) "
            "VALUES (102, 'PNORWD', 'test', '010123', '120000', 'DS', '[15.0]', 1, 1)"
        )

        # Trigger latest query success (922)
        res = data_layer.query_directional_spectrum()
        assert res["measurement_date"] == "010123"

        # Trigger exact timestamp success (900)
        res = data_layer.query_directional_spectrum(timestamp=now)
        assert res["measurement_date"] == "010123"

        # 896-897, 881-883: Date format fallbacks
        # We delete by timestamp and try date/time strings
        real_conn.execute("UPDATE pnore_data SET received_at = NULL")
        # Query with a timestamp that should match '010123' and '120000'
        res = data_layer.query_directional_spectrum(timestamp=now)
        assert res["measurement_date"] == "010123"

    def test_directional_spectrum_fallback_errors(self, data_layer, real_conn):
        """Line 976 (frequencies empty if missing start_f/step_f)."""
        real_conn.execute("DROP VIEW IF EXISTS wave_measurement_full")
        data_layer._source_cache = {}
        now = datetime(2023, 1, 1, 12, 0, 0)
        real_conn.execute(
            "INSERT INTO pnore_data (record_id, received_at, sentence_type, "
            "original_sentence, measurement_date, measurement_time, spectrum_basis, "
            "num_frequencies, energy_densities) "
            "VALUES (110, ?, 'PNORE', 'test', '010123', '120000', 1, 1, '[1.0]')",
            [now],
        )
        res = data_layer.query_directional_spectrum(timestamp=now)
        assert res["frequencies"] == []

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

    def test_missing_source_metadata_returns_empty(self, data_layer):
        """Lines 542, 615, 666, 713."""
        assert data_layer.query_amplitude_heatmap("nonexistent") == []
        assert data_layer.query_spectrum_data("nonexistent") == []
        assert data_layer.query_wave_energy("nonexistent") == []
        assert data_layer.get_available_bursts(source_name="nonexistent") == []

    def test_query_amplitude_heatmap_no_amp_cols(self, data_layer, real_conn):
        """Line 556."""
        real_conn.execute("CREATE TABLE no_amp_table (received_at TIMESTAMP, cell_index INT)")
        assert data_layer.query_amplitude_heatmap("no_amp_table") == []

    def test_query_spectral_json_loading(self):
        """Lines 807, 812, 819."""
        # Using a mocked record to hit the json.loads branches in query_directional_spectrum
        mock_conn = MagicMock()
        dl = DataLayer(mock_conn)

        with patch.object(dl, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource(
                "wave_measurement_full", "Full", [], timestamp_column="received_at"
            )
            mock_conn.execute.return_value.fetchone.return_value = (
                datetime.now(),
                "010123",
                "120000",
                0.5,
                0.1,
                1,
                "[1.0]",
                "[90.0]",
                "[15.0]",
            )
            mock_conn.description = [
                ("received_at",),
                ("measurement_date",),
                ("measurement_time",),
                ("start_frequency",),
                ("step_frequency",),
                ("num_frequencies",),
                ("energy_densities",),
                ("directions",),
                ("spreads",),
            ]
            res = dl.query_directional_spectrum()
            assert res["energy"] == [1.0]
            assert res["directions"] == [90.0]
            assert res["spreads"] == [15.0]

    def test_source_categorization_unknown(self, data_layer, real_conn):
        """Line 251 (fallback to 'Other')."""
        real_conn.execute("CREATE TABLE unknown_table (id INT)")
        meta = data_layer.get_source_metadata("unknown_table")
        assert meta is not None
        assert meta.category == "Other"

    def test_get_column_info_exception(self, data_layer):
        """Line 299."""
        mock_conn = MagicMock()
        data_layer.conn = mock_conn
        mock_conn.execute.side_effect = Exception("DESCRIBE fail")
        assert data_layer.get_column_info("any") == []

    def test_get_column_info_success(self, data_layer):
        """Line 297."""
        res = data_layer.get_column_info("pnors_df100")
        assert len(res) > 0
        assert "record_id" in [c[0] for c in res]

    def test_query_success(self, data_layer, real_conn):
        """Lines 270-283."""
        real_conn.execute(
            "INSERT INTO pnors_df100 (record_id, measurement_date, measurement_time, "
            "original_sentence) "
            "VALUES (2, '010123', '120000', 'test')"
        )
        # Hits line 273 (order_by)
        res = data_layer.query("pnors_df100", columns=["record_id"], order_by="record_id")
        assert len(res) >= 1

        # Hits line 277 (source.has_timestamp fallback)
        res2 = data_layer.query("pnors_df100", columns=["record_id"], order_by=None)
        assert len(res2) >= 1

    def test_query_directional_spectrum_no_latest(self, data_layer):
        """Line 921."""
        mock_conn = MagicMock()
        data_layer.conn = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = None
        assert data_layer.query_directional_spectrum() == {}

    def test_get_column_stats_exception(self, data_layer):
        """Lines 1028-1029."""
        mock_conn = MagicMock()
        data_layer.conn = mock_conn
        mock_conn.execute.side_effect = Exception("Stats fail")
        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.return_value = DataSource("t", "T", [ColumnMetadata("c", ColumnType.NUMERIC)])
            assert data_layer.get_column_stats("t", "c") == {}

    def test_get_quality_metrics_loops_and_fallbacks(self):
        """Lines 1342-1343, 1349, 1369-1370."""
        # Use a fresh connection and DataLayer
        conn = duckdb.connect(":memory:")
        dl = DataLayer(conn)

        # Ensure parse_errors table exists and has data
        conn.execute(
            "CREATE TABLE parse_errors (error_id BIGINT, received_at TIMESTAMP, error_msg TEXT)"
        )
        conn.execute("INSERT INTO parse_errors VALUES (1, now(), 'test error')")

        # We need at least one total record to trigger error_rate calculation
        conn.execute("CREATE TABLE TmpMetricTable (received_at TIMESTAMP)")
        conn.execute("INSERT INTO TmpMetricTable VALUES (now())")

        with patch.object(dl, "get_available_sources") as mock_sources:
            mock_sources.return_value = [
                DataSource(
                    "TmpMetricTable", "Tmp", [], has_timestamp=True, timestamp_column="received_at"
                )
            ]
            # get_quality_metrics will check get_source_metadata("parse_errors")
            # We mock it to return a DataSource for the table we just created
            with patch.object(dl, "get_source_metadata") as mock_meta:
                mock_meta.side_effect = lambda name: (
                    DataSource(name, name, []) if name == "parse_errors" else None
                )
                metrics = dl.get_quality_metrics()
                assert "error_count" in metrics
                assert metrics["error_count"] == 1
                assert metrics["error_rate"] > 0

        # 1342-1343: Exception in sources loop
        mock_conn = MagicMock()
        dl.conn = mock_conn
        with patch.object(dl, "get_available_sources") as mock_sources2:
            mock_sources2.return_value = [
                DataSource("t", "T", [], has_timestamp=True, timestamp_column="ts")
            ]
            mock_conn.execute.side_effect = Exception("Loop fail")
            metrics = dl.get_quality_metrics()
            assert metrics["total_records"] == 0

            # 1369-1370: Exception in error count
            mock_conn.execute.side_effect = [
                MagicMock(),  # sources loop count
                Exception("Error query fail"),  # error count fail
            ]
            with patch.object(dl, "get_source_metadata") as mock_meta2:
                mock_meta2.side_effect = lambda name: (
                    DataSource(name, name, []) if name == "parse_errors" else None
                )
                metrics = dl.get_quality_metrics()
                assert "error_count" not in metrics

    def test_get_quality_metrics_errors_table_fallback(self):
        """Line 1349."""
        conn = duckdb.connect(":memory:")
        dl = DataLayer(conn)
        conn.execute("CREATE TABLE Errors (received_at TIMESTAMP, error_msg TEXT)")
        conn.execute("INSERT INTO Errors VALUES (now(), 'err')")
        with patch.object(dl, "get_available_sources", return_value=[]):
            with patch.object(dl, "get_source_metadata") as mock_meta:
                mock_meta.side_effect = lambda name: (
                    DataSource(name, name, []) if name == "Errors" else None
                )
                metrics = dl.get_quality_metrics()
                assert metrics["error_count"] == 1

    def test_get_quality_metrics_is_valid_and_filtering(self, data_layer, real_conn):
        """Lines 1311, 1332-1338."""
        # 1311: Skip error/raw tables
        real_conn.execute("CREATE TABLE raw_lines_table (id INT)")
        real_conn.execute("CREATE TABLE error_log (id INT)")
        metrics = data_layer.get_quality_metrics()
        assert "raw_lines_table" not in metrics["sources"]
        assert "error_log" not in metrics["sources"]

        # 1332-1338: is_valid column
        real_conn.execute(
            "CREATE TABLE valid_test (received_at TIMESTAMP, is_valid BOOLEAN, val FLOAT)"
        )
        real_conn.execute("INSERT INTO valid_test VALUES (now(), TRUE, 1.0)")
        real_conn.execute("INSERT INTO valid_test VALUES (now(), FALSE, 2.0)")
        data_layer._source_cache = {}
        metrics = data_layer.get_quality_metrics()
        # Find valid_test in total records
        assert metrics["sources"]["valid_test"] == 2
        assert metrics["invalid_records"] >= 1


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
            data_layer.detect_current_profile_view()
            assert mock_meta.call_count == 1
