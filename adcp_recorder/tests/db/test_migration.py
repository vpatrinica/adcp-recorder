import logging
import sys
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import duckdb
import pytest

from adcp_recorder.db.migration import (
    ensure_pnorw_h3,
    get_old_table_exists,
    get_table_row_count,
    main,
    migrate_database,
    migrate_pnorw_fields,
    verify_migration,
)


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


def test_migration_intermediate_schema_missing_h3(tmp_path):
    """Test migration when database is in intermediate schema state (missing h3)."""
    db_path = tmp_path / "intermediate.duckdb"
    conn = duckdb.connect(str(db_path))

    # Create pnorw_data with NEW field names but MISSING h3
    # This simulates a state where pnorw_data was migrated/created partially
    conn.execute("""
        CREATE SEQUENCE pnorw_data_seq;
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
            tz DOUBLE,       -- was mean_period (new name)
            dir_tp DOUBLE,   -- was peak_dir (new name)
            spr_tp DOUBLE,   -- was peak_directional_spread (new name)
            main_dir DOUBLE, -- was mean_dir (new name)
            wave_error_code INTEGER,
            checksum VARCHAR
            -- Missing: h3, h10, uni_index, mean_pressure, num_detects, near_surface...
        )
    """)
    conn.execute(
        "INSERT INTO pnorw_data VALUES (1, null, 'PNORW', 'src', '010101', '000000', "
        "1, 1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0, 'CS')"
    )
    conn.close()

    target_path = tmp_path / "intermediate_migrated.duckdb"
    stats = migrate_database(db_path, target_path)

    # Verify ensure_pnorw_h3 ran
    # migrate_pnorw_fields should return 0 (skipped because new names present)
    # ensure_pnorw_h3 should return 1 (added columns)
    assert stats.get("pnorw_data (field update)", 0) == 0
    assert stats.get("pnorw_data (h3 fix)", 0) == 1

    # Verify h3 exists in target
    conn = duckdb.connect(str(target_path))
    cols = [
        row[0]
        for row in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'pnorw_data'"
        ).fetchall()
    ]
    conn.close()

    assert "h3" in cols
    assert "h10" in cols
    assert "uni_index" in cols


def test_migration_intermediate_schema_already_has_h3(tmp_path):
    """Test ensure_pnorw_h3 when h3 already exists."""
    db_path = tmp_path / "intermediate_with_h3.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE pnorw_data (record_id BIGINT, h3 DECIMAL(5,2))")
    conn.close()

    from adcp_recorder.db.migration import ensure_pnorw_h3

    conn = duckdb.connect(str(db_path))
    count = ensure_pnorw_h3(conn)
    conn.close()

    # Should perform no ops and return row count (0)
    assert count == 0


def test_migration_pnorc_alternative_column(tmp_path):
    """Test migration of pnorc tables with 'distance' instead of 'cell_distance'."""
    db_path = tmp_path / "pnorc_dist.duckdb"
    conn = duckdb.connect(str(db_path))

    # Create pnorc_df101 with 'distance' column
    conn.execute(
        "CREATE TABLE pnorc_df101 (record_id BIGINT PRIMARY KEY, received_at TIMESTAMP, "
        "original_sentence TEXT, measurement_date VARCHAR, measurement_time VARCHAR, "
        "cell_index SMALLINT, distance DECIMAL, vel1 DECIMAL, vel2 DECIMAL, "
        "vel3 DECIMAL, vel4 DECIMAL, amp1 DECIMAL, amp2 DECIMAL, amp3 DECIMAL, amp4 DECIMAL, "
        "corr1 SMALLINT, corr2 SMALLINT, corr3 SMALLINT, corr4 SMALLINT, checksum VARCHAR)"
    )
    conn.execute(
        "INSERT INTO pnorc_df101 VALUES (1, null, 'src', '010101', '000000', 1, 10.5, "
        "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'CS')"
    )
    conn.close()

    target_path = tmp_path / "pnorc_migrated.duckdb"
    stats = migrate_database(db_path, target_path)

    assert stats["pnorc_df101/102->pnorc12"] == 1

    # Verify migration picked up 'distance' value
    conn = duckdb.connect(str(target_path))
    res = conn.execute("SELECT cell_distance FROM pnorc12").fetchone()
    conn.close()

    assert res is not None
    assert float(res[0]) == 10.5


