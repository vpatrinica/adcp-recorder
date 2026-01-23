"""Bulk export ADCP data from DuckDB to Parquet."""

import logging
import os
from datetime import datetime
from pathlib import Path

import duckdb
from adcp_recorder.export.parquet_writer import ParquetWriter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BulkExporter:
    """Exports all base tables from a DuckDB database to partitioned Parquet files."""

    def __init__(self, db_path: str, output_path: str, buffer_size: int = 5000):
        """Initialize exporter.

        Args:
            db_path: Path to source DuckDB database
            output_path: Path to target directory for Parquet files
            buffer_size: Number of records to buffer before flushing
        """
        self.db_path = db_path
        self.output_path = Path(output_path)
        self.writer = ParquetWriter(self.output_path, buffer_size=buffer_size)

        # Mapping from SQL table names to Parquet prefixes (folder names)
        self.table_map = {
            "pnore_data": "PNORE",
            "pnorw_data": "PNORW",
            "pnorb_data": "PNORB",
            "pnorf_data": "PNORF",
            "pnorwd_data": "PNORWD",
            "pnora_data": "PNORA",
            "pnors_df100": "PNORS",
            "pnorc_df100": "PNORC",
            "pnors12": "PNORS12",
            "pnorc12": "PNORC12",
            "pnors34": "PNORS34",
            "pnorc34": "PNORC34",
            "pnorh": "PNORH",
            "pnori": "PNORI",
            "pnori12": "PNORI12",
            "parse_errors": "PARSE_ERRORS",
            "raw_lines": "RAW_LINES",
        }

    def export_all(self) -> dict[str, int]:
        """Export all mapped tables.

        Returns:
            Dictionary mapping table names to exported record counts.
        """
        if not os.path.exists(self.db_path):
            logger.error(f"Database not found: {self.db_path}")
            return {}

        conn = duckdb.connect(self.db_path)
        try:
            # Get list of base tables
            tables_info = conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' AND table_type = 'BASE TABLE'"
            ).fetchall()
            available_tables = [t[0] for t in tables_info]

            stats = {}
            for table in available_tables:
                if table in self.table_map:
                    prefix = self.table_map[table]
                    count = self.export_table(conn, table, prefix)
                    stats[table] = count
                else:
                    logger.info(f"Skipping unmapped table: {table}")

            return stats
        finally:
            conn.close()
            self.writer.close()

    def export_table(self, conn: duckdb.DuckDBPyConnection, table_name: str, prefix: str) -> int:
        """Export a single table.

        Args:
            conn: DuckDB connection
            table_name: Source table name
            prefix: Target Parquet prefix

        Returns:
            Number of records exported.
        """
        logger.info(f"Exporting table '{table_name}' to prefix '{prefix}'...")

        # Get row count for progress reporting
        total_rows = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        if total_rows == 0:
            logger.info(f"Table '{table_name}' is empty. Skipping.")
            return 0

        # Stream records using fetchmany
        result = conn.execute(f"SELECT * FROM {table_name}")
        col_names = [d[0] for d in result.description]

        count = 0
        while True:
            chunk = result.fetchmany(2000)
            if not chunk:
                break

            for row in chunk:
                # Convert row tuple to dict
                record = dict(zip(col_names, row))

                # Logic for measurement_id is already in ParquetWriter.write_record
                # It will use record['measurement_date'] and record['measurement_time']

                self.writer.write_record(prefix, record)
                count += 1

            if count % 10000 == 0:
                logger.info(f"  ...processed {count}/{total_rows} rows")

        self.writer.flush(prefix)
        logger.info(f"Finished exporting '{table_name}': {count} rows.")
        return count


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Bulk export ADCP DuckDB to Parquet")
    parser.add_argument(
        "--db",
        default="/workspaces/adcp-recorder/utils/adcp-data/db/adcp.duckdb",
        help="Path to source DuckDB",
    )
    parser.add_argument(
        "--out",
        default="/workspaces/adcp-recorder/utils/adcp-data/parquet",
        help="Path to output directory",
    )
    parser.add_argument("--buffer", type=int, default=10000, help="Buffer size for writing")

    args = parser.parse_args()

    exporter = BulkExporter(args.db, args.out, buffer_size=args.buffer)
    start_time = datetime.now()
    stats = exporter.export_all()
    duration = datetime.now() - start_time

    print("\nExport Summary:")
    print("-" * 30)
    for table, count in stats.items():
        print(f"{table:20} : {count:,} rows")
    print("-" * 30)
    print(f"Total time: {duration}")
    print(f"Output directory: {args.out}")


if __name__ == "__main__":
    main()
