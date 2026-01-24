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
    m_id = 11626120000
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
            data = {"hmo": 1.2, "tp": 8.0, "main_dir": 90.0}
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

    return str(base_path)


class TestParquetDataLayerCoverage:
    """Coverage tests for ParquetDataLayer missing lines."""

    def test_joined_views_creation(self, sample_parquet_dir):
        """Test that all joined views are created correctly."""
        layer = ParquetDataLayer(sample_parquet_dir)
        layer.load_data()

        views = layer.get_loaded_views()

        # Check base views
        assert "pq_pnorw" in views
        assert "pq_pnore" in views
        assert "pq_pnors" in views
        assert "pq_pnorc" in views
        assert "pq_pnors12" in views
        assert "pq_pnorc12" in views
        assert "pq_pnorh" in views
        assert "pq_pnors34" in views
        assert "pq_pnorc34" in views

        # Check joined views
        assert "wave_measurement" in views
        assert "wave_measurement_full" in views
        assert "current_profile_df100" in views
        assert "current_profile_12" in views
        assert "current_profile_34" in views

    def test_query_joined_views(self, sample_parquet_dir):
        """Verify that joined views actually return data."""
        layer = ParquetDataLayer(sample_parquet_dir)
        layer.load_data()

        # 1. Wave Measurement
        wm = layer.conn.execute(
            "SELECT hs, energy_densities, energy_start_freq FROM wave_measurement"
        ).fetchone()
        assert wm is not None
        assert wm[0] == 1.5
        assert wm[1] == json.dumps([0.1, 0.2, 0.3])
        assert wm[2] == 0.05

        # 2. Wave Measurement Full
        wmf = layer.conn.execute(
            "SELECT hs, band_hm0, coefficients, directional_values FROM wave_measurement_full"
        ).fetchone()
        assert wmf is not None
        assert wmf[1] == 1.2
        assert wmf[2] == json.dumps([1, 2])
        assert wmf[3] == json.dumps([10, 20])

        # 3. Current Profile DF100
        cp100 = layer.conn.execute(
            "SELECT heading, cell_index, speed FROM current_profile_df100"
        ).fetchone()
        assert cp100 is not None
        assert cp100[0] == 180.0
        assert cp100[1] == 1
        assert cp100[2] == 0.2

        # 4. Current Profile 12
        cp12 = layer.conn.execute(
            "SELECT heading, cell_distance, vel1 FROM current_profile_12"
        ).fetchone()
        assert cp12 is not None
        assert cp12[0] == 90.0
        assert cp12[1] == 2.5

        # 5. Current Profile 34
        cp34 = layer.conn.execute(
            "SELECT header_id, heading, speed FROM current_profile_34"
        ).fetchone()
        assert cp34 is not None
        assert cp34[0] == 1
        assert cp34[1] == 270.0
        assert cp34[2] == 0.5

    def test_resolve_source_name_fallback(self, sample_parquet_dir):
        """Test the regex-based fallback in resolve_source_name."""
        layer = ParquetDataLayer(sample_parquet_dir)
        layer.load_data()

        # pnors_df100 -> matches pnor[a-z]+ -> pnors -> pq_pnors
        assert layer.resolve_source_name("pnors_df100") == "pq_pnors"
        # pnorc12 -> matches pnor[a-z]+ -> pnorc12 -> pq_pnorc12
        assert layer.resolve_source_name("pnorc12") == "pq_pnorc12"
        # wave_data -> matches pnor[a-z]+ -> fail -> None
        assert layer.resolve_source_name("wave_data") is None

        # Test extraction of base record type with _data suffix
        # pnorw_data -> pq_pnorw
        assert layer.resolve_source_name("pnorw_data") == "pq_pnorw"

    def test_get_join_condition_exception(self, sample_parquet_dir):
        """Test the pass-through on exception in _get_join_condition."""
        layer = ParquetDataLayer(sample_parquet_dir)
        layer.load_data()

        # Pass non-existent view to trigger exception inside _get_join_condition
        cond = layer._get_join_condition("non_existent", "pq_pnorw", "n", "w")
        # Should fallback to date/time join
        assert "measurement_date" in cond
        assert "measurement_time" in cond

    def test_create_joined_views_exception_logging(self, sample_parquet_dir, caplog):
        """Test that failed view creation logs but doesn't crash."""
        layer = ParquetDataLayer(sample_parquet_dir)
        layer.load_data()

        # Mock connection to fail on execute
        from unittest.mock import MagicMock, patch

        import adcp_recorder.ui.parquet_data_layer as pdl

        mock_conn = MagicMock(spec=layer._conn)
        mock_conn.execute.side_effect = Exception("DB Failure")
        with patch.object(layer, "_conn", mock_conn):
            # Clear loaded views to re-trigger creation
            layer._loaded_views.add("pq_pnorw")
            layer._loaded_views.add("pq_pnore")

            with patch.object(pdl.logger, "debug") as mock_debug:
                layer._create_joined_views()
                # Verify that debug was called with a message containing "Failed to create"
                found = any(
                    "Failed to create" in str(args[0]) for args, kwargs in mock_debug.call_args_list
                )
                assert found, (
                    f"Expected 'Failed to create' log message, got {mock_debug.call_args_list}"
                )