def test_migration_main(tmp_path, capsys):
    """Test the main CLI point with verification and in-place."""
    db_path = tmp_path / "cli_test.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE echo_data (id INT)")
    conn.close()

    # Test in-place with verify
    with patch.object(sys, "argv", ["migration.py", str(db_path), "--in-place", "--verify"]):
        main()

    # Test with target and verify
    target = tmp_path / "cli_migrated.duckdb"
    # Create again since in-place might have changed it or we want fresh start
    db_path2 = tmp_path / "cli_test2.duckdb"
    conn = duckdb.connect(str(db_path2))
    conn.execute("CREATE TABLE echo_data (id INT)")
    conn.close()
    with patch.object(
        sys, "argv", ["migration.py", str(db_path2), "--target", str(target), "--verify"]
    ):
        main()
    assert target.exists()


def test_migration_pnorw_empty(tmp_path):
    """Test migration when pnorw_data is empty."""
    db_path = tmp_path / "pnorw_empty.duckdb"
    conn = duckdb.connect(str(db_path))
    # pnorw_data exists but has old schema names and 0 rows
    conn.execute("CREATE TABLE pnorw_data (record_id BIGINT, mean_dir DOUBLE)")
    conn.close()

    target_path = tmp_path / "pnorw_empty_migrated.duckdb"
    stats = migrate_database(db_path, target_path)
    assert stats.get("pnorw_data (field update)", 0) == 0


def test_migration_secondary_empty_data(tmp_path):
    """Test migration where secondary tables exist but are empty."""
    db_path = tmp_path / "empty_data.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE pnori1 (id INT)")
    conn.execute("CREATE TABLE pnori2 (id INT)")  # Exists but empty
    conn.close()

    target_path = tmp_path / "empty_data_migrated.duckdb"
    stats = migrate_database(db_path, target_path)
    assert stats.get("pnori1/2->pnori12", 0) == 0


def test_utils_exceptions():
    """Test exception handling in utility functions."""

    # Mock connection that raises exception
    bad_conn = Mock()
    bad_conn.execute.side_effect = Exception("DB Error")

    assert get_old_table_exists(bad_conn, "some_table") is False
    assert get_table_row_count(bad_conn, "some_table") == 0


def test_ensure_pnorw_h3_exception(tmp_path, caplog):
    """Test exception handling during column addition in ensure_pnorw_h3."""

    db_path = tmp_path / "h3_error.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE pnorw_data (id INT)")  # Exists but missing h3

    mock_conn = MagicMock()
    # first call: get_old_table_exists -> execute(...).fetchone() -> [1] (exists)
    # second call: check h3 -> execute(...).fetchone() -> None (missing)
    # third call: get_table_row_count -> execute(...).fetchone() -> [0]
    # fourth call: ALTER TABLE -> raise Exception

    mock_cursor = MagicMock()
    mock_conn.execute.return_value = mock_cursor

    def side_effect(query, params=None):
        if "information_schema.tables" in query:
            mock_cursor.fetchone.return_value = [1]
        elif "information_schema.columns" in query:
            mock_cursor.fetchone.return_value = None
        elif "COUNT(*)" in query:
            mock_cursor.fetchone.return_value = [0]
        elif "ALTER TABLE" in query:
            raise Exception("Serious Error")
        return mock_cursor

    mock_conn.execute.side_effect = side_effect

    with caplog.at_level(logging.WARNING):
        ensure_pnorw_h3(mock_conn)
        assert "Failed to add column" in caplog.text


def test_migrate_pnorw_fields_exception(caplog):
    """Test exception handling in migrate_pnorw_fields version check."""

    # Mock connection that raises exception during schema check
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.execute.return_value = mock_cursor

    # First call (get_old_table_exists) returns True
    # Second call (execute for column_name) raises Exception
    def side_effect(query, params=None):
        if "information_schema.tables" in query:
            return MagicMock(fetchone=lambda: [1])
        raise Exception("Inner DB Error")

    mock_conn.execute.side_effect = side_effect

    # If old_schema is False (via exception), it skips migration and returns 0
    count = migrate_pnorw_fields(mock_conn)
    assert count == 0


