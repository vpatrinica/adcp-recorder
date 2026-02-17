"""Comprehensive coverage tests for ParquetDataLayer joined views and name resolution."""

import json
from datetime import datetime
from typing import Any

import polars as pl
import pytest

from adcp_recorder.ui.parquet_data_layer import ParquetDataLayer


@pytest.fixture
def sample_parquet_dir(tmp_path):
    """Create a sample parquet directory with multiple record types for joining."""
    base_path = tmp_path / "parquet"

    # Common metadata
    date_str = "011626"
    time_str = "120000"
    # New format YYMMDDHHMMSS -> 260116120000
    m_id = 260116120000
    ts = datetime(2026, 1, 16, 12, 0, 0)

    # 1. PNORW (Wave base)
    pnorw_dir = base_path / "PNORW" / "date=2026-01-16"
    pnorw_dir.mkdir(parents=True)
    pl.DataFrame(
        [
            {
                "received_at": ts,
                "measurement_date": date_str,
                "measurement_time": time_str,
                "measurement_id": m_id,
                "hs": 1.5,
                "tp": 10.0,
            }
        ]
    ).write_parquet(pnorw_dir / "pnorw.parquet")

    # 2. PNORE (Energy)
    pnore_dir = base_path / "PNORE" / "date=2026-01-16"
    pnore_dir.mkdir(parents=True)
    pl.DataFrame(
        [
            {
                "received_at": ts,
                "measurement_date": date_str,
                "measurement_time": time_str,
                "measurement_id": m_id,
                "energy_densities": json.dumps([0.1, 0.2, 0.3]),
                "start_frequency": 0.05,
                "step_frequency": 0.01,
                "num_frequencies": 3,
            }
        ]
    ).write_parquet(pnore_dir / "pnore.parquet")

    # 3. PNORS (Sensor)
    pnors_dir = base_path / "PNORS" / "date=2026-01-16"
    pnors_dir.mkdir(parents=True)
    pl.DataFrame(
        [
            {
                "received_at": ts,
                "measurement_date": date_str,
                "measurement_time": time_str,
                "measurement_id": m_id,
                "heading": 180.0,
                "pitch": 0.0,
                "roll": 0.0,
                "pressure": 10.0,
                "temperature": 15.0,
            }
        ]
    ).write_parquet(pnors_dir / "pnors.parquet")

    # 4. PNORC (Cell)
    pnorc_dir = base_path / "PNORC" / "date=2026-01-16"
    pnorc_dir.mkdir(parents=True)
    pl.DataFrame(
        [
            {
                "received_at": ts,
                "measurement_date": date_str,
                "measurement_time": time_str,
                "measurement_id": m_id,
                "cell_index": 1,
                "vel1": 0.1,
                "vel2": 0.1,
                "vel3": 0.1,
                "vel4": 0.1,
                "speed": 0.2,
                "direction": 45.0,
            }
        ]
    ).write_parquet(pnorc_dir / "pnorc.parquet")

    # 5. PNORS12 (Sensor 1/2) - Legacy fallback test (no measurement_id)
    pnors12_dir = base_path / "PNORS12" / "date=2026-01-16"
    pnors12_dir.mkdir(parents=True)
    pl.DataFrame(
        [
            {
                "received_at": ts,
                "measurement_date": date_str,
                "measurement_time": time_str,
                "heading": 90.0,
            }
        ]
    ).write_parquet(pnors12_dir / "pnors12.parquet")

    # 6. PNORC12 (Cell 1/2)
    pnorc12_dir = base_path / "PNORC12" / "date=2026-01-16"
    pnorc12_dir.mkdir(parents=True)
    pl.DataFrame(
        [
            {
                "received_at": ts,
                "measurement_date": date_str,
                "measurement_time": time_str,
                "cell_index": 1,
                "cell_distance": 2.5,
                "vel1": 0.2,
                "vel2": 0.2,
                "vel3": 0.2,
                "vel4": 0.2,
            }
        ]
    ).write_parquet(pnorc12_dir / "pnorc12.parquet")

    # 7. PNORH (Header)
    pnorh_dir = base_path / "PNORH" / "date=2026-01-16"
    pnorh_dir.mkdir(parents=True)
    pl.DataFrame(
        [
            {
                "received_at": ts,
                "measurement_date": date_str,
                "measurement_time": time_str,
                "record_id": 1,
                "data_format": "DF103",
                "error_code": 0,
                "status_code": 0,
            }
        ]
    ).write_parquet(pnorh_dir / "pnorh.parquet")

    # 8. PNORS34 (Sensor 3/4)
    pnors34_dir = base_path / "PNORS34" / "date=2026-01-16"
    pnors34_dir.mkdir(parents=True)
    pl.DataFrame(
        [
            {
                "received_at": ts,
                "measurement_date": date_str,
                "measurement_time": time_str,
                "heading": 270.0,
                "pitch": 1.0,
                "roll": 2.0,
                "pressure": 5.0,
                "temperature": 10.0,
            }
        ]
    ).write_parquet(pnors34_dir / "pnors34.parquet")

    # 9. PNORC34 (Cell 3/4)
    pnorc34_dir = base_path / "PNORC34" / "date=2026-01-16"
    pnorc34_dir.mkdir(parents=True)
    pl.DataFrame(
        [
            {
                "received_at": ts,
                "measurement_date": date_str,
                "measurement_time": time_str,
                "cell_index": 1,
                "cell_distance": 5.0,
                "speed": 0.5,
                "direction": 180.0,
            }
        ]
    ).write_parquet(pnorc34_dir / "pnorc34.parquet")

    # 10. PNORB, PNORF, PNORWD for Full Wave view
    for p in ["PNORB", "PNORF", "PNORWD"]:
        p_dir = base_path / p / "date=2026-01-16"
        p_dir.mkdir(parents=True)
        data: dict[str, Any] = {}
        if p == "PNORB":
            data = {"hm0": 1.2, "tp": 8.0, "main_dir": 90.0}
        elif p == "PNORF":
            data = {"coefficients": json.dumps([1, 2]), "coefficient_flag": "A1"}
        else:  # PNORWD
            data = {"values": json.dumps([10, 20]), "direction_type": "MD"}

        data.update(
            {
                "received_at": ts,
                "measurement_date": date_str,
                "measurement_time": time_str,
                "measurement_id": m_id,
            }
        )
        pl.DataFrame([data]).write_parquet(p_dir / f"{p.lower()}.parquet")

    # 11. PNORI (Instrument info)
    pnori_dir = base_path / "PNORI" / "date=2026-01-16"
    pnori_dir.mkdir(parents=True)
    pl.DataFrame(
        [
            {
                "received_at": ts,
                "measurement_date": date_str,
                "measurement_time": time_str,
                "measurement_id": m_id,
                "instrument_type_name": "ADCP",
                "cell_count": 10,
                "cell_size": 1.0,
            }
        ]
    ).write_parquet(pnori_dir / "pnori.parquet")

    # 12. PNORI12 (Instrument info 1/2)
    pnori12_dir = base_path / "PNORI12" / "date=2026-01-16"
    pnori12_dir.mkdir(parents=True)
    pl.DataFrame(
        [
            {
                "received_at": ts,
                "measurement_date": date_str,
                "measurement_time": time_str,
                "instrument_type_name": "ADCP12",
                "beam_count": 4,
                "cell_count": 20,
                "cell_size": 0.5,
            }
        ]
    ).write_parquet(pnori12_dir / "pnori12.parquet")

    return str(base_path)


