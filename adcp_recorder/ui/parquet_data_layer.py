"""Parquet-based data access layer for dashboard visualizations.

Provides in-memory DuckDB queries over Parquet files with robust
single-writer/multi-reader support using atomic file signaling.
"""

import logging
import re
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)


class WritingFileStatus(str, Enum):
    """Status of a stale .writing file check."""

    WAITING_FIRST_RETRY = "waiting_first_retry"  # Will retry in 15s
    WAITING_SECOND_RETRY = "waiting_second_retry"  # Will retry in 30s
    FAULT_DETECTED = "fault_detected"  # Writer may be stuck
    COMPLETED = "completed"  # File is now complete


@dataclass
class StaleWritingFile:
    """Tracks a file stuck in .writing state."""

    path: Path
    first_seen: datetime
    retry_count: int = 0
    status: WritingFileStatus = WritingFileStatus.WAITING_FIRST_RETRY


class StaleWritingMonitor:
    """Monitors .writing files and retries with progressive delays.

    If a file remains in .writing state after retry attempts,
    notifies via callback about potential writer fault.

    Retry schedule:
    - First retry: 15 seconds after detection
    - Second retry: 30 seconds after first retry
    - After second retry fails: notify of potential fault
    """

    FIRST_RETRY_DELAY = 15.0  # seconds
    SECOND_RETRY_DELAY = 30.0  # seconds

    def __init__(
        self,
        on_fault_detected: Callable[[Path, str], None] | None = None,
        on_file_completed: Callable[[Path], None] | None = None,
    ) -> None:
        """Initialize the stale writing monitor.

        Args:
            on_fault_detected: Callback when writer fault is detected.
                               Receives (file_path, message).
            on_file_completed: Callback when a stale file completes.
                               Receives (file_path).

        """
        self._tracked_files: dict[Path, StaleWritingFile] = {}
        self._lock = threading.Lock()
        self._on_fault_detected = on_fault_detected
        self._on_file_completed = on_file_completed

    def track_writing_file(self, writing_path: Path) -> None:
        """Start tracking a .writing file.

        Args:
            writing_path: Path to the .writing file

        """
        with self._lock:
            if writing_path not in self._tracked_files:
                self._tracked_files[writing_path] = StaleWritingFile(
                    path=writing_path,
                    first_seen=datetime.now(),
                )
                logger.debug(f"Started tracking stale writing file: {writing_path}")

    def check_and_retry(self, writing_path: Path) -> WritingFileStatus:
        """Check if a .writing file is now complete, applying retry logic.

        Args:
            writing_path: Path to the .writing file

        Returns:
            Current status of the file

        """
        # First check if the corresponding .parquet file exists (write completed)
        final_path = Path(str(writing_path).replace(".parquet.writing", ".parquet"))
        if final_path.exists():
            self._complete_file(writing_path)
            return WritingFileStatus.COMPLETED

        # Check if .writing file was removed (write completed or cancelled)
        if not writing_path.exists():
            self._complete_file(writing_path)
            return WritingFileStatus.COMPLETED

        with self._lock:
            if writing_path not in self._tracked_files:
                self.track_writing_file(writing_path)

            tracked = self._tracked_files[writing_path]
            now = datetime.now()
            elapsed = (now - tracked.first_seen).total_seconds()

            if tracked.retry_count == 0:
                # Check if first retry delay has passed
                if elapsed >= self.FIRST_RETRY_DELAY:
                    tracked.retry_count = 1
                    tracked.status = WritingFileStatus.WAITING_SECOND_RETRY
                    logger.info(f"First retry for stale writing file (15s elapsed): {writing_path}")
                return tracked.status

            elif tracked.retry_count == 1:
                # Check if second retry delay has passed
                if elapsed >= self.FIRST_RETRY_DELAY + self.SECOND_RETRY_DELAY:
                    tracked.retry_count = 2
                    tracked.status = WritingFileStatus.FAULT_DETECTED
                    logger.warning(f"Writer fault detected - file stuck for 45s+: {writing_path}")
                    self._notify_fault(writing_path)
                return tracked.status

            else:
                # Already notified
                return WritingFileStatus.FAULT_DETECTED

    def _complete_file(self, writing_path: Path) -> None:
        """Mark a file as completed and notify."""
        with self._lock:
            if writing_path in self._tracked_files:
                del self._tracked_files[writing_path]
                logger.debug(f"Writing file completed: {writing_path}")

        if self._on_file_completed:
            try:
                self._on_file_completed(writing_path)
            except Exception as e:
                logger.error(f"Error in file_completed callback: {e}")

    def _notify_fault(self, writing_path: Path) -> None:
        """Notify about a potential writer fault."""
        message = (
            f"File '{writing_path.name}' has been in .writing state for over 45 seconds. "
            f"The writer process may be stuck or crashed. "
            f"Check the writer service status and restart if needed."
        )

        logger.error(message)

        if self._on_fault_detected:
            try:
                self._on_fault_detected(writing_path, message)
            except Exception as e:
                logger.error(f"Error in fault_detected callback: {e}")

    def get_stale_files(self) -> list[StaleWritingFile]:
        """Get list of currently tracked stale files."""
        with self._lock:
            return list(self._tracked_files.values())

    def get_faulted_files(self) -> list[Path]:
        """Get list of files with detected faults."""
        with self._lock:
            return [
                f.path
                for f in self._tracked_files.values()
                if f.status == WritingFileStatus.FAULT_DETECTED
            ]

    def clear(self) -> None:
        """Clear all tracked files."""
        with self._lock:
            self._tracked_files.clear()


