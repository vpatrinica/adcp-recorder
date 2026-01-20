"""Database migration module for schema v0.1.x to v0.2.0.

This module provides functions to migrate databases from the old schema
(with separate tables for each data format) to the new consolidated schema.

Migration mappings:
- echo_data -> pnore_data (rename)
- pnori1, pnori2 -> pnori12 (consolidate with data_format)
- pnors_df101, pnors_df102 -> pnors12 (consolidate)
- pnors_df103, pnors_df104 -> pnors34 (consolidate)
- pnorc_df101, pnorc_df102 -> pnorc12 (consolidate)
- pnorc_df103, pnorc_df104 -> pnorc34 (consolidate)
- pnorh_df103, pnorh_df104 -> pnorh (consolidate)
- pnorw_data -> pnorw_data (field mapping update)
"""

import logging
import sys
from pathlib import Path

import duckdb

from adcp_recorder.db.schema import ALL_SCHEMA_SQL

logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Exception raised during migration."""

    pass


def get_old_table_exists(conn: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    """Check if table exists in the database."""
    try:
        res = conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [table_name],
        ).fetchone()
        return res[0] > 0 if res else False
    except Exception:
        return False


def get_table_row_count(conn: duckdb.DuckDBPyConnection, table_name: str) -> int:
    """Get row count for a table."""
    try:
        res = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return res[0] if res else 0
    except Exception:
        return 0


def migrate_echo_data_to_pnore(conn: duckdb.DuckDBPyConnection) -> int:
    """Migrate echo_data to pnore_data table."""
    if not get_old_table_exists(conn, "echo_data"):
        logger.info("echo_data table not found, skipping migration")
        return 0

    count = get_table_row_count(conn, "echo_data")
    if count == 0:
        logger.info("echo_data is empty, skipping migration")
        return 0

    logger.info(f"Migrating {count} rows from echo_data to pnore_data")

    # Insert from echo_data to pnore_data
    # Note: echo_data has sentence_type but original didn't have CHAR(6) constraints
    conn.execute("""
        INSERT INTO pnore_data (
            record_id, received_at, sentence_type, original_sentence,
            measurement_date, measurement_time, spectrum_basis,
            start_frequency, step_frequency, num_frequencies, energy_densities, checksum
        )
        SELECT
            record_id, received_at, 'PNORE', original_sentence,
            SUBSTRING(measurement_date, 1, 6), SUBSTRING(measurement_time, 1, 6),
            spectrum_basis, start_frequency, step_frequency,
            num_frequencies, energy_densities, SUBSTRING(checksum, 1, 2)
        FROM echo_data
    """)

    return count


def migrate_pnori_consolidated(conn: duckdb.DuckDBPyConnection) -> int:
    """Migrate pnori1 and pnori2 to pnori12."""
    total = 0

    for old_table, data_format in [("pnori1", 101), ("pnori2", 102)]:
        if not get_old_table_exists(conn, old_table):
            logger.info(f"{old_table} table not found, skipping")
            continue

        count = get_table_row_count(conn, old_table)
        if count == 0:
            logger.info(f"{old_table} is empty, skipping")
            continue

        logger.info(f"Migrating {count} rows from {old_table} to pnori12")

        conn.execute(f"""
            INSERT INTO pnori12 (
                config_id, received_at, data_format, original_sentence,
                instrument_type_name, instrument_type_code, head_id,
                beam_count, cell_count, blanking_distance, cell_size,
                coord_system_name, coord_system_code, checksum
            )
            SELECT
                nextval('pnori12_seq'), received_at, {data_format}, original_sentence,
                instrument_type_name, instrument_type_code, head_id,
                beam_count, cell_count, blanking_distance, cell_size,
                coord_system_name, coord_system_code, SUBSTRING(checksum, 1, 2)
            FROM {old_table}
        """)

        total += count

    return total


def migrate_pnors_df101_102(conn: duckdb.DuckDBPyConnection) -> int:
    """Migrate pnors_df101 and pnors_df102 to pnors12."""
    total = 0

    for old_table, data_format in [("pnors_df101", 101), ("pnors_df102", 102)]:
        if not get_old_table_exists(conn, old_table):
            logger.info(f"{old_table} table not found, skipping")
            continue

        count = get_table_row_count(conn, old_table)
        if count == 0:
            logger.info(f"{old_table} is empty, skipping")
            continue

        logger.info(f"Migrating {count} rows from {old_table} to pnors12")

        conn.execute(f"""
            INSERT INTO pnors12 (
                record_id, received_at, data_format, original_sentence,
                measurement_date, measurement_time, error_code, status_code,
                battery, sound_speed, heading_std_dev, heading,
                pitch, pitch_std_dev, roll, roll_std_dev,
                pressure, pressure_std_dev, temperature, checksum
            )
            SELECT
                nextval('pnors12_seq'), received_at, {data_format}, original_sentence,
                SUBSTRING(measurement_date, 1, 6), SUBSTRING(measurement_time, 1, 6),
                CAST(error_code AS INTEGER), status_code,
                battery, sound_speed,
                COALESCE(heading_std_dev, 0.0), heading,
                pitch, COALESCE(pitch_std_dev, 0.0),
                roll, COALESCE(roll_std_dev, 0.0),
                pressure, COALESCE(pressure_std_dev, 0.0),
                temperature, SUBSTRING(checksum, 1, 2)
            FROM {old_table}
        """)

        total += count

    return total


def migrate_pnors_df103_104(conn: duckdb.DuckDBPyConnection) -> int:
    """Migrate pnors_df103 and pnors_df104 to pnors34 (without extra fields)."""
    total = 0

    for old_table, data_format in [("pnors_df103", 103), ("pnors_df104", 104)]:
        if not get_old_table_exists(conn, old_table):
            logger.info(f"{old_table} table not found, skipping")
            continue

        count = get_table_row_count(conn, old_table)
        if count == 0:
            logger.info(f"{old_table} is empty, skipping")
            continue

        logger.info(f"Migrating {count} rows from {old_table} to pnors34")

        conn.execute(f"""
            INSERT INTO pnors34 (
                record_id, received_at, data_format, original_sentence,
                measurement_date, measurement_time, battery, sound_speed,
                heading, pitch, roll, pressure, temperature, checksum
            )
            SELECT
                nextval('pnors34_seq'), received_at, {data_format}, original_sentence,
                SUBSTRING(measurement_date, 1, 6), SUBSTRING(measurement_time, 1, 6),
                battery, sound_speed, heading, pitch, roll, pressure, temperature,
                SUBSTRING(checksum, 1, 2)
            FROM {old_table}
        """)

        total += count

    return total


def migrate_pnorc_df101_102(conn: duckdb.DuckDBPyConnection) -> int:
    """Migrate pnorc_df101 and pnorc_df102 to pnorc12."""
    total = 0

    for old_table, data_format in [("pnorc_df101", 101), ("pnorc_df102", 102)]:
        if not get_old_table_exists(conn, old_table):
            logger.info(f"{old_table} table not found, skipping")
            continue

        count = get_table_row_count(conn, old_table)
        if count == 0:
            logger.info(f"{old_table} is empty, skipping")
            continue

        logger.info(f"Migrating {count} rows from {old_table} to pnorc12")

        conn.execute(f"""
            INSERT INTO pnorc12 (
                record_id, received_at, data_format, original_sentence,
                measurement_date, measurement_time, cell_index, cell_distance,
                vel1, vel2, vel3, vel4, amp1, amp2, amp3, amp4,
                corr1, corr2, corr3, corr4, checksum
            )
            SELECT
                nextval('pnorc12_seq'), received_at, {data_format}, original_sentence,
                SUBSTRING(measurement_date, 1, 6), SUBSTRING(measurement_time, 1, 6),
                cell_index, COALESCE(cell_distance, 0.0),
                vel1, vel2, vel3, vel4,
                COALESCE(amp1, 0.0), COALESCE(amp2, 0.0), COALESCE(amp3, 0.0), COALESCE(amp4, 0.0),
                COALESCE(corr1, 0), COALESCE(corr2, 0), COALESCE(corr3, 0), COALESCE(corr4, 0),
                SUBSTRING(checksum, 1, 2)
            FROM {old_table}
        """)

        total += count

    return total


def migrate_pnorc_df103_104(conn: duckdb.DuckDBPyConnection) -> int:
    """Migrate pnorc_df103 and pnorc_df104 to pnorc34 (minimal fields)."""
    total = 0

    for old_table, data_format in [("pnorc_df103", 103), ("pnorc_df104", 104)]:
        if not get_old_table_exists(conn, old_table):
            logger.info(f"{old_table} table not found, skipping")
            continue

        count = get_table_row_count(conn, old_table)
        if count == 0:
            logger.info(f"{old_table} is empty, skipping")
            continue

        logger.info(f"Migrating {count} rows from {old_table} to pnorc34")

        conn.execute(f"""
            INSERT INTO pnorc34 (
                record_id, received_at, data_format, original_sentence,
                measurement_date, measurement_time, cell_index, cell_distance,
                speed, direction, checksum
            )
            SELECT
                nextval('pnorc34_seq'), received_at, {data_format}, original_sentence,
                SUBSTRING(measurement_date, 1, 6), SUBSTRING(measurement_time, 1, 6),
                cell_index, COALESCE(cell_distance, 0.0),
                COALESCE(speed, 0.0), COALESCE(direction, 0.0),
                SUBSTRING(checksum, 1, 2)
            FROM {old_table}
        """)

        total += count

    return total


def migrate_pnorh_consolidated(conn: duckdb.DuckDBPyConnection) -> int:
    """Migrate pnorh_df103 and pnorh_df104 to pnorh."""
    total = 0

    for old_table, data_format in [("pnorh_df103", 103), ("pnorh_df104", 104)]:
        if not get_old_table_exists(conn, old_table):
            logger.info(f"{old_table} table not found, skipping")
            continue

        count = get_table_row_count(conn, old_table)
        if count == 0:
            logger.info(f"{old_table} is empty, skipping")
            continue

        logger.info(f"Migrating {count} rows from {old_table} to pnorh")

        conn.execute(f"""
            INSERT INTO pnorh (
                record_id, received_at, data_format, original_sentence,
                measurement_date, measurement_time, error_code, status_code, checksum
            )
            SELECT
                nextval('pnorh_seq'), received_at, {data_format}, original_sentence,
                SUBSTRING(measurement_date, 1, 6), SUBSTRING(measurement_time, 1, 6),
                COALESCE(error_code, 0), status_code, SUBSTRING(checksum, 1, 2)
            FROM {old_table}
        """)

        total += count

    return total


def migrate_pnorw_fields(conn: duckdb.DuckDBPyConnection) -> int:
    """Migrate pnorw_data with updated field names.

    Old schema had different field names, new schema uses standardized names.
    """
    if not get_old_table_exists(conn, "pnorw_data"):
        logger.info("pnorw_data table not found, skipping migration")
        return 0

    # Check if old schema has different field names (mean_dir vs dir_tp, etc.)
    try:
        result = conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'pnorw_data' AND column_name = 'mean_dir'"
        ).fetchone()
        old_schema = result is not None
    except Exception:
        old_schema = False

    if not old_schema:
        # Already in new schema
        logger.info("pnorw_data already in new schema, skipping migration")
        return 0

    count = get_table_row_count(conn, "pnorw_data")
    if count == 0:
        logger.info("pnorw_data is empty, skipping migration")
        return 0

    logger.info(f"Migrating {count} rows in pnorw_data (updating field names)")

    # Create a new table with new schema, migrate data, swap
    conn.execute("""
        CREATE TABLE pnorw_data_new AS
        SELECT
            record_id, received_at, sentence_type, original_sentence,
            SUBSTRING(measurement_date, 1, 6) AS measurement_date,
            SUBSTRING(measurement_time, 1, 6) AS measurement_time,
            spectrum_basis, processing_method,
            CAST(hm0 AS DECIMAL(5,2)) AS hm0,
            CAST(NULL AS DECIMAL(5,2)) AS h3,
            CAST(NULL AS DECIMAL(5,2)) AS h10,
            CAST(hmax AS DECIMAL(5,2)) AS hmax,
            CAST(tm02 AS DECIMAL(5,2)) AS tm02,
            CAST(tp AS DECIMAL(5,2)) AS tp,
            CAST(mean_period AS DECIMAL(5,2)) AS tz,
            CAST(peak_dir AS DECIMAL(6,2)) AS dir_tp,
            CAST(peak_directional_spread AS DECIMAL(6,2)) AS spr_tp,
            CAST(mean_dir AS DECIMAL(6,2)) AS main_dir,
            CAST(NULL AS DECIMAL(5,2)) AS uni_index,
            CAST(NULL AS DECIMAL(5,2)) AS mean_pressure,
            CAST(NULL AS INTEGER) AS num_no_detects,
            CAST(NULL AS INTEGER) AS num_bad_detects,
            CAST(NULL AS DECIMAL(5,2)) AS near_surface_speed,
            CAST(NULL AS DECIMAL(6,2)) AS near_surface_dir,
            wave_error_code,
            SUBSTRING(checksum, 1, 2) AS checksum
        FROM pnorw_data
    """)

    # Drop old table, rename new
    conn.execute("DROP TABLE pnorw_data")
    conn.execute("ALTER TABLE pnorw_data_new RENAME TO pnorw_data")

    return count


def copy_existing_tables(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Copy data from tables that don't need structural changes.

    These tables have the same schema in old and new versions.
    """
    tables_to_copy = {
        "pnori": "pnori",  # Original PNORI (DF100) - same schema
        "pnors_df100": "pnors_df100",  # Same schema after removing extra fields
        "pnorc_df100": "pnorc_df100",  # Same schema
        "pnorb_data": "pnorb_data",
        "pnorf_data": "pnorf_data",
        "pnorwd_data": "pnorwd_data",
        "pnora_data": "pnora_data",
        "raw_lines": "raw_lines",
        "parse_errors": "parse_errors",
    }

    counts = {}

    for old_name, new_name in tables_to_copy.items():
        if not get_old_table_exists(conn, old_name):
            logger.info(f"{old_name} table not found, skipping copy")
            counts[old_name] = 0
            continue

        count = get_table_row_count(conn, old_name)
        counts[old_name] = count
        logger.info(f"Table {old_name} has {count} rows (will be preserved)")

    return counts