def test_ensure_pnorw_h3_check_exception(tmp_path, caplog):
    """Test exception handling during h3 check in ensure_pnorw_h3."""
    db_path = tmp_path / "h3_check_error.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE pnorw_data (id INT)")

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.execute.return_value = mock_cursor

    def side_effect(query, params=None):
        if "information_schema.tables" in query:
            # Table exists
            mock_cursor.fetchone.return_value = [1]
        elif "AND column_name = 'h3'" in query:
            # Checking for h3 raises exception
            raise Exception("DB Error checking column")
        return mock_cursor

    mock_conn.execute.side_effect = side_effect

    # Should handle exception and return 0
    count = ensure_pnorw_h3(mock_conn)
    assert count == 0


def test_ensure_is_valid_column_exception(caplog):
    """Exercise the exception branch when checking/adding `is_valid` in migration."""
    from adcp_recorder.db import migration

    mock_conn = MagicMock()

    # get_old_table_exists should return True for one table to trigger the loop
    def exists_side(table_conn, table_name):
        # Return True for a table that exists in ensure_is_valid_column's table list
        return table_name == "pnori"

    # Replace the real check so function enters the try/except branch
    patcher = patch("adcp_recorder.db.migration.get_old_table_exists", side_effect=exists_side)
    patcher.start()

    # Simulate failure during PRAGMA table_info (raises) to hit except block
    def exec_side(query, params=None):
        if "PRAGMA table_info" in str(query):
            raise Exception("Schema read failure")
        return MagicMock()

    mock_conn.execute.side_effect = exec_side

    with caplog.at_level(logging.WARNING):
        migration.ensure_is_valid_column(mock_conn)
        assert "Failed to check/add is_valid" in caplog.text

    patcher.stop()


def test_migrate_pnorc_df101_102_exception(tmp_path):
    """Test exception handling in migrate_pnorc_df101_102 column check."""
    from adcp_recorder.db.migration import migrate_pnorc_df101_102

    # Mock connection that exists but fails on PRAGMA table_info
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.execute.return_value = mock_cursor

    def side_effect(query, params=None):
        if "information_schema.tables" in query:
            return Mock(fetchone=lambda: [1])
        elif "COUNT(*)" in query:
            return Mock(fetchone=lambda: [10])
        elif "PRAGMA table_info" in query:
            raise Exception("DB Error reading schema")
        return mock_cursor

    mock_conn.execute.side_effect = side_effect

    # Should fall back to cell_distance and try insert
    # The insert will fail (mock doesn't handle it) but we check if it tried to run
    try:
        migrate_pnorc_df101_102(mock_conn)
    except Exception:
        pass  # Expected since our mock setup is minimal

    # Verify that it tried to insert using cell_distance (default fallback)
    calls = mock_conn.execute.call_args_list
    insert_call = next((c for c in calls if "INSERT INTO pnorc12" in str(c)), None)
    assert insert_call is not None
    assert "COALESCE(cell_distance, 0.0)" in insert_call[0][0]


def test_migrate_pnorc_df103_104_exception(tmp_path):
    """Test exception handling in migrate_pnorc_df103_104 column check."""
    from adcp_recorder.db.migration import migrate_pnorc_df103_104

    # Mock connection that exists but fails on PRAGMA table_info
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.execute.return_value = mock_cursor

    def side_effect(query, params=None):
        if "information_schema.tables" in query:
            return Mock(fetchone=lambda: [1])
        elif "COUNT(*)" in query:
            return Mock(fetchone=lambda: [10])
        elif "PRAGMA table_info" in query:
            raise Exception("DB Error reading schema")
        return mock_cursor

    mock_conn.execute.side_effect = side_effect

    # Should fall back to cell_distance and try insert
    try:
        migrate_pnorc_df103_104(mock_conn)
    except Exception:
        pass

    # Verify that it tried to insert using cell_distance (default fallback)
    calls = mock_conn.execute.call_args_list
    insert_call = next((c for c in calls if "INSERT INTO pnorc34" in str(c)), None)
    assert insert_call is not None
    assert "COALESCE(cell_distance, 0.0)" in insert_call[0][0]


def test_ensure_pnorw_h3_table_not_found():
    """Test ensure_pnorw_h3 returns 0 when pnorw_data table does not exist."""
    # Mock connection
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.execute.return_value = mock_cursor

    # Mock get_old_table_exists to return False
    def side_effect(query, params=None):
        if "information_schema.tables" in query:
            return Mock(fetchone=lambda: [0])
        return mock_cursor

    mock_conn.execute.side_effect = side_effect

    count = ensure_pnorw_h3(mock_conn)
    assert count == 0