@dataclass
class ParquetFileInfo:
    """Metadata for a single Parquet file."""

    path: Path
    record_type: str
    file_date: date
    size_bytes: int
    modified_at: datetime

    @property
    def is_complete(self) -> bool:
        """Check if file is complete (not being written)."""
        # Files with .writing extension are incomplete
        return not str(self.path).endswith(".writing")


@dataclass
class ParquetDirectory:
    """Represents a discovered Parquet data directory structure."""

    base_path: Path
    record_types: dict[str, dict[date, list[ParquetFileInfo]]] = field(default_factory=dict)
    last_scan: datetime | None = None

    def get_all_dates(self) -> list[date]:
        """Get all unique dates across all record types."""
        dates_set: set[date] = set()
        for type_data in self.record_types.values():
            dates_set.update(type_data.keys())
        return sorted(dates_set, reverse=True)

    def get_files_for_selection(
        self,
        record_types: list[str] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Path]:
        """Get file paths matching the selection criteria."""
        files: list[Path] = []

        types_to_check = record_types or list(self.record_types.keys())

        for rec_type in types_to_check:
            if rec_type not in self.record_types:
                continue

            for file_date, file_list in self.record_types[rec_type].items():
                # Apply date filters
                if start_date and file_date < start_date:
                    continue
                if end_date and file_date > end_date:
                    continue

                # Only include complete files
                for file_info in file_list:
                    if file_info.is_complete:
                        files.append(file_info.path)

        return files


