"""Unit tests for database migration logic."""

from datetime import datetime
from typing import Any

import duckdb
import pytest

from adcp_recorder.db.migration import migrate_database, verify_migration


@pytest.fixture
def old_db_path(tmp_path):
    """Create a DuckDB database with the old (v0.1.x) schema and some data."""
    db_path = tmp_path / "old_adcp.duckdb"
    conn = duckdb.connect(str(db_path))

    # Create old tables
    conn.execute("""
        CREATE TABLE raw_lines (
            line_id BIGINT PRIMARY KEY,
            received_at TIMESTAMP,
            raw_sentence TEXT,
            parse_status VARCHAR,
            record_type VARCHAR,
            checksum_valid BOOLEAN,
            error_message TEXT
        )
    """)

    # PNORI family
    conn.execute(
        "CREATE TABLE pnori1 (config_id BIGINT PRIMARY KEY, received_at TIMESTAMP, "
        "original_sentence TEXT, instrument_type_name VARCHAR, instrument_type_code TINYINT, "
        "head_id VARCHAR, beam_count TINYINT, cell_count SMALLINT, blanking_distance DECIMAL, "
        "cell_size DECIMAL, coord_system_name VARCHAR, coord_system_code TINYINT, checksum VARCHAR)"
    )
    conn.execute(
        "CREATE TABLE pnori2 (config_id BIGINT PRIMARY KEY, received_at TIMESTAMP, "
        "original_sentence TEXT, instrument_type_name VARCHAR, instrument_type_code TINYINT, "
        "head_id VARCHAR, beam_count TINYINT, cell_count SMALLINT, blanking_distance DECIMAL, "
        "cell_size DECIMAL, coord_system_name VARCHAR, coord_system_code TINYINT, checksum VARCHAR)"
    )

    # PNORS family
    conn.execute(
        "CREATE TABLE pnors_df101 (record_id BIGINT PRIMARY KEY, received_at TIMESTAMP, "
        "original_sentence TEXT, measurement_date VARCHAR, measurement_time VARCHAR, "
        "error_code VARCHAR, status_code VARCHAR, battery DECIMAL, sound_speed DECIMAL, "
        "heading_std_dev DECIMAL, heading DECIMAL, pitch DECIMAL, pitch_std_dev DECIMAL, "
        "roll DECIMAL, roll_std_dev DECIMAL, pressure DECIMAL, pressure_std_dev DECIMAL, "
        "temperature DECIMAL, checksum VARCHAR)"
    )
    conn.execute(
        "CREATE TABLE pnors_df102 (record_id BIGINT PRIMARY KEY, received_at TIMESTAMP, "
        "original_sentence TEXT, measurement_date VARCHAR, measurement_time VARCHAR, "
        "error_code VARCHAR, status_code VARCHAR, battery DECIMAL, sound_speed DECIMAL, "
        "heading_std_dev DECIMAL, heading DECIMAL, pitch DECIMAL, pitch_std_dev DECIMAL, "
        "roll DECIMAL, roll_std_dev DECIMAL, pressure DECIMAL, pressure_std_dev DECIMAL, "
        "temperature DECIMAL, checksum VARCHAR)"
    )
    conn.execute(
        "CREATE TABLE pnors_df103 (record_id BIGINT PRIMARY KEY, received_at TIMESTAMP, "
        "original_sentence TEXT, measurement_date VARCHAR, measurement_time VARCHAR, "
        "battery DECIMAL, sound_speed DECIMAL, heading DECIMAL, pitch DECIMAL, roll DECIMAL, "
        "pressure DECIMAL, temperature DECIMAL, checksum VARCHAR)"
    )
    conn.execute(
        "CREATE TABLE pnors_df104 (record_id BIGINT PRIMARY KEY, received_at TIMESTAMP, "
        "original_sentence TEXT, measurement_date VARCHAR, measurement_time VARCHAR, "
        "battery DECIMAL, sound_speed DECIMAL, heading DECIMAL, pitch DECIMAL, roll DECIMAL, "
        "pressure DECIMAL, temperature DECIMAL, checksum VARCHAR)"
    )

    # PNORC family
    conn.execute(
        "CREATE TABLE pnorc_df101 (record_id BIGINT PRIMARY KEY, received_at TIMESTAMP, "
        "original_sentence TEXT, measurement_date VARCHAR, measurement_time VARCHAR, "
        "cell_index SMALLINT, cell_distance DECIMAL, vel1 DECIMAL, vel2 DECIMAL, "
        "vel3 DECIMAL, vel4 DECIMAL, amp1 DECIMAL, amp2 DECIMAL, amp3 DECIMAL, amp4 DECIMAL, "
        "corr1 SMALLINT, corr2 SMALLINT, corr3 SMALLINT, corr4 SMALLINT, checksum VARCHAR)"
    )
    conn.execute(
        "CREATE TABLE pnorc_df102 (record_id BIGINT PRIMARY KEY, received_at TIMESTAMP, "
        "original_sentence TEXT, measurement_date VARCHAR, measurement_time VARCHAR, "
        "cell_index SMALLINT, cell_distance DECIMAL, vel1 DECIMAL, vel2 DECIMAL, "
        "vel3 DECIMAL, vel4 DECIMAL, amp1 DECIMAL, amp2 DECIMAL, amp3 DECIMAL, amp4 DECIMAL, "
        "corr1 SMALLINT, corr2 SMALLINT, corr3 SMALLINT, corr4 SMALLINT, checksum VARCHAR)"
    )
    conn.execute(
        "CREATE TABLE pnorc_df103 (record_id BIGINT PRIMARY KEY, received_at TIMESTAMP, "
        "original_sentence TEXT, measurement_date VARCHAR, measurement_time VARCHAR, "
        "cell_index SMALLINT, cell_distance DECIMAL, speed DECIMAL, direction DECIMAL, "
        "checksum VARCHAR)"
    )
    conn.execute(
        "CREATE TABLE pnorc_df104 (record_id BIGINT PRIMARY KEY, received_at TIMESTAMP, "
        "original_sentence TEXT, measurement_date VARCHAR, measurement_time VARCHAR, "
        "cell_index SMALLINT, cell_distance DECIMAL, speed DECIMAL, direction DECIMAL, "
        "checksum VARCHAR)"
    )

    # PNORH family
    conn.execute(
        "CREATE TABLE pnorh_df103 (record_id BIGINT PRIMARY KEY, received_at TIMESTAMP, "
        "original_sentence TEXT, measurement_date VARCHAR, measurement_time VARCHAR, "
        "error_code INTEGER, status_code CHAR(8), checksum VARCHAR)"
    )
    conn.execute(
        "CREATE TABLE pnorh_df104 (record_id BIGINT PRIMARY KEY, received_at TIMESTAMP, "
        "original_sentence TEXT, measurement_date VARCHAR, measurement_time VARCHAR, "
        "error_code INTEGER, status_code CHAR(8), checksum VARCHAR)"
    )

    conn.execute("""
        CREATE TABLE echo_data (
            record_id BIGINT PRIMARY KEY,
            received_at TIMESTAMP,
            original_sentence TEXT,
            measurement_date VARCHAR,
            measurement_time VARCHAR,
            spectrum_basis INTEGER,
            start_frequency DOUBLE,
            step_frequency DOUBLE,
            num_frequencies INTEGER,
            energy_densities TEXT,
            checksum VARCHAR
        )
    """)

    conn.execute("""
        CREATE TABLE pnorw_data (
            record_id BIGINT PRIMARY KEY,
            received_at TIMESTAMP,
            sentence_type VARCHAR,
            original_sentence TEXT,
            measurement_date VARCHAR,
            measurement_time VARCHAR,
            spectrum_basis INTEGER,
            processing_method INTEGER,
            hm0 DOUBLE,
            hmax DOUBLE,
            tm02 DOUBLE,
            tp DOUBLE,
            mean_period DOUBLE,
            peak_dir DOUBLE,
            peak_directional_spread DOUBLE,
            mean_dir DOUBLE,
            wave_error_code INTEGER,
            checksum VARCHAR
        )
    """)

    # Insert data into ALL tables
    t = datetime.now()
    tables = [
        "pnori1",
        "pnori2",
        "pnors_df101",
        "pnors_df102",
        "pnors_df103",
        "pnors_df104",
        "pnorc_df101",
        "pnorc_df102",
        "pnorc_df103",
        "pnorc_df104",
        "pnorh_df103",
        "pnorh_df104",
    ]
    for tbl in tables:
        # Generic insertion for testing row count
        cols = conn.execute(f"DESCRIBE {tbl}").fetchall()
        # cols: (column_name, column_type, null, key, default, extra)
        # DuckDB DESCRIBE format: [column_name, column_type, null, key, default, extra]
        data: list[Any] = []
        for i, col in enumerate(cols):
            name, col_type, nullable = col[0], col[1], col[2]
            if i == 0:  # record_id / config_id
                data.append(1)
            elif name == "received_at":
                data.append(t)
            elif name in ("original_sentence", "instrument_type_name"):
                data.append("dummy")
            elif name == "head_id":
                data.append("dummy")
            elif name == "coord_system_name":
                data.append("ENU")
            elif name == "measurement_date":
                data.append("190126")
            elif name == "measurement_time":
                data.append("234500")
            elif name == "cell_index":
                data.append(1)
            elif name in ("beam_count", "cell_count"):
                data.append(4)
            elif name == "instrument_type_code":
                data.append(0)
            elif name == "coord_system_code":
                data.append(0)
            elif name in ("blanking_distance", "cell_size"):
                data.append(1.0)
            elif name == "heading":
                data.append(90.0)
            elif name in ("pitch", "roll", "pressure", "temperature", "battery", "sound_speed"):
                data.append(1.0)
            elif name in ("hm0", "hmax", "tm02", "tp", "mean_period", "peak_dir", "mean_dir"):
                data.append(1.0)
            elif name == "spectrum_basis":
                data.append(1)
            elif name == "num_frequencies":
                data.append(1)
            elif name == "energy_densities":
                data.append("[1.0]")
            elif name == "values":
                data.append("[1.0]")
            elif "VARCHAR" in col_type or "CHAR" in col_type or "TEXT" in col_type:
                data.append("dummy" if nullable == "NO" else None)
            elif "INT" in col_type or "DECIMAL" in col_type or "DOUBLE" in col_type:
                data.append(0 if nullable == "NO" else None)
            else:
                data.append(None)

        placeholders = ", ".join(["?"] * len(data))
        conn.execute(f"INSERT INTO {tbl} VALUES ({placeholders})", data)

    conn.execute("INSERT INTO raw_lines VALUES (1, ?, 'raw1', 'OK', 'PNORI', true, null)", [t])
    conn.execute(
        "INSERT INTO echo_data VALUES (1, ?, 'echo1', '190126', '234500', 1, 0.5, 0.1, 10, "
        "'[1.0, 2.0]', 'AB')",
        [t],
    )
    conn.execute(
        "INSERT INTO pnorw_data VALUES (1, ?, 'PNORW', 'pnorw1', '190126', '234500', 1, 1, 1.2, "
        "2.0, 5.0, 6.0, 5.5, 180.0, 10.0, 90.0, 0, 'GH')",
        [t],
    )

    conn.close()
    return db_path


