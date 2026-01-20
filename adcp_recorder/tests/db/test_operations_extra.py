"""Additional tests for database operations to reach 100% coverage."""

import pytest

from adcp_recorder.db import DatabaseManager
from adcp_recorder.db.operations import (
    expand_coefficients,
    expand_energy_densities,
    expand_pnorwd_values,
    insert_header_data,
    insert_pnora_data,
    insert_pnorb_data,
    insert_pnore_data,
    insert_pnorf_data,
    insert_pnorw_data,
    insert_pnorwd_data,
    insert_sensor_data,
    insert_velocity_data,
    query_header_data,
    query_pnora_data,
    query_pnorb_data,
    query_pnore_data,
    query_pnorf_data,
    query_pnorw_data,
    query_pnorwd_data,
    query_sensor_data,
    query_velocity_data,
)


@pytest.fixture
def conn():
    db = DatabaseManager(":memory:")
    return db.get_connection()


def test_insert_sensor_data_all_variants(conn):
    """Test insert_sensor_data for all PNORS variants."""
    base_data = {
        "date": "010123",
        "time": "120000",
        "heading": 90.0,
        "pitch": 1.0,
        "roll": 2.0,
        "pressure": 10.0,
        "temperature": 15.0,
        "sound_speed": 1500.0,
        "battery": 12.0,
        "checksum": "00",
    }

    # PNORS
    d = base_data.copy()
    d.update(
        {
            "sentence_type": "PNORS",
            "error_code": "0000",
            "status_code": "0000",
            "analog1": 0,
            "analog2": 0,
        }
    )
    insert_sensor_data(conn, "$PNORS", d)

    # PNORS1
    d = base_data.copy()
    d.update(
        {
            "sentence_type": "PNORS1",
            "error_code": "0000",
            "status_code": "0000",
            "heading_std_dev": 0.1,
            "pitch_std_dev": 0.1,
            "roll_std_dev": 0.1,
            "pressure_std_dev": 0.1,
        }
    )
    insert_sensor_data(conn, "$PNORS1", d)

    # PNORS2
    d = base_data.copy()
    d.update(
        {
            "sentence_type": "PNORS2",
            "error_code": "0000",
            "status_code": "0000",
            "heading_std_dev": 0.1,
            "pitch_std_dev": 0.1,
            "roll_std_dev": 0.1,
            "pressure_std_dev": 0.1,
        }
    )
    insert_sensor_data(conn, "$PNORS2", d)

    # PNORS3
    d = base_data.copy()
    d.update({"sentence_type": "PNORS3", "data_format": 103})
    insert_sensor_data(conn, "$PNORS3", d)

    # PNORS4
    d = base_data.copy()
    d.update({"sentence_type": "PNORS4", "data_format": 104})
    insert_sensor_data(conn, "$PNORS4", d)

    assert len(query_sensor_data(conn)) == 5

    with pytest.raises(ValueError):
        insert_sensor_data(conn, "$INVALID", {"sentence_type": "INVALID"})


def test_insert_velocity_data_all_variants(conn):
    """Test insert_velocity_data for all variants."""
    base_data = {
        "date": "010123",
        "time": "120000",
        "cell_index": 1,
        "vel1": 1.0,
        "vel2": 0.0,
        "vel3": 0.0,
        "vel4": 0.0,
        "amp1": 100,
        "amp2": 100,
        "amp3": 100,
        "amp4": 100,
        "corr1": 100,
        "corr2": 100,
        "corr3": 100,
        "corr4": 100,
        "amp_unit": 1.0,
        "corr_unit": 1.0,
        "speed": 1.0,
        "direction": 180.0,
        "velocity_unit": 0.5,
        "checksum": "00",
    }

    # PNORC
    d = base_data.copy()
    d.update({"sentence_type": "PNORC"})
    insert_velocity_data(conn, "$PNORC", d)

    # PNORC1
    d = base_data.copy()
    d.update({"sentence_type": "PNORC1"})
    insert_velocity_data(conn, "$PNORC1", d)

    # PNORC2
    d = base_data.copy()
    d.update({"sentence_type": "PNORC2"})
    insert_velocity_data(conn, "$PNORC2", d)

    # PNORC3
    d = base_data.copy()
    d.update({"sentence_type": "PNORC3"})
    insert_velocity_data(conn, "$PNORC3", d)

    # PNORC4
    d = base_data.copy()
    d.update({"sentence_type": "PNORC4"})
    insert_velocity_data(conn, "$PNORC4", d)

    assert len(query_velocity_data(conn)) == 3

    with pytest.raises(ValueError):
        insert_velocity_data(conn, "$INVALID", {"sentence_type": "INVALID"})