class ParquetFileDiscovery:
    """Discovers and caches Parquet file structure in a directory."""

    # Pattern for date partition directories: date=YYYY-MM-DD
    DATE_PARTITION_PATTERN = re.compile(r"date=(\d{4}-\d{2}-\d{2})")

    def __init__(
        self,
        base_path: str | Path,
        stale_monitor: StaleWritingMonitor | None = None,
    ) -> None:
        """Initialize file discovery.

        Args:
            base_path: Base directory containing Parquet files.
                       Expected structure: base_path/parquet/RECORD_TYPE/date=YYYY-MM-DD/*.parquet
            stale_monitor: Optional monitor for tracking stale .writing files

        """
        self.base_path = Path(base_path)
        self._cache: ParquetDirectory | None = None
        self._cache_ttl_seconds = 5.0  # Re-scan at most every 5 seconds
        self._stale_monitor = stale_monitor
        self._writing_files: list[Path] = []

    def set_base_path(self, base_path: str | Path) -> None:
        """Change the base path and invalidate cache."""
        self.base_path = Path(base_path)
        self._cache = None
        self._writing_files = []

    def scan(self, force: bool = False) -> ParquetDirectory:
        """Scan directory for Parquet files.

        Args:
            force: If True, bypass cache and always rescan

        Returns:
            ParquetDirectory with discovered file structure

        """
        now = datetime.now()

        # Return cache if valid
        if not force and self._cache is not None:
            if self._cache.last_scan:
                age = (now - self._cache.last_scan).total_seconds()
                if age < self._cache_ttl_seconds:
                    return self._cache

        result = ParquetDirectory(base_path=self.base_path, last_scan=now)
        self._writing_files = []

        # Look for parquet subdirectory
        parquet_dir = self.base_path / "parquet"
        if not parquet_dir.exists():
            # Try base_path directly
            parquet_dir = self.base_path

        if not parquet_dir.exists():
            logger.warning(f"Parquet directory does not exist: {parquet_dir}")
            self._cache = result
            return result

        # Scan record type directories
        try:
            for record_type_dir in parquet_dir.iterdir():
                if not record_type_dir.is_dir():
                    continue

                record_type = record_type_dir.name.upper()
                result.record_types[record_type] = {}

                # Scan date partition directories
                for date_dir in record_type_dir.iterdir():
                    if not date_dir.is_dir():
                        continue

                    # Parse date from directory name
                    match = self.DATE_PARTITION_PATTERN.match(date_dir.name)
                    if not match:
                        continue

                    try:
                        file_date = date.fromisoformat(match.group(1))
                    except ValueError:
                        continue

                    if file_date not in result.record_types[record_type]:
                        result.record_types[record_type][file_date] = []

                    # Scan Parquet files (including .writing files for tracking)
                    for parquet_file in date_dir.glob("*.parquet*"):
                        # Track .writing files for stale detection
                        if str(parquet_file).endswith(".writing"):
                            self._writing_files.append(parquet_file)
                            if self._stale_monitor:
                                self._stale_monitor.track_writing_file(parquet_file)
                            continue

                        try:
                            stat = parquet_file.stat()
                            file_info = ParquetFileInfo(
                                path=parquet_file,
                                record_type=record_type,
                                file_date=file_date,
                                size_bytes=stat.st_size,
                                modified_at=datetime.fromtimestamp(stat.st_mtime),
                            )
                            result.record_types[record_type][file_date].append(file_info)
                        except OSError as e:
                            logger.warning(f"Failed to stat file {parquet_file}: {e}")

        except OSError as e:
            logger.error(f"Failed to scan directory {parquet_dir}: {e}")

        self._cache = result
        return result

    def check_stale_files(self) -> list[WritingFileStatus]:
        """Check status of all tracked .writing files.

        Applies retry logic and returns current status of each file.

        Returns:
            List of statuses for tracked .writing files

        """
        if not self._stale_monitor:
            return []

        statuses = []
        for writing_path in list(self._writing_files):
            status = self._stale_monitor.check_and_retry(writing_path)
            statuses.append(status)

            # Remove from list if completed
            if status == WritingFileStatus.COMPLETED:
                self._writing_files.remove(writing_path)

        return statuses

    def get_writing_files(self) -> list[Path]:
        """Get list of currently tracked .writing files."""
        return self._writing_files.copy()

    def get_faulted_files(self) -> list[Path]:
        """Get list of files with detected writer faults."""
        if not self._stale_monitor:
            return []
        return self._stale_monitor.get_faulted_files()

    def invalidate_cache(self) -> None:
        """Force cache invalidation."""
        self._cache = None