class TestParquetDataLayerCoverage:
    """Coverage tests for ParquetDataLayer missing lines."""

    def test_joined_views_creation(self, sample_parquet_dir):
        """Test that all joined views are created correctly."""
        layer = ParquetDataLayer(sample_parquet_dir)
        layer.load_data()

        views = layer.get_loaded_views()

        assert "current_profile_df100" in views
        assert "current_profile_12" in views
        assert "pq_pnori12" in views

    def test_query_joined_views(self, sample_parquet_dir):
        """Verify that joined views actually return data with instrument info."""
        layer = ParquetDataLayer(sample_parquet_dir)
        layer.load_data()

        # 1. Current Profile DF100 (PNORS + PNORC + PNORI)
        cp100 = layer.conn.execute(
            "SELECT heading, speed, instrument_type_name FROM current_profile_df100"
        ).fetchone()
        assert cp100 is not None
        assert cp100[2] == "ADCP"

        # 2. Current Profile 12 (PNORS12 + PNORC12 + PNORI12)
        cp12 = layer.conn.execute(
            "SELECT heading, vel1, beam_count, cell_count FROM current_profile_12"
        ).fetchone()
        assert cp12 is not None
        assert cp12[0] == 90.0
        assert cp12[1] == 0.2
        assert cp12[2] == 4
        assert cp12[3] == 20

    def test_resolve_source_name_fallback(self, sample_parquet_dir):
        """Test the regex-based fallback in resolve_source_name."""
        layer = ParquetDataLayer(sample_parquet_dir)
        layer.load_data()

        assert layer.resolve_source_name("pnors_df100") == "pq_pnors"
        assert layer.resolve_source_name("pnorc12") == "pq_pnorc12"

    def test_get_join_condition_exception(self, sample_parquet_dir):
        """Test the pass-through on exception in _get_join_condition."""
        layer = ParquetDataLayer(sample_parquet_dir)
        layer.load_data()

        cond = layer._get_join_condition("non_existent", "pq_pnorw", "n", "w")
        assert cond == "1=1"

    def test_create_joined_views_exception_logging(self, sample_parquet_dir):
        """Test that failed view creation logs but doesn't crash."""
        from unittest.mock import MagicMock, patch

        import adcp_recorder.ui.parquet_data_layer as pdl

        layer = ParquetDataLayer(sample_parquet_dir)
        layer.load_data()

        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("DB Failure")
        with patch.object(layer, "_conn", mock_conn):
            layer._loaded_views.add("pq_pnorw")
            with patch.object(pdl.logger, "error") as mock_error:
                layer._create_joined_views()
                found = any(
                    "Failed to create" in str(args[0]) for args, _ in mock_error.call_args_list
                )
                assert found

    def test_current_profile_df100_fallback(self, tmp_path):
        """Test fallback projection in current_profile_df100 when wildcard join fails."""
        from unittest.mock import MagicMock, patch

        import duckdb

        base_path = tmp_path / "parquet_fallback"
        layer = ParquetDataLayer(base_path)
        layer._loaded_views.update({"pq_pnors", "pq_pnorc", "pq_pnori"})

        mock_conn = MagicMock()

        # Track whether fallback was triggered
        primary_attempted = False

        def smart_execute(sql, *args, **kwargs):
            nonlocal primary_attempted
            sql_upper = sql.upper()
            # Handle DESCRIBE queries for _get_view_columns and _get_join_condition
            if sql_upper.startswith("DESCRIBE "):
                res = MagicMock()
                if "PQ_PNORS" in sql_upper:
                    res.fetchall.return_value = [
                        ("received_at", "TIMESTAMP", "YES", None, None, None),
                        ("heading", "FLOAT", "YES", None, None, None),
                        ("pitch", "FLOAT", "YES", None, None, None),
                    ]
                elif "PQ_PNORC" in sql_upper:
                    res.fetchall.return_value = [
                        ("received_at", "TIMESTAMP", "YES", None, None, None),
                        ("cell_index", "INT", "NO", None, None, None),
                        ("speed", "FLOAT", "YES", None, None, None),
                        ("direction", "FLOAT", "YES", None, None, None),
                    ]
                elif "PQ_PNORI" in sql_upper:
                    res.fetchall.return_value = [
                        ("received_at", "TIMESTAMP", "YES", None, None, None),
                        ("instrument_type_name", "VARCHAR", "YES", None, None, None),
                        ("cell_count", "INT", "YES", None, None, None),
                        ("cell_size", "FLOAT", "YES", None, None, None),
                    ]
                else:
                    res.fetchall.return_value = []
                return res
            if "CREATE OR REPLACE VIEW CURRENT_PROFILE_DF100" in sql_upper:
                if not primary_attempted:
                    # First attempt (primary path with s.*) fails
                    primary_attempted = True
                    raise duckdb.Error("Ambiguous")
                # Fallback path succeeds
            return MagicMock()

        with patch.object(layer, "_conn", mock_conn):
            mock_conn.execute.side_effect = smart_execute
            layer._create_joined_views()
            assert "current_profile_df100" in layer._loaded_views
            calls = [c[0][0].upper() for c in mock_conn.execute.call_args_list]
            # Verify fallback enumerates columns explicitly (no s.*)
            fallback_calls = [
                s
                for s in calls
                if "CREATE OR REPLACE VIEW CURRENT_PROFILE_DF100" in s and "S.*" not in s
            ]
            assert len(fallback_calls) >= 1, "Fallback should enumerate columns without s.*"
            # Verify speed and direction are NOT renamed to cell_speed/cell_direction
            for s in fallback_calls:
                assert "AS CELL_SPEED" not in s, "speed should not be aliased as cell_speed"
                assert "AS CELL_DIRECTION" not in s, "direction should not be aliased"

    def test_df101_102_distance_alias(self, tmp_path):
        """Test DF101/102 'distance' -> 'cell_distance' alias (lines 787-788).

        When PNORC12 parquet has 'distance' (not 'cell_distance'), the code
        should alias it as 'cell_distance' for consistency with the DB schema.
        """
        from datetime import datetime

        import polars as pl

        base_path = tmp_path / "parquet_dist12"
        ts = datetime(2026, 1, 16, 12, 0, 0)

        # PNORS12 with measurement_date/time for join
        pnors12_dir = base_path / "PNORS12" / "date=2026-01-16"
        pnors12_dir.mkdir(parents=True)
        pl.DataFrame(
            [
                {
                    "received_at": ts,
                    "measurement_date": "011626",
                    "measurement_time": "120000",
                    "heading": 90.0,
                }
            ]
        ).write_parquet(pnors12_dir / "pnors12.parquet")

        # PNORC12 with 'distance' instead of 'cell_distance'
        pnorc12_dir = base_path / "PNORC12" / "date=2026-01-16"
        pnorc12_dir.mkdir(parents=True)
        pl.DataFrame(
            [
                {
                    "received_at": ts,
                    "measurement_date": "011626",
                    "measurement_time": "120000",
                    "cell_index": 1,
                    "distance": 2.5,
                    "vel1": 0.2,
                    "vel2": 0.2,
                    "vel3": 0.2,
                    "vel4": 0.2,
                }
            ]
        ).write_parquet(pnorc12_dir / "pnorc12.parquet")

        layer = ParquetDataLayer(str(base_path))
        layer.load_data()

        assert "current_profile_12" in layer._loaded_views

        # Verify the alias: 'distance' should appear as 'cell_distance'
        result = layer.conn.execute("SELECT cell_distance FROM current_profile_12").fetchone()
        assert result is not None
        assert result[0] == 2.5

    def test_df103_104_distance_alias(self, tmp_path):
        """Test DF103/104 'distance' -> 'cell_distance' alias (line 842).

        When PNORC34 parquet has 'distance' (not 'cell_distance'), the code
        should alias it as 'cell_distance' for consistency with the DB schema.
        """
        from datetime import datetime

        import polars as pl

        base_path = tmp_path / "parquet_dist34"
        ts = datetime(2026, 1, 16, 12, 0, 0)
        date_str = "011626"
        time_str = "120000"

        # PNORH (header)
        pnorh_dir = base_path / "PNORH" / "date=2026-01-16"
        pnorh_dir.mkdir(parents=True)
        pl.DataFrame(
            [
                {
                    "received_at": ts,
                    "measurement_date": date_str,
                    "measurement_time": time_str,
                    "record_id": 1,
                    "data_format": "DF103",
                    "error_code": 0,
                    "status_code": 0,
                }
            ]
        ).write_parquet(pnorh_dir / "pnorh.parquet")

        # PNORS34 (sensor)
        pnors34_dir = base_path / "PNORS34" / "date=2026-01-16"
        pnors34_dir.mkdir(parents=True)
        pl.DataFrame(
            [
                {
                    "received_at": ts,
                    "measurement_date": date_str,
                    "measurement_time": time_str,
                    "heading": 270.0,
                    "pitch": 1.0,
                    "roll": 2.0,
                    "pressure": 5.0,
                    "temperature": 10.0,
                }
            ]
        ).write_parquet(pnors34_dir / "pnors34.parquet")

        # PNORC34 with 'distance' instead of 'cell_distance'
        pnorc34_dir = base_path / "PNORC34" / "date=2026-01-16"
        pnorc34_dir.mkdir(parents=True)
        pl.DataFrame(
            [
                {
                    "received_at": ts,
                    "measurement_date": date_str,
                    "measurement_time": time_str,
                    "cell_index": 1,
                    "distance": 5.0,
                    "speed": 0.5,
                    "direction": 180.0,
                }
            ]
        ).write_parquet(pnorc34_dir / "pnorc34.parquet")

        layer = ParquetDataLayer(str(base_path))
        layer.load_data()

        assert "current_profile_34" in layer._loaded_views

        # Verify the alias: 'distance' should appear as 'cell_distance'
        result = layer.conn.execute("SELECT cell_distance FROM current_profile_34").fetchone()
        assert result is not None
        assert result[0] == 5.0

    def test_time_column_alias_for_measurement_time(self, tmp_path):
        """If a parquet file uses 'time' instead of 'measurement_time',
        the layer should alias it to 'measurement_time' when creating the view
        (covers lines around the measurement_time alias path).
        """
        from datetime import datetime

        import polars as pl

        base_path = tmp_path / "parquet_time_alias"
        ts = datetime(2026, 1, 16, 12, 0, 0)

        # PNORC with 'time' column (not 'measurement_time')
        pnorc_dir = base_path / "PNORC" / "date=2026-01-16"
        pnorc_dir.mkdir(parents=True)
        pl.DataFrame(
            [
                {
                    "received_at": ts,
                    "measurement_date": "011626",
                    "time": "120000",
                    "cell_index": 1,
                    "cell_distance": 3.3,
                    "speed": 0.5,
                }
            ]
        ).write_parquet(pnorc_dir / "pnorc.parquet")

        layer = ParquetDataLayer(str(base_path))
        layer.load_data()

        # Verify base view for PNORC exists and measurement_time column was aliased
        cols = [c[0].lower() for c in layer.conn.execute("DESCRIBE pq_pnorc").fetchall()]
        assert "measurement_time" in cols
