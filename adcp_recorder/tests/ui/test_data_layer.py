"""Unit tests for dashboard data layer."""

from datetime import datetime, timedelta
from typing import Any, cast

import duckdb
import pytest

from adcp_recorder.db.schema import ALL_SCHEMA_SQL
from adcp_recorder.ui.data_layer import (
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
        from datetime import datetime

        ts = datetime.now()
        real_conn.execute(
            "INSERT INTO pnorc_df100 (record_id, received_at, original_sentence, measurement_date, "
            "measurement_time, cell_index, vel1) VALUES (1, ?, 'test', '010123', '120000', 1, 1.0)",
            [ts],
        )
        real_conn.execute(
            "INSERT INTO pnorc_df100 (record_id, received_at, original_sentence, measurement_date, "
            "measurement_time, cell_index, vel1) VALUES (2, ?, 'test', '010123', '120000', 2, 1.1)",
            [ts],
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

    def test_query_amplitude_heatmap_no_amp_columns(self, data_layer):
        """When the source has no amplitude-like columns, return an empty list."""
        assert data_layer.query_amplitude_heatmap("pnors_df100") == []

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


# ---------------------------------------------------------------------------
# Additional unit tests to exercise edge branches in DataLayer without
# touching the real DuckDB connection internals. These use small fake
# connection objects and/or ephemeral test tables to trigger specific
# exception/edge-handling paths reported as uncovered.
# ---------------------------------------------------------------------------


def test_query_velocity_profile_fallback_handles_missing_date_time(real_conn):
    """If timestamp equality fails and measurement_date/time columns are
    missing, the fallback loop should catch exceptions and return empty
    profile rather than raising."""
    import datetime as _dt

    # Create a minimal table without measurement_date/measurement_time
    real_conn.execute(
        "CREATE TABLE pnorc_custom (record_id INTEGER, "
        "received_at TIMESTAMP, original_sentence VARCHAR, "
        "cell_index INTEGER, vel1 DOUBLE)"
    )

    ts_insert = _dt.datetime.now() - _dt.timedelta(days=1)
    real_conn.execute(
        "INSERT INTO pnorc_custom (record_id, received_at, original_sentence, "
        "cell_index, vel1) VALUES (1, ?, 'test', 1, 1.0)",
        [ts_insert],
    )

    # Build a fresh DataLayer on the real connection for this test
    dl = DataLayer(real_conn)

    # Use a timestamp that will not match the inserted row so the code falls
    # back to the measurement_date/measurement_time loop and exercises the
    # exception-handling branch (columns missing -> SQL raises internally).
    res = dl.query_velocity_profile("pnorc_custom", timestamp=_dt.datetime.now())
    assert res["depths"] == []
    assert all(isinstance(v, list) and v == [] for v in res["velocities"].values())


def test_query_amplitude_heatmap_exec_raises_and_short_rows_are_skipped():
    """Cover the exception path and the short-row skip in
    query_amplitude_heatmap using a fake connection and a fabricated
    DataSource (avoids modifying the real DuckDB connection)."""
    from datetime import datetime

    now = datetime.now()

    # Helper fake DataSource with one amp column
    ds = DataSource(
        name="pnorc12",
        display_name="pnorc12",
        columns=[
            ColumnMetadata(name="received_at", column_type=ColumnType.TIMESTAMP),
            ColumnMetadata(name="cell_index", column_type=ColumnType.NUMERIC),
            ColumnMetadata(name="amp1", column_type=ColumnType.NUMERIC),
        ],
        record_count=1,
        has_timestamp=True,
        timestamp_column="received_at",
        category="Wave Data",
    )

    # Case A: execute() raises -> function should return []
    class BadConn:
        description = None

        def execute(self, sql, params=None):
            if "avg_amp" in sql:
                raise RuntimeError("boom")

            class _ResultEmptyA:
                def fetchall(self):
                    return []

            return _ResultEmptyA()

    dl = DataLayer(cast(Any, BadConn()))
    cast(Any, dl).get_source_metadata = lambda name: ds
    assert dl.query_amplitude_heatmap("pnorc12") == []

    # Case B: execute() returns rows that are too short -> these rows are
    # skipped and overall result is empty.
    class ShortRowConn:
        description = None

        def execute(self, sql, params=None):
            class _ResultShortRow:
                def fetchall(self):
                    return [(now,)]

            return _ResultShortRow()

    dl2 = DataLayer(cast(Any, ShortRowConn()))
    cast(Any, dl2).get_source_metadata = lambda name: ds
    assert dl2.query_amplitude_heatmap("pnorc12") == []


def test_query_directional_spectrum_wave_measurement_full_variants():
    """Exercise the `wave_measurement_full` parsing paths where JSON
    fields may already be native Python objects (not strings), and where
    frequencies may be missing."""
    from datetime import datetime

    # Fake connection that returns a single row for the wave_measurement_full
    class WMFConn:
        def __init__(self, row, cols):
            self._row = row
            # description should be a sequence of 7+ column tuples
            self.description = [(c, None) for c in cols]

        def execute(self, sql, params=None):
            class _ResultOneRow:
                def __init__(self, row):
                    self._row = row

                def fetchone(self):
                    return self._row

            return _ResultOneRow(self._row)

    # A) energy already a Python list, directions/spreads missing -> fallbacks
    energy_list = [1.0, 2.0]
    cols = [
        "received_at",
        "measurement_date",
        "measurement_time",
        "start_frequency",
        "step_frequency",
        "num_frequencies",
        "energy_densities",
        "directions",
        "spreads",
    ]

    now = datetime.now()
    row = (now, "010123", "120000", 0.5, 0.1, 2, energy_list, None, None)

    dl = DataLayer(cast(Any, WMFConn(row, cols)))
    cast(Any, dl).get_source_metadata = lambda name: DataSource(
        name="wave_measurement_full",
        display_name="Wave Measurement Full",
        columns=[],
        record_count=1,
        has_timestamp=True,
        timestamp_column="received_at",
        category="Wave Data",
    )

    spec = dl.query_directional_spectrum()
    assert spec["energy"] == energy_list
    assert spec["directions"] == [0.0, 0.0]
    assert spec["spreads"] == [0.0, 0.0]
    assert spec["frequencies"] == [0.5, 0.6]

    # B) missing frequency metadata -> frequencies should be empty
    row2: tuple[object, ...] = (now, "010123", "120000", None, None, None, energy_list, [], [])
    dl2 = DataLayer(cast(Any, WMFConn(row2, cols)))
    cast(Any, dl2).get_source_metadata = cast(Any, dl).get_source_metadata
    spec2 = dl2.query_directional_spectrum()
    assert spec2["frequencies"] == []


def test_query_directional_spectrum_fallback_and_error_paths():
    """Use a fake connection to drive the older pnore/pnorwd fallback logic
    through exception paths and missing-data returns.
    """
    from datetime import datetime

    # Helper DataSource stubs for pnore/pnorwd
    pnore_ds = DataSource(
        name="pnore_data",
        display_name="pnore_data",
        columns=[],
        record_count=0,
        has_timestamp=True,
        timestamp_column="received_at",
        category="Wave Data",
    )
    pnorwd_ds = DataSource(
        name="pnorwd_data",
        display_name="pnorwd_data",
        columns=[],
        record_count=0,
        has_timestamp=True,
        timestamp_column="received_at",
        category="Wave Data",
    )

    # Case: timestamp provided -> initial select returns None, then the
    # measurement_date/time fallback raises (should be handled and return {}).
    class BadFallbackConn:
        description = None

        def execute(self, sql, params=None):
            # If checking timestamp select -> return object with fetchone() -> None
            if "WHERE received_at = ?" in sql or "WHERE received_at =" in sql:

                class _ResultNoneTimestamp:
                    def fetchone(self):
                        return None

                return _ResultNoneTimestamp()

            # For the measurement_date/time fallback -> simulate SQL error
            if "measurement_date = ? AND measurement_time = ?" in sql:
                raise RuntimeError("bad fallback")

            # Any other query -> return None-ish
            class _ResultNoneFallback:
                def fetchone(self):
                    return None

            return _ResultNoneFallback()

    dl = DataLayer(cast(Any, BadFallbackConn()))
    cast(Any, dl).get_source_metadata = lambda name: (
        pnore_ds if name == "pnore_data" else (pnorwd_ds if name == "pnorwd_data" else None)
    )

    assert dl.query_directional_spectrum(timestamp=datetime.now()) == {}

    # Case: latest measurement is found but subsequent energy lookup returns
    # None -> should return {}
    class LatestButNoEnergyConn:
        description = None

        def execute(self, sql, params=None):
            if "SELECT DISTINCT e.measurement_date" in sql:

                class _ResultLatestFoundA:
                    def fetchone(self):
                        return ("010123", "120000", datetime.now())

                return _ResultLatestFoundA()

            if "FROM pnore_data" in sql and "measurement_date = ?" in sql:

                class _ResultNoneB:
                    def fetchone(self):
                        return None

                return _ResultNoneB()

            class _ResultNoneC:
                def fetchone(self):
                    return None

            return _ResultNoneC()

    dl2 = DataLayer(cast(Any, LatestButNoEnergyConn()))
    cast(Any, dl2).get_source_metadata = cast(Any, dl).get_source_metadata
    assert dl2.query_directional_spectrum() == {}

    # Case: energy row present but energy_densities is None -> return {}
    class EnergyNullConn:
        description = None

        def execute(self, sql, params=None):
            if "SELECT DISTINCT e.measurement_date" in sql:

                class _ResultEnergyLatest:
                    def fetchone(self):
                        return ("010123", "120000", datetime.now())

                return _ResultEnergyLatest()

            if "FROM pnore_data" in sql and "energy_densities" in sql:

                class _ResultEnergyRow:
                    def fetchone(self):
                        # start_f, step_f, num_f, energy_densities_json, ts
                        return (0.5, 0.1, 2, None, datetime.now())

                return _ResultEnergyRow()

            class _ResultNoneD:
                def fetchone(self):
                    return None

            return _ResultNoneD()

    dl3 = DataLayer(cast(Any, EnergyNullConn()))
    cast(Any, dl3).get_source_metadata = cast(Any, dl).get_source_metadata
    assert dl3.query_directional_spectrum() == {}

    # Case: num_f is non-integer -> int() raises and we fall back to n_freq = 0
    class BadNumFConn:
        description = None

        def execute(self, sql, params=None):
            if "SELECT DISTINCT e.measurement_date" in sql:

                class _ResultBadNumFLatest:
                    def fetchone(self):
                        return ("010123", "120000", datetime.now())

                return _ResultBadNumFLatest()

            if "FROM pnore_data" in sql and "energy_densities" in sql:

                class _ResultBadNumFRow:
                    def fetchone(self):
                        # invalid num_f string to trigger except path
                        return (0.5, 0.1, "bad", "[1.0,2.0]", datetime.now())

                return _ResultBadNumFRow()

            # md_data / ds_data -> return None so directions/spreads become []
            class _ResultBadNumFNone:
                def fetchone(self):
                    return None

            return _ResultBadNumFNone()

    dl4 = DataLayer(cast(Any, BadNumFConn()))
    cast(Any, dl4).get_source_metadata = cast(Any, dl).get_source_metadata
    res = dl4.query_directional_spectrum()
    # With n_freq == 0, directions/spreads should be empty lists and frequencies []
    assert res.get("frequencies") == []
    assert res.get("directions") == []
    assert res.get("spreads") == []
