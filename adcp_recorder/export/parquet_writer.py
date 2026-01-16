"""Parquet writer for efficient storage of structured ADCP records."""

import contextlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)


class ParquetWriter:
    """Writes structured records to Parquet files with daily partitioning.

    Uses DuckDB as the engine for efficient Parquet generation.
    """

    def __init__(self, base_path: str, buffer_size: int = 100):
        """Initialize Parquet writer.

        Args:
            base_path: Base directory for the "DuckLake" storage
            buffer_size: Number of records to buffer before flushing to disk

        """
        self.base_path = Path(base_path) / "parquet"
        self.buffer_size = buffer_size
        self._buffers: dict[str, list[dict[str, Any]]] = {}
        self._conn = duckdb.connect(database=":memory:")
        self._ensure_base_path()

    def _ensure_base_path(self) -> None:
        """Ensure base directory for Parquet files exists."""
        os.makedirs(self.base_path, exist_ok=True)

    def _get_partition_path(self, prefix: str, date: datetime.date) -> Path:
        """Get the partitioned directory path for a record type and date."""
        # Partitioning by record type and then by date
        # Format: base/prefix/date=YYYY-MM-DD/
        partition_dir = self.base_path / prefix / f"date={date.isoformat()}"
        os.makedirs(partition_dir, exist_ok=True)
        return partition_dir

    def write_record(self, prefix: str, record: dict[str, Any]) -> None:
        """Buffer a record for writing.

        Args:
            prefix: Record type prefix (e.g., 'PNORS', 'PNORC')
            record: Dictionary of data to store

        """
        if prefix not in self._buffers:
            self._buffers[prefix] = []

        # Add timestamp if not present
        if "recorded_at" not in record:
            record["recorded_at"] = datetime.now()

        self._buffers[prefix].append(record)

        if len(self._buffers[prefix]) >= self.buffer_size:
            self.flush(prefix)

    def flush(self, prefix: str | None = None) -> None:
        """Flush buffered records to Parquet files.

        Args:
            prefix: If specified, only flush that prefix. Otherwise flush all.

        """
        prefixes = [prefix] if prefix else list(self._buffers.keys())

        for p in prefixes:
            buffer = self._buffers.get(p)
            if not buffer:
                continue

            try:
                # Group by date for partitioning
                records_by_date: dict[datetime.date, list[dict[str, Any]]] = {}
                for rec in buffer:
                    ts = rec.get("recorded_at")
                    date = ts.date() if isinstance(ts, datetime) else datetime.now().date()
                    if date not in records_by_date:
                        records_by_date[date] = []
                    records_by_date[date].append(rec)

                for date, records in records_by_date.items():
                    self._write_to_parquet(p, date, records)

                self._buffers[p] = []
            except Exception as e:
                logger.error(f"Failed to flush Parquet records for {p}: {e}")

    def _write_to_parquet(
        self, prefix: str, date: datetime.date, records: list[dict[str, Any]]
    ) -> None:
        """Actually write a batch of records to a Parquet file."""
        partition_dir = self._get_partition_path(prefix, date)

        # Filename: {prefix}_{timestamp}.parquet
        filename = f"{prefix}_{datetime.now().strftime('%H%M%S_%f')}.parquet"
        file_path = partition_dir / filename

        # Ensure all records have record_type for consistency
        for r in records:
            if "record_type" not in r:
                r["record_type"] = prefix

        try:
            # Use polars to write Parquet directly - more efficient and no pandas dependency
            import polars as pl

            df = pl.DataFrame(records)
            df.write_parquet(str(file_path))
            logger.debug(f"Wrote {len(records)} records to {file_path}")
        except Exception as e:
            logger.error(f"Polars Parquet write error: {prefix}: {e}")
            raise

    def close(self) -> None:
        """Flush all buffers and close connections."""
        self.flush()
        with contextlib.suppress(Exception):
            self._conn.close()