def create_new_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all new schema tables and sequences."""
    logger.info("Creating new schema tables...")

    for sql in ALL_SCHEMA_SQL:
        try:
            conn.execute(sql)
        except Exception as e:
            # Table may already exist
            if "already exists" not in str(e).lower():
                logger.warning(f"Schema creation warning: {e}")


def migrate_database(
    source_path: str | Path,
    target_path: str | Path | None = None,
    *,
    in_place: bool = False,
) -> dict[str, int]:
    """Perform full database migration from v0.1.x to v0.2.0 schema.

    Args:
        source_path: Path to the source database
        target_path: Path for the migrated database (optional, only if not in_place)
        in_place: If True, modify the source database directly

    Returns:
        Dictionary with migration statistics (table: rows migrated)
    """
    source_path = Path(source_path)

    if not source_path.exists():
        raise MigrationError(f"Source database not found: {source_path}")

    if in_place:
        target_path = source_path
        logger.info(f"Migrating {source_path} in-place")
    else:
        if target_path is None:
            target_path = source_path.parent / f"{source_path.stem}_migrated.duckdb"
        target_path = Path(target_path)

        # Copy source to target
        import shutil

        logger.info(f"Copying {source_path} to {target_path}")
        shutil.copy2(source_path, target_path)

    # Connect to target database
    conn = duckdb.connect(str(target_path))

    stats: dict[str, int] = {}

    try:
        # Create new schema tables
        create_new_schema(conn)

        # Migrate data
        stats["echo_data->pnore_data"] = migrate_echo_data_to_pnore(conn)
        stats["pnori1/2->pnori12"] = migrate_pnori_consolidated(conn)
        stats["pnors_df101/102->pnors12"] = migrate_pnors_df101_102(conn)
        stats["pnors_df103/104->pnors34"] = migrate_pnors_df103_104(conn)
        stats["pnorc_df101/102->pnorc12"] = migrate_pnorc_df101_102(conn)
        stats["pnorc_df103/104->pnorc34"] = migrate_pnorc_df103_104(conn)
        stats["pnorh_df103/104->pnorh"] = migrate_pnorh_consolidated(conn)
        stats["pnorw_data (field update)"] = migrate_pnorw_fields(conn)

        # Report existing table counts
        existing_counts = copy_existing_tables(conn)
        stats.update({f"{k} (preserved)": v for k, v in existing_counts.items()})

        # Drop old tables if migration was successful
        old_tables_to_drop = [
            "echo_data",
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

        for table in old_tables_to_drop:
            if get_old_table_exists(conn, table):
                count = get_table_row_count(conn, table)
                logger.info(f"Dropping old table: {table} ({count} rows migrated)")
                conn.execute(f"DROP TABLE IF EXISTS {table}")

        # Re-run schema creation to ensure views are created/updated
        # (views depend on tables like pnorw_data which might have been updated during migration)
        logger.info("Re-applying schema to update views...")
        create_new_schema(conn)

        # Checkpoint to persist changes
        conn.execute("CHECKPOINT")

        logger.info("Migration completed successfully!")
        logger.info(f"Migrated database saved to: {target_path}")

        return stats

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise MigrationError(f"Migration failed: {e}") from e

    finally:
        conn.close()


def verify_migration(db_path: str | Path) -> dict[str, int]:
    """Verify that migration was successful by checking table row counts.

    Args:
        db_path: Path to the migrated database

    Returns:
        Dictionary with table names and row counts
    """
    conn = duckdb.connect(str(db_path), read_only=True)

    tables = [
        "pnore_data",
        "pnori",
        "pnori12",
        "pnors_df100",
        "pnors12",
        "pnors34",
        "pnorc_df100",
        "pnorc12",
        "pnorc34",
        "pnorh",
        "pnorw_data",
        "pnorb_data",
        "pnorf_data",
        "pnorwd_data",
        "pnora_data",
        "raw_lines",
        "parse_errors",
    ]

    counts = {}
    for table in tables:
        count = get_table_row_count(conn, table)
        counts[table] = count

    conn.close()
    return counts


def main():
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    parser = argparse.ArgumentParser(description="Migrate ADCP database schema")
    parser.add_argument("source", help="Source database path")
    parser.add_argument("--target", "-t", help="Target database path (optional)")
    parser.add_argument(
        "--in-place", "-i", action="store_true", help="Modify source database directly"
    )
    parser.add_argument(
        "--verify", "-v", action="store_true", help="Verify migration after completion"
    )

    args = parser.parse_args()

    try:
        stats = migrate_database(args.source, args.target, in_place=args.in_place)

        print("\nMigration Statistics:")
        print("-" * 50)
        for table, count in stats.items():
            print(f"  {table}: {count} rows")

        if args.verify:
            source = Path(args.source)
            if args.in_place:
                target = source
            elif args.target:
                target = Path(args.target)
            else:
                target = source.parent / f"{source.stem}_migrated.duckdb"
            print("\nVerification:")
            print("-" * 50)
            verification = verify_migration(target)
            for table, count in verification.items():
                print(f"  {table}: {count} rows")

    except MigrationError as e:
        print(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
