"""Tests for migration.py CLI."""

import subprocess

import duckdb


def test_migration_cli_help():
    """Test migration.py --help."""
    result = subprocess.run(
        ["python", "-m", "adcp_recorder.db.migration", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Migrate ADCP database schema" in result.stdout


def test_migration_cli_basic(tmp_path):
    """Test migration.py CLI basic run."""
    old_db = tmp_path / "old.duckdb"
    new_db = tmp_path / "new.duckdb"

    # Create old dummy DB with enough columns to satisfy the migration SELECT
    conn = duckdb.connect(str(old_db))
    conn.execute("""
        CREATE TABLE pnori1 (
            received_at TIMESTAMP,
            original_sentence TEXT,
            instrument_type_name VARCHAR,
            instrument_type_code INTEGER,
            head_id INTEGER,
            beam_count INTEGER,
            cell_count INTEGER,
            blanking_distance FLOAT,
            cell_size FLOAT,
            coord_system_name VARCHAR,
            coord_system_code INTEGER,
            checksum VARCHAR
        )
    """)
    conn.execute("""
        INSERT INTO pnori1 VALUES (
            current_timestamp, '$PNORI', 'ADCP', 0, 1, 4, 10, 0.5, 1.0, 'XYZ', 1, '00'
        )
    """)
    conn.close()

    # Run migration CLI
    result = subprocess.run(
        ["python", "-m", "adcp_recorder.db.migration", str(old_db), "-t", str(new_db)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Migration Statistics:" in result.stdout

    # Verify new DB
    conn = duckdb.connect(str(new_db))
    res = conn.execute("SELECT count(*) FROM pnori12").fetchone()
    assert res is not None
    assert res[0] == 1
    conn.close()