def test_insert_header_data(conn):
    """Test insert_header_data and query_header_data."""
    data = {
        "sentence_type": "PNORH3",
        "date": "010123",
        "time": "120000",
        "data_format": 103,
        "error_code": 0,
        "status_code": "00000000",
        "checksum": "00",
    }
    insert_header_data(conn, "$PNORH3", data)

    data["sentence_type"] = "PNORH4"
    data["data_format"] = 104
    insert_header_data(conn, "$PNORH4", data)

    results = query_header_data(conn)
    assert len(results) == 2


def test_complex_data_and_expansions(conn):
    """Test PNORE, PNORB, PNORW, PNORF, PNORWD, PNORA."""
    # PNORE
    insert_pnore_data(
        conn,
        "$PNORE",
        {
            "sentence_type": "PNORE",
            "date": "010123",
            "time": "120000",
            "spectrum_basis": 1,
            "num_frequencies": 2,
            "energy_densities": [1.0, 2.0],
            "start_frequency": 0.5,
            "step_frequency": 0.1,
        },
    )
    assert len(query_pnore_data(conn)) == 1
    assert len(expand_energy_densities(conn)) == 2

    # PNORB
    insert_pnorb_data(
        conn,
        "$PNORB",
        {
            "sentence_type": "PNORB",
            "date": "010123",
            "time": "120000",
            "spectrum_basis": 1,
            "processing_method": 1,
            "freq_low": 0.1,
            "freq_high": 0.5,
            "hm0": 1.0,
            "tm02": 2.0,
            "tp": 2.1,
            "dir_tp": 180.0,
            "spr_tp": 10.0,
            "main_dir": 185.0,
            "wave_error_code": "0000",
        },
    )
    assert len(query_pnorb_data(conn)) == 1

    # PNORW
    insert_pnorw_data(
        conn,
        "$PNORW",
        {
            "sentence_type": "PNORW",
            "date": "010123",
            "time": "120000",
            "spectrum_basis": 1,
            "processing_method": 1,
            "hm0": 1.0,
            "h3": 1.1,
            "h10": 1.2,
            "hmax": 1.3,
            "tm02": 2.0,
            "tp": 2.1,
            "tz": 2.2,
            "dir_tp": 180.0,
            "spr_tp": 10.0,
            "main_dir": 185.0,
            "uni_index": 0.5,
            "mean_pressure": 10.0,
            "num_no_detects": 0,
            "num_bad_detects": 0,
            "near_surface_speed": 1.0,
            "near_surface_dir": 180.0,
            "wave_error_code": "0000",
        },
    )
    assert len(query_pnorw_data(conn)) == 1

    # PNORF
    insert_pnorf_data(
        conn,
        "$PNORF",
        {
            "sentence_type": "PNORF",
            "date": "010123",
            "time": "120000",
            "coefficient_flag": "A1",
            "spectrum_basis": 1,
            "num_frequencies": 2,
            "coefficients": [0.1, 0.2],
            "start_frequency": 0.5,
            "step_frequency": 0.1,
        },
    )
    assert len(query_pnorf_data(conn)) == 1
    assert len(expand_coefficients(conn)) == 2

    # PNORWD
    insert_pnorwd_data(
        conn,
        "$PNORWD",
        {
            "sentence_type": "PNORWD",
            "date": "010123",
            "time": "120000",
            "direction_type": "MD",
            "spectrum_basis": 1,
            "num_frequencies": 2,
            "values": [180.0, 190.0],
            "start_frequency": 0.5,
            "step_frequency": 0.1,
        },
    )
    assert len(query_pnorwd_data(conn)) == 1
    assert len(expand_pnorwd_values(conn)) == 2

    # PNORA
    insert_pnora_data(
        conn,
        "$PNORA",
        {
            "sentence_type": "PNORA",
            "date": "010123",
            "time": "120000",
            "pressure": 10.5,
            "distance": 5.0,
            "quality": 2,
            "status": "00",
            "pitch": 1.0,
            "roll": 2.0,
        },
    )
    assert len(query_pnora_data(conn)) == 1
