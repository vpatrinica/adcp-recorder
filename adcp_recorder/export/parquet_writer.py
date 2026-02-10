"""Parquet writer for efficient storage of structured ADCP records."""

import logging
import os
from datetime import date, datetime
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
        self._last_flush: dict[str, datetime] = {}
        self._conn = duckdb.connect(database=":memory:")
        self._ensure_base_path()

    def _ensure_base_path(self) -> None:
        """Ensure base directory for Parquet files exists."""
        os.makedirs(self.base_path, exist_ok=True)

    def _get_partition_path(self, prefix: str, record_date: date) -> Path:
        """Get the partitioned directory path for a record type and date."""
        # Partitioning by record type and then by date
        # Format: base/prefix/date=YYYY-MM-DD/
        partition_dir = self.base_path / prefix / f"date={record_date.isoformat()}"
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
            self._last_flush[prefix] = datetime.now()

        # Add timestamp if not present
        if "received_at" not in record:
            record["received_at"] = datetime.now()

        # Add measurement_id for optimized joins if date and time are present
        if "measurement_date" in record and "measurement_time" in record:
            try:
                date_str = str(record["measurement_date"])
                time_str = str(record["measurement_time"])
                if len(date_str) == 6 and len(time_str) == 6:
                    # NMEA date is MMDDYY, we want YYMMDDHHMMSS for sorting
                    yy = date_str[4:6]
                    mm = date_str[0:2]
                    dd = date_str[2:4]
                    record["measurement_id"] = int(f"{yy}{mm}{dd}{time_str}")
            except (ValueError, TypeError):
                pass

        self._buffers[prefix].append(record)

        if len(self._buffers[prefix]) >= self.buffer_size:
            self.flush(prefix)
        else:
            # Check for stale buffers occasionally even if not full
            # We don't want to check on every single record for high-freq ones,
            # but for low-freq it's fine.
            self.flush_stale(max_age_seconds=300)  # 5 minutes default

    def flush_stale(self, max_age_seconds: int = 300) -> None:
        """Flush buffers that haven't been flushed in a while.

        Args:
            max_age_seconds: Threshold for flushing stale buffers.
        """
        now = datetime.now()
        for prefix in list(self._buffers.keys()):
            if not self._buffers[prefix]:
                continue

            last_flush = self._last_flush.get(prefix)
            if last_flush is None or (now - last_flush).total_seconds() > max_age_seconds:
                logger.info(f"Time-based flush for {prefix} ({len(self._buffers[prefix])} records)")
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
                records_by_date: dict[date, list[dict[str, Any]]] = {}
                for rec in buffer:
                    ts = rec.get("received_at")
                    date_val = ts.date() if isinstance(ts, datetime) else datetime.now().date()
                    if date_val not in records_by_date:
                        records_by_date[date_val] = []
                    records_by_date[date_val].append(rec)

                for date_val, records in records_by_date.items():
                    self._write_to_parquet(p, date_val, records)

                self._buffers[p] = []
                self._last_flush[p] = datetime.now()
            except Exception as e:
                logger.error(f"Failed to flush Parquet records for {p}: {e}")

    def _write_to_parquet(
        self, prefix: str, record_date: date, records: list[dict[str, Any]]
    ) -> None:
        """Actually write a batch of records to a Parquet file.

        Ensures maximum 1 file per day per prefix by appending to existing file if it exists.
        Also compacts legacy files ({prefix}_*.parquet) into the single daily file.
        Uses atomic write signaling: writes to a temporary .writing file first,
        then renames to the final .parquet file. This ensures readers never see
        incomplete files.
        """
        partition_dir = self._get_partition_path(prefix, record_date)

        # Filename: {prefix}.parquet (one per daily partition)
        final_filename = f"{prefix}.parquet"
        temp_filename = f"{prefix}.parquet.writing"

        final_path = partition_dir / final_filename
        temp_path = partition_dir / temp_filename

        # Detect legacy files: {prefix}_*.parquet (but not the final one)
        legacy_files = [
            f
            for f in partition_dir.glob(f"{prefix}_*.parquet")
            if f.name != final_filename and not f.name.endswith(".writing")
        ]

        # Ensure all records have record_type for consistency
        for r in records:
            if "record_type" not in r:
                r["record_type"] = prefix

        try:
            # Use polars to write Parquet directly - more efficient and no pandas dependency
            import polars as pl

            # Create dataframe for new records
            new_df = pl.from_dicts(records, infer_schema_length=10000)

            # Collect data from existing and legacy files
            dataframes = []
            if final_path.exists():
                try:
                    dataframes.append(pl.read_parquet(str(final_path)))
                except Exception as e:
                    logger.warning(f"Could not read existing Parquet {final_path}: {e}")

            for legacy_path in legacy_files:
                try:
                    dataframes.append(pl.read_parquet(str(legacy_path)))
                except Exception as e:
                    logger.warning(f"Could not read legacy Parquet {legacy_path}: {e}")

            dataframes.append(new_df)

            # Align types to handle schema conflicts (e.g., Int64 vs Float64)
            if dataframes:
                # Get common columns
                all_cols = set(new_df.columns)
                for df_existing in dataframes[:-1]:  # new_df is at the end
                    all_cols.update(df_existing.columns)

                # For all columns in new_df, align with existing dataframes if types differ
                for col in new_df.columns:
                    for df_existing in dataframes[:-1]:
                        if col in df_existing.columns:
                            existing_dtype = df_existing[col].dtype
                            if new_df[col].dtype != existing_dtype:
                                try:
                                    # If target is float-ish, promote to float
                                    if "Float" in str(existing_dtype):
                                        new_df = new_df.with_columns(pl.col(col).cast(pl.Float64))
                                    else:
                                        new_df = new_df.with_columns(
                                            pl.col(col).cast(existing_dtype)
                                        )
                                except Exception as e:
                                    logger.warning(
                                        f"Failed to align column {col} type from "
                                        f"{new_df[col].dtype} to {existing_dtype}: {e}"
                                    )
                                break
                            break

                # Update the reference in the dataframes list to use the aligned version
                dataframes[-1] = new_df

            # Use diagonal union to handle schema evolutions (new columns)
            df = pl.concat(dataframes, how="diagonal")

            # Backfill measurement_id for legacy records if missing
            if "measurement_id" in df.columns:
                # Fill nulls in measurement_id if date and time are present
                # This is a bit complex in polars expressions, so we do it if possible
                if "measurement_date" in df.columns and "measurement_time" in df.columns:
                    # Only try if we have the necessary strings
                    df = df.with_columns(
                        pl.when(pl.col("measurement_id").is_null())
                        .then(
                            # YYMMDDHHMMSS
                            (
                                pl.col("measurement_date").str.slice(4, 2)
                                + pl.col("measurement_date").str.slice(0, 2)
                                + pl.col("measurement_date").str.slice(2, 2)
                                + pl.col("measurement_time")
                            ).cast(pl.UInt64)
                        )
                        .otherwise(pl.col("measurement_id"))
                        .alias("measurement_id")
                    )

            # Write to temporary file first
            df.write_parquet(str(temp_path))

            # Atomic replace to final path (atomic on POSIX systems, replaces on Windows if exists)
            os.replace(temp_path, final_path)

            # Clean up legacy files after successful write
            for legacy_path in legacy_files:
                try:
                    legacy_path.unlink()
                except Exception as e:
                    logger.warning(f"Could not delete legacy file {legacy_path}: {e}")

            logger.debug(f"Wrote {len(records)} records (total {len(df)}) to {final_path}")
        except Exception as e:
            logger.error(f"Polars Parquet write error: {prefix}: {e}")
            # Clean up temp file if it exists
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

    def close(self) -> None:
        """Flush all buffers and close connections."""
        self.flush()
        try:
            self._conn.close()
        except Exception as e:
            logger.error(f"Error closing DuckDB connection in ParquetWriter: {e}")
