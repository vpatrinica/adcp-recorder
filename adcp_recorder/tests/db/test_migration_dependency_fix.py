import duckdb
import pytest

from adcp_recorder.db.migration import migrate_database


def test_migration_dependency_with_typos(tmp_path):
    # 1. Create a database with old schema and TYPOS in pnorb_data
    db_path = tmp_path / "old_adcp.duckdb"
    conn = duckdb.connect(str(db_path))

    # Old pnorb_data with 'hmo' instead of 'hm0'
    conn.execute("""
        CREATE TABLE pnorb_data (
            record_id BIGINT PRIMARY KEY,
            received_at TIMESTAMP DEFAULT current_timestamp,
            sentence_type VARCHAR(10),
            original_sentence TEXT,
            measurement_date CHAR(6),
            measurement_time CHAR(6),
            spectrum_basis TINYINT,
            processing_method TINYINT,
            freq_low DECIMAL(4,2),
            freq_high DECIMAL(4,2),
            hmo DECIMAL(5,2),
            tm02 DECIMAL(5,2),
            tp DECIMAL(5,2),
            dirtp DECIMAL(5,2),
            sprtp DECIMAL(5,2),
            main_dir DECIMAL(5,2),
            wave_error_code CHAR(4),
            checksum CHAR(2)
        )
    """)
    # measurement_date and measurement_time are CHAR(6) in final schema,
    # but the view joins them on whatever is there.
    conn.execute("""
        INSERT INTO pnorb_data (
            record_id, hmo, tp, measurement_date, measurement_time
        ) VALUES (1, 1.23, 10.5, '230101', '120000')
    """)

    # Old pnorw_data with ALL old field names
    conn.execute("""
        CREATE TABLE pnorw_data (
            record_id BIGINT PRIMARY KEY,
            received_at TIMESTAMP DEFAULT current_timestamp,
            sentence_type VARCHAR(10),
            original_sentence TEXT,
            measurement_date CHAR(8),
            measurement_time CHAR(8),
            spectrum_basis TINYINT,
            processing_method TINYINT,
            hm0 DECIMAL(5,2),
            h3 DECIMAL(5,2),
            h10 DECIMAL(5,2),
            hmax DECIMAL(5,2),
            tm02 DECIMAL(5,2),
            tp DECIMAL(5,2),
            mean_period DECIMAL(5,2),
            peak_dir DECIMAL(6,2),
            peak_directional_spread DECIMAL(6,2),
            mean_dir DECIMAL(6,2),
            uni_index DECIMAL(5,2),
            mean_pressure DECIMAL(5,2),
            num_no_detects INTEGER,
            num_bad_detects INTEGER,
            near_surface_speed DECIMAL(5,2),
            near_surface_dir DECIMAL(6,2),
            wave_error_code CHAR(4),
            checksum CHAR(4)
        )
    """)
    # Note: migration script does SUBSTRING(measurement_date, 1, 6)
    # So '20230101' becomes '202301'.
    # To match '230101', it should probably be '230101' in both or something compatible.
    conn.execute("""
        INSERT INTO pnorw_data (
            record_id, measurement_date, measurement_time,
            mean_period, peak_dir, peak_directional_spread, mean_dir, hm0
        ) VALUES (
            1, '230101', '120000',
            5.5, 180.0, 10.0, 175.0, 1.5
        )
    """)

    # Create an old view that might cause dependency
    conn.execute("CREATE VIEW old_v AS SELECT hmo FROM pnorb_data")

    conn.close()

    # 2. Run migration in-place
    # This should NOT fail with Binder Error or Dependency Error
    stats = migrate_database(db_path, in_place=True)

    assert stats["pnorb_data (typo fix)"] == 1
    assert stats["pnorw_data (field update)"] == 1

    # 3. Verify target state
    conn = duckdb.connect(str(db_path))

    # Check pnorb_data
    cols = [row[1] for row in conn.execute("PRAGMA table_info(pnorb_data)").fetchall()]
    assert "hm0" in cols
    assert "hmo" not in cols

    # Check views
    # This view was created during migration and should be valid
    res = conn.execute("SELECT band_hm0 FROM wave_measurement_full").fetchone()
    assert res is not None
    assert float(res[0]) == pytest.approx(1.23)

    # Check pnorw_data migrated fields
    row = conn.execute("SELECT main_dir, tz FROM pnorw_data").fetchone()
    assert row is not None
    assert float(row[0]) == pytest.approx(175.0)
    assert float(row[1]) == pytest.approx(5.5)

    conn.close()