def test_full_migration(old_db_path):
    """Test full database migration from v0.1.x to v0.2.0."""
    target_path = old_db_path.parent / "migrated.duckdb"

    stats = migrate_database(old_db_path, target_path)

    assert stats["echo_data->pnore_data"] == 1
    assert stats["pnori1/2->pnori12"] == 2
    assert stats["pnors_df101/102->pnors12"] == 2
    assert stats["pnors_df103/104->pnors34"] == 2
    assert stats["pnorc_df101/102->pnorc12"] == 2
    assert stats["pnorc_df103/104->pnorc34"] == 2
    assert stats["pnorh_df103/104->pnorh"] == 2
    assert stats["pnorw_data (field update)"] == 1

    # Verify tables in new database
    verification = verify_migration(target_path)
    assert verification["pnore_data"] == 1
    assert verification["pnori12"] == 2
    assert verification["pnors12"] == 2
    assert verification["pnors34"] == 2
    assert verification["pnorc12"] == 2
    assert verification["pnorc34"] == 2
    assert verification["pnorh"] == 2

    # Check specific fields in pnors12 (conversion)
    # Check specific fields in pnors12 (conversion)
    conn = duckdb.connect(str(target_path))
    res = conn.execute("SELECT data_format, heading FROM pnors12").fetchone()
    assert res is not None
    assert res[0] == 101
    assert float(res[1]) == 90.0

    # Check pnorw_data standardized names
    res = conn.execute("SELECT main_dir, dir_tp, spr_tp, tz FROM pnorw_data").fetchone()
    assert res is not None
    assert float(res[0]) == 90.0  # was mean_dir
    assert float(res[1]) == 180.0  # was peak_dir
    assert float(res[2]) == 10.0  # was peak_directional_spread
    assert float(res[3]) == 5.5  # was mean_period

    conn.close()


def test_migration_empty_tables(tmp_path):
    """Test migration with empty tables."""
    db_path = tmp_path / "empty_old.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE echo_data (record_id BIGINT)")
    conn.close()

    target_path = tmp_path / "empty_migrated.duckdb"
    stats = migrate_database(db_path, target_path)

    assert stats["echo_data->pnore_data"] == 0
    verification = verify_migration(target_path)
    assert verification["pnore_data"] == 0


def test_migration_source_not_found():
    """Test migration error when source does not exist."""
    with pytest.raises(Exception):
        migrate_database("non_existent.duckdb")


def test_migration_already_migrated(tmp_path):
    """Test migration on a database that is already migrated."""
    db_path = tmp_path / "already_new.duckdb"
    conn = duckdb.connect(str(db_path))
    # Create new schema
    from adcp_recorder.db.schema import ALL_SCHEMA_SQL

    for sql in ALL_SCHEMA_SQL:
        conn.execute(sql)
    conn.close()

    stats = migrate_database(db_path, in_place=True)
    # Should not crash and should skip migrations
    assert stats.get("echo_data->pnore_data", 0) == 0