def test_migration_all_empty_secondary(tmp_path):
    """Test migration with all secondary tables empty/missing."""
    db_path = tmp_path / "all_empty_secondary.duckdb"
    conn = duckdb.connect(str(db_path))
    # Create all first tables but no second tables
    tables = [
        "pnors_df101",
        "pnors_df103",
        "pnorc_df101",
        "pnorc_df103",
        "pnorh_df103",
        "pnorw_data",
    ]
    for tbl in tables:
        # Check if table has mean_dir for pnorw
        if tbl == "pnorw_data":
            conn.execute(f"CREATE TABLE {tbl} (id INT, mean_dir DOUBLE)")
        else:
            conn.execute(f"CREATE TABLE {tbl} (id INT)")
    conn.close()

    target_path = tmp_path / "all_empty_migrated.duckdb"
    stats = migrate_database(db_path, target_path)
    assert stats.get("pnors_df101/102->pnors12", 0) == 0


def test_migration_main_default_target(tmp_path):
    """Test main function default target path logic."""
    db_path = tmp_path / "default_target.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE echo_data (id INT)")
    conn.close()

    with patch.object(sys, "argv", ["migration.py", str(db_path), "--verify"]):
        main()

    expected = db_path.parent / "default_target_migrated.duckdb"
    assert expected.exists()


def test_migration_error_handling(tmp_path):
    """Test error handling in migrate_database."""
    db_path = tmp_path / "error_trigger.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE echo_data (id INT)")
    conn.close()

    # Trigger error during migration (by mocking create_new_schema to fail)
    with patch(
        "adcp_recorder.db.migration.create_new_schema", side_effect=Exception("Fatal Error")
    ):
        with pytest.raises(Exception) as excinfo:
            migrate_database(db_path, tmp_path / "fail.duckdb")
        assert "Migration failed" in str(excinfo.value)


def test_migration_empty_secondary_tables(tmp_path):
    """Test migration where secondary tables (e.g., pnori2) are empty/missing."""
    db_path = tmp_path / "empty_secondary.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute(
        "CREATE TABLE pnori1 (config_id BIGINT PRIMARY KEY, received_at TIMESTAMP, "
        "original_sentence TEXT, instrument_type_name VARCHAR, instrument_type_code TINYINT, "
        "head_id VARCHAR, beam_count TINYINT, cell_count SMALLINT, blanking_distance DECIMAL, "
        "cell_size DECIMAL, coord_system_name VARCHAR, coord_system_code TINYINT, checksum VARCHAR)"
    )
    conn.execute(
        "INSERT INTO pnori1 VALUES (1, now(), 'dummy', 'dummy', 0, 'dummy', 4, 4, "
        "1.0, 1.0, 'ENU', 0, 'AB')"
    )
    # pnori2 is missing
    conn.close()

    target_path = tmp_path / "secondary_migrated.duckdb"
    # Should skip missing pnori2 without error
    stats = migrate_database(db_path, target_path)
    assert stats.get("pnori1/2->pnori12", 0) == 1


def test_migration_main_error(tmp_path):
    """Test migration main function with invalid arguments."""
    with patch.object(sys, "argv", ["migration.py", "non_existent.duckdb"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1


def test_copy_existing_tables_missing(tmp_path):
    """Test copy_existing_tables when some tables are missing."""
    from adcp_recorder.db.migration import copy_existing_tables

    db_path = tmp_path / "missing_copy.duckdb"
    conn = duckdb.connect(str(db_path))
    # No tables created
    counts = copy_existing_tables(conn)
    conn.close()
    assert counts["pnori"] == 0


def test_migrate_pnorw_fields_not_found(tmp_path):
    """Test migrate_pnorw_fields when table does not exist."""
    mock_conn = MagicMock()
    # get_old_table_exists returns False (fetchone returns [0] or None)
    mock_conn.execute.return_value = MagicMock(fetchone=lambda: [0])

    from adcp_recorder.db.migration import migrate_pnorw_fields

    count = migrate_pnorw_fields(mock_conn)
    assert count == 0