class ParquetDataLayer:
    """Data access layer for querying Parquet files via in-memory DuckDB.

    Provides the same query interface as DataLayer but reads from Parquet
    files instead of a persistent DuckDB database.
    """

    def __init__(
        self,
        base_path: str | Path | None = None,
        on_writer_fault: Callable[[Path, str], None] | None = None,
    ) -> None:
        """Initialize Parquet data layer.

        Args:
            base_path: Optional base path for Parquet files.
                       Can be set later via set_data_directory().
            on_writer_fault: Optional callback when writer fault is detected.
                             Receives (file_path, message).

        """
        self._conn = duckdb.connect(database=":memory:")
        self._discovery: ParquetFileDiscovery | None = None
        self._loaded_views: set[str] = set()
        self._stale_monitor = StaleWritingMonitor(on_fault_detected=on_writer_fault)
        self._on_writer_fault = on_writer_fault

        if base_path:
            self.set_data_directory(base_path)

    def set_data_directory(self, base_path: str | Path) -> None:
        """Set or change the data directory.

        Args:
            base_path: Path to directory containing Parquet files

        """
        self._discovery = ParquetFileDiscovery(base_path, stale_monitor=self._stale_monitor)
        self._clear_views()

    def _clear_views(self) -> None:
        """Drop all created views."""
        for view_name in list(self._loaded_views):
            try:
                self._conn.execute(f"DROP VIEW IF EXISTS {view_name}")
            except Exception:
                pass
        self._loaded_views.clear()

    def get_file_structure(self) -> ParquetDirectory | None:
        """Get the current file structure.

        Returns:
            ParquetDirectory or None if no directory is set

        """
        if not self._discovery:
            return None
        return self._discovery.scan()

    def get_available_record_types(self) -> list[str]:
        """Get list of available record types."""
        structure = self.get_file_structure()
        if not structure:
            return []
        return sorted(structure.record_types.keys())

    def get_available_dates(self, record_type: str | None = None) -> list[date]:
        """Get available dates, optionally filtered by record type."""
        structure = self.get_file_structure()
        if not structure:
            return []

        if record_type and record_type in structure.record_types:
            return sorted(structure.record_types[record_type].keys(), reverse=True)

        return structure.get_all_dates()

    def load_data(
        self,
        record_types: list[str] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, int]:
        """Load Parquet files into DuckDB views.

        Args:
            record_types: List of record types to load (None = all)
            start_date: Start date filter (None = no filter)
            end_date: End date filter (None = no filter)

        Returns:
            Dict mapping view names to record counts

        """
        self._clear_views()

        structure = self.get_file_structure()
        if not structure:
            return {}

        result: dict[str, int] = {}
        types_to_load = record_types or list(structure.record_types.keys())

        for rec_type in types_to_load:
            if rec_type not in structure.record_types:
                continue

            files = structure.get_files_for_selection(
                record_types=[rec_type],
                start_date=start_date,
                end_date=end_date,
            )

            if not files:
                continue

            view_name = f"pq_{rec_type.lower()}"
            file_paths = [str(f) for f in files]

            try:
                # Create view over Parquet files
                files_list = ", ".join(f"'{p}'" for p in file_paths)
                self._conn.execute(
                    f"CREATE OR REPLACE VIEW {view_name} AS "
                    f"SELECT * FROM read_parquet([{files_list}])"
                )
                self._loaded_views.add(view_name)

                # Get record count
                count_result = self._conn.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()
                result[view_name] = count_result[0] if count_result else 0

            except Exception as e:
                logger.error(f"Failed to create view {view_name}: {e}")

        return result

    def get_loaded_views(self) -> list[str]:
        """Get list of currently loaded view names."""
        return sorted(self._loaded_views)

    def query(
        self,
        view_name: str,
        columns: list[str] | None = None,
        limit: int = 100,
        order_by: str | None = None,
        order_desc: bool = True,
    ) -> list[dict[str, Any]]:
        """Query data from a loaded view.

        Args:
            view_name: Name of the view to query
            columns: Columns to select (None = all)
            limit: Maximum rows to return
            order_by: Column to order by (None = no ordering)
            order_desc: If True, order descending

        Returns:
            List of row dictionaries

        """
        if view_name not in self._loaded_views:
            raise ValueError(f"View not loaded: {view_name}")

        col_str = ", ".join(columns) if columns else "*"
        query = f"SELECT {col_str} FROM {view_name}"

        if order_by:
            direction = "DESC" if order_desc else "ASC"
            query += f" ORDER BY {order_by} {direction}"

        query += f" LIMIT {limit}"

        result = self._conn.execute(query).fetchall()
        col_names = [d[0] for d in self._conn.description]
        return [dict(zip(col_names, row, strict=False)) for row in result]

    def query_time_series(
        self,
        view_name: str,
        x_column: str,
        y_columns: list[str],
        limit: int = 10000,
    ) -> dict[str, Any]:
        """Query time series data for plotting.

        Args:
            view_name: View to query
            x_column: Column for X axis (typically timestamp)
            y_columns: Columns for Y axis values
            limit: Maximum records

        Returns:
            Dict with 'x' and 'series' keys for plotting

        """
        if view_name not in self._loaded_views:
            raise ValueError(f"View not loaded: {view_name}")

        all_cols = [x_column] + y_columns
        col_str = ", ".join(all_cols)

        query = f"SELECT {col_str} FROM {view_name} ORDER BY {x_column} ASC LIMIT {limit}"

        result = self._conn.execute(query).fetchall()

        x_values = [row[0] for row in result]
        series_data: dict[str, list] = {col: [] for col in y_columns}

        for row in result:
            for i, col in enumerate(y_columns):
                series_data[col].append(row[i + 1])

        return {"x": x_values, "series": series_data}

    def get_column_info(self, view_name: str) -> list[tuple[str, str]]:
        """Get column names and types for a view.

        Args:
            view_name: View to inspect

        Returns:
            List of (column_name, column_type) tuples

        """
        if view_name not in self._loaded_views:
            raise ValueError(f"View not loaded: {view_name}")

        result = self._conn.execute(f"DESCRIBE {view_name}").fetchall()
        return [(row[0], row[1]) for row in result]

    def execute_sql(self, sql: str) -> list[dict[str, Any]]:
        """Execute arbitrary SQL query.

        Args:
            sql: SQL query string

        Returns:
            List of row dictionaries

        """
        result = self._conn.execute(sql).fetchall()
        if not self._conn.description:
            return []
        col_names = [d[0] for d in self._conn.description]
        return [dict(zip(col_names, row, strict=False)) for row in result]

    def refresh(self) -> None:
        """Refresh file discovery cache."""
        if self._discovery:
            self._discovery.invalidate_cache()

    def check_stale_files(self) -> list[WritingFileStatus]:
        """Check status of all tracked .writing files.

        This applies the retry logic (15s, then 30s delay) and triggers
        fault notifications when files remain stuck.

        Returns:
            List of statuses for tracked .writing files

        """
        if not self._discovery:
            return []
        return self._discovery.check_stale_files()

    def get_writer_faults(self) -> list[Path]:
        """Get list of files with detected writer faults.

        These are files that remained in .writing state after retry attempts.

        Returns:
            List of file paths with detected faults

        """
        if not self._discovery:
            return []
        return self._discovery.get_faulted_files()

    def get_writing_files(self) -> list[Path]:
        """Get list of currently tracked .writing files."""
        if not self._discovery:
            return []
        return self._discovery.get_writing_files()

    def close(self) -> None:
        """Close the DuckDB connection."""
        try:
            self._conn.close()
        except Exception:
            pass


def parse_time_range(time_range: str) -> tuple[date | None, date | None]:
    """Parse a time range string into start/end dates.

    Args:
        time_range: Time range like '24h', '7d', '30d'

    Returns:
        Tuple of (start_date, end_date) where end_date is today

    """
    today = date.today()
    end_date = today

    range_map = {
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "24h": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
    }

    if time_range in range_map:
        start_datetime = datetime.now() - range_map[time_range]
        return (start_datetime.date(), end_date)

    return (None, None)
