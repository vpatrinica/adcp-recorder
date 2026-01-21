"""Comprehensive tests for ParquetDataLayer and ParquetFileDiscovery.

Tests cover file discovery, caching, DuckDB views, queries, and edge cases.
"""

from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import polars as pl
import pytest

from adcp_recorder.ui.parquet_data_layer import (
    ParquetDataLayer,
    ParquetDirectory,
    ParquetFileDiscovery,
    ParquetFileInfo,
    StaleWritingFile,
    StaleWritingMonitor,
    WritingFileStatus,
    parse_time_range,
)


class TestParquetFileInfo:
    """Tests for ParquetFileInfo dataclass."""

    def test_is_complete_true(self):
        """Test that normal parquet files are complete."""
        info = ParquetFileInfo(
            path=Path("/data/test.parquet"),
            record_type="PNORS",
            file_date=date.today(),
            size_bytes=1000,
            modified_at=datetime.now(),
        )
        assert info.is_complete is True

    def test_is_complete_false_for_writing(self):
        """Test that .writing files are incomplete."""
        info = ParquetFileInfo(
            path=Path("/data/test.parquet.writing"),
            record_type="PNORS",
            file_date=date.today(),
            size_bytes=1000,
            modified_at=datetime.now(),
        )
        assert info.is_complete is False


class TestParquetDirectory:
    """Tests for ParquetDirectory dataclass."""

    def test_get_all_dates_empty(self):
        """Test get_all_dates with no data."""
        directory = ParquetDirectory(base_path=Path("/data"))
        assert directory.get_all_dates() == []

    def test_get_all_dates_multiple_types(self):
        """Test get_all_dates with multiple record types."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        directory = ParquetDirectory(
            base_path=Path("/data"),
            record_types={
                "PNORS": {today: [], yesterday: []},
                "PNORC": {today: []},
            },
        )

        dates = directory.get_all_dates()
        assert len(dates) == 2
        assert today in dates
        assert yesterday in dates
        # Should be sorted descending
        assert dates[0] > dates[1]

    def test_get_files_for_selection_all(self):
        """Test getting all files without filters."""
        today = date.today()
        file1 = ParquetFileInfo(
            path=Path("/data/test1.parquet"),
            record_type="PNORS",
            file_date=today,
            size_bytes=100,
            modified_at=datetime.now(),
        )
        file2 = ParquetFileInfo(
            path=Path("/data/test2.parquet"),
            record_type="PNORC",
            file_date=today,
            size_bytes=200,
            modified_at=datetime.now(),
        )

        directory = ParquetDirectory(
            base_path=Path("/data"),
            record_types={
                "PNORS": {today: [file1]},
                "PNORC": {today: [file2]},
            },
        )

        files = directory.get_files_for_selection()
        assert len(files) == 2

    def test_get_files_for_selection_filtered(self):
        """Test getting files with record type filter."""
        today = date.today()
        file1 = ParquetFileInfo(
            path=Path("/data/test1.parquet"),
            record_type="PNORS",
            file_date=today,
            size_bytes=100,
            modified_at=datetime.now(),
        )

        directory = ParquetDirectory(
            base_path=Path("/data"),
            record_types={"PNORS": {today: [file1]}},
        )

        files = directory.get_files_for_selection(record_types=["PNORS"])
        assert len(files) == 1

        files = directory.get_files_for_selection(record_types=["PNORC"])
        assert len(files) == 0

    def test_get_files_for_selection_date_range(self):
        """Test getting files with date range filter."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)

        file1 = ParquetFileInfo(
            path=Path("/data/test1.parquet"),
            record_type="PNORS",
            file_date=today,
            size_bytes=100,
            modified_at=datetime.now(),
        )
        file2 = ParquetFileInfo(
            path=Path("/data/test2.parquet"),
            record_type="PNORS",
            file_date=last_week,
            size_bytes=200,
            modified_at=datetime.now(),
        )

        directory = ParquetDirectory(
            base_path=Path("/data"),
            record_types={"PNORS": {today: [file1], last_week: [file2]}},
        )

        # Filter to only recent files
        files = directory.get_files_for_selection(start_date=yesterday)
        assert len(files) == 1
        assert files[0] == file1.path

    def test_get_files_excludes_incomplete(self):
        """Test that incomplete files are excluded."""
        today = date.today()
        complete = ParquetFileInfo(
            path=Path("/data/test1.parquet"),
            record_type="PNORS",
            file_date=today,
            size_bytes=100,
            modified_at=datetime.now(),
        )
        incomplete = ParquetFileInfo(
            path=Path("/data/test2.parquet.writing"),
            record_type="PNORS",
            file_date=today,
            size_bytes=200,
            modified_at=datetime.now(),
        )

        directory = ParquetDirectory(
            base_path=Path("/data"),
            record_types={"PNORS": {today: [complete, incomplete]}},
        )

        files = directory.get_files_for_selection()
        assert len(files) == 1
        assert files[0] == complete.path


class TestParquetFileDiscovery:
    """Tests for ParquetFileDiscovery class."""

    @pytest.fixture
    def temp_parquet_dir(self, tmp_path):
        """Create a temporary directory with Parquet files."""
        parquet_dir = tmp_path / "parquet"
        parquet_dir.mkdir()

        # Create PNORS directory with dates
        today = date.today()
        pnors_dir = parquet_dir / "PNORS" / f"date={today.isoformat()}"
        pnors_dir.mkdir(parents=True)

        # Create a real Parquet file using polars
        df = pl.DataFrame({"value": [1, 2, 3], "name": ["a", "b", "c"]})
        df.write_parquet(str(pnors_dir / "test_001.parquet"))

        return tmp_path

    def test_scan_empty_directory(self, tmp_path):
        """Test scanning an empty directory."""
        # Create a fresh subdirectory to avoid conftest-created files
        empty_dir = tmp_path / "empty_test"
        empty_dir.mkdir()

        discovery = ParquetFileDiscovery(empty_dir)
        result = discovery.scan()

        assert result.base_path == empty_dir
        # Should have no record types with actual files
        total_files = sum(
            len(files) for dates in result.record_types.values() for files in dates.values()
        )
        assert total_files == 0

    def test_scan_with_parquet_files(self, temp_parquet_dir):
        """Test scanning a directory with Parquet files."""
        discovery = ParquetFileDiscovery(temp_parquet_dir)
        result = discovery.scan()

        assert "PNORS" in result.record_types
        assert len(result.record_types["PNORS"]) == 1

        today = date.today()
        assert today in result.record_types["PNORS"]
        assert len(result.record_types["PNORS"][today]) == 1

    def test_scan_caching(self, temp_parquet_dir):
        """Test that scan results are cached."""
        discovery = ParquetFileDiscovery(temp_parquet_dir)
        discovery._cache_ttl_seconds = 60  # Long TTL for test

        result1 = discovery.scan()
        result2 = discovery.scan()

        # Should be the same cached object
        assert result1 is result2

    def test_scan_force_bypass_cache(self, temp_parquet_dir):
        """Test that force=True bypasses cache."""
        discovery = ParquetFileDiscovery(temp_parquet_dir)
        discovery._cache_ttl_seconds = 60

        result1 = discovery.scan()
        result2 = discovery.scan(force=True)

        # Should be different objects
        assert result1 is not result2

    def test_set_base_path_invalidates_cache(self, temp_parquet_dir, tmp_path):
        """Test that changing base path invalidates cache."""
        discovery = ParquetFileDiscovery(temp_parquet_dir)
        discovery.scan()

        assert discovery._cache is not None

        discovery.set_base_path(tmp_path)
        assert discovery._cache is None

    def test_invalidate_cache(self, temp_parquet_dir):
        """Test manual cache invalidation."""
        discovery = ParquetFileDiscovery(temp_parquet_dir)
        discovery.scan()

        assert discovery._cache is not None

        discovery.invalidate_cache()
        assert discovery._cache is None

    def test_skip_writing_files(self, tmp_path):
        """Test that .writing files are skipped."""
        parquet_dir = tmp_path / "parquet"
        today = date.today()
        pnors_dir = parquet_dir / "PNORS" / f"date={today.isoformat()}"
        pnors_dir.mkdir(parents=True)

        # Create complete file
        df = pl.DataFrame({"value": [1]})
        df.write_parquet(str(pnors_dir / "complete.parquet"))

        # Create .writing file (simulating in-progress write)
        (pnors_dir / "incomplete.parquet.writing").touch()

        discovery = ParquetFileDiscovery(tmp_path)
        result = discovery.scan()

        files = result.record_types["PNORS"][today]
        assert len(files) == 1
        assert "complete.parquet" in str(files[0].path)


class TestParquetDataLayer:
    """Tests for ParquetDataLayer class."""

    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create temporary directory with sample Parquet data."""
        parquet_dir = tmp_path / "parquet"
        today = date.today()

        # Create PNORS data
        pnors_dir = parquet_dir / "PNORS" / f"date={today.isoformat()}"
        pnors_dir.mkdir(parents=True)

        df = pl.DataFrame(
            {
                "record_id": [1, 2, 3],
                "temperature": [20.5, 21.0, 21.5],
                "received_at": [
                    datetime.now() - timedelta(hours=2),
                    datetime.now() - timedelta(hours=1),
                    datetime.now(),
                ],
            }
        )
        df.write_parquet(str(pnors_dir / "data_001.parquet"))

        # Create PNORC data
        pnorc_dir = parquet_dir / "PNORC" / f"date={today.isoformat()}"
        pnorc_dir.mkdir(parents=True)

        df2 = pl.DataFrame(
            {
                "record_id": [1, 2],
                "vel1": [0.5, 0.6],
                "vel2": [0.4, 0.5],
            }
        )
        df2.write_parquet(str(pnorc_dir / "data_001.parquet"))

        return tmp_path

    def test_init_without_path(self):
        """Test initialization without base path."""
        layer = ParquetDataLayer()
        assert layer._discovery is None
        layer.close()

    def test_init_with_path(self, temp_data_dir):
        """Test initialization with base path."""
        layer = ParquetDataLayer(temp_data_dir)
        assert layer._discovery is not None
        layer.close()

    def test_set_data_directory(self, temp_data_dir):
        """Test setting data directory."""
        layer = ParquetDataLayer()
        layer.set_data_directory(temp_data_dir)

        assert layer._discovery is not None
        assert layer._discovery.base_path == temp_data_dir
        layer.close()

    def test_get_file_structure(self, temp_data_dir):
        """Test getting file structure."""
        layer = ParquetDataLayer(temp_data_dir)
        structure = layer.get_file_structure()

        assert structure is not None
        assert "PNORS" in structure.record_types
        assert "PNORC" in structure.record_types
        layer.close()

    def test_get_file_structure_no_dir(self):
        """Test get_file_structure when no directory set."""
        layer = ParquetDataLayer()
        assert layer.get_file_structure() is None
        layer.close()

    def test_get_available_record_types(self, temp_data_dir):
        """Test getting available record types."""
        layer = ParquetDataLayer(temp_data_dir)
        types = layer.get_available_record_types()

        assert "PNORC" in types
        assert "PNORS" in types
        layer.close()

    def test_get_available_dates(self, temp_data_dir):
        """Test getting available dates."""
        layer = ParquetDataLayer(temp_data_dir)
        dates = layer.get_available_dates()

        assert len(dates) >= 1
        assert date.today() in dates
        layer.close()

    def test_get_available_dates_filtered(self, temp_data_dir):
        """Test getting dates for specific record type."""
        layer = ParquetDataLayer(temp_data_dir)
        dates = layer.get_available_dates(record_type="PNORS")

        assert len(dates) >= 1
        layer.close()

    def test_load_data(self, temp_data_dir):
        """Test loading data into views."""
        layer = ParquetDataLayer(temp_data_dir)
        result = layer.load_data()

        assert "pq_pnors" in result
        assert "pq_pnorc" in result
        assert result["pq_pnors"] == 3
        assert result["pq_pnorc"] == 2
        layer.close()

    def test_load_data_filtered(self, temp_data_dir):
        """Test loading specific record types."""
        layer = ParquetDataLayer(temp_data_dir)
        result = layer.load_data(record_types=["PNORS"])

        assert "pq_pnors" in result
        assert "pq_pnorc" not in result
        layer.close()

    def test_get_loaded_views(self, temp_data_dir):
        """Test getting list of loaded views."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        views = layer.get_loaded_views()
        assert "pq_pnorc" in views
        assert "pq_pnors" in views
        layer.close()

    def test_query(self, temp_data_dir):
        """Test basic query."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        rows = layer.query("pq_pnors")
        assert len(rows) == 3
        assert "record_id" in rows[0]
        assert "temperature" in rows[0]
        layer.close()

    def test_query_with_columns(self, temp_data_dir):
        """Test query with specific columns."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        rows = layer.query("pq_pnors", columns=["temperature"])
        assert len(rows) == 3
        assert "temperature" in rows[0]
        layer.close()

    def test_query_with_order(self, temp_data_dir):
        """Test query with ordering."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        rows = layer.query("pq_pnors", order_by="record_id", order_desc=False)
        assert rows[0]["record_id"] == 1

        rows = layer.query("pq_pnors", order_by="record_id", order_desc=True)
        assert rows[0]["record_id"] == 3
        layer.close()

    def test_query_not_loaded(self, temp_data_dir):
        """Test query on non-loaded view raises error."""
        layer = ParquetDataLayer(temp_data_dir)

        with pytest.raises(ValueError, match="View not loaded"):
            layer.query("pq_nonexistent")
        layer.close()

    def test_query_time_series(self, temp_data_dir):
        """Test time series query."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        result = layer.query_time_series("pq_pnors", "received_at", ["temperature"])
        assert len(result["x"]) == 3
        assert len(result["series"]["temperature"]) == 3
        layer.close()

    def test_get_column_info(self, temp_data_dir):
        """Test getting column info."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        columns = layer.get_column_info("pq_pnors")
        col_names = [c[0] for c in columns]

        assert "record_id" in col_names
        assert "temperature" in col_names
        layer.close()

    def test_execute_sql(self, temp_data_dir):
        """Test arbitrary SQL execution."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        result = layer.execute_sql("SELECT COUNT(*) as cnt FROM pq_pnors")
        assert result[0]["cnt"] == 3
        layer.close()

    def test_refresh(self, temp_data_dir):
        """Test cache refresh."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        # Refresh should not raise
        layer.refresh()
        layer.close()

    def test_close(self, temp_data_dir):
        """Test closing connection."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.close()
        # Should not raise on double close
        layer.close()


class TestParseTimeRange:
    """Tests for parse_time_range function."""

    def test_parse_24h(self):
        """Test 24h range."""
        start, end = parse_time_range("24h")
        assert start is not None
        assert end == date.today()
        assert start <= end

    def test_parse_7d(self):
        """Test 7d range."""
        start, end = parse_time_range("7d")
        assert start is not None
        assert end == date.today()
        assert (end - start).days <= 7

    def test_parse_30d(self):
        """Test 30d range."""
        start, end = parse_time_range("30d")
        assert start is not None
        assert end == date.today()
        assert (end - start).days <= 30

    def test_parse_unknown(self):
        """Test unknown range returns None."""
        start, end = parse_time_range("unknown")
        assert start is None
        assert end is None

    def test_parse_1h(self):
        """Test 1h range."""
        start, end = parse_time_range("1h")
        assert start is not None
        assert end == date.today()

    def test_parse_6h(self):
        """Test 6h range."""
        start, end = parse_time_range("6h")
        assert start is not None
        assert end == date.today()


class TestStaleWritingMonitor:
    """Tests for StaleWritingMonitor class."""

    def test_track_writing_file(self, tmp_path):
        """Test tracking a .writing file."""
        monitor = StaleWritingMonitor()
        writing_file = tmp_path / "test.parquet.writing"
        writing_file.touch()

        monitor.track_writing_file(writing_file)
        stale_files = monitor.get_stale_files()

        assert len(stale_files) == 1
        assert stale_files[0].path == writing_file
        assert stale_files[0].status == WritingFileStatus.WAITING_FIRST_RETRY

    def test_check_and_retry_file_completed(self, tmp_path):
        """Test that completed files are detected."""
        monitor = StaleWritingMonitor()
        writing_file = tmp_path / "test.parquet.writing"
        final_file = tmp_path / "test.parquet"

        # Create final file (simulating completed write)
        final_file.touch()

        status = monitor.check_and_retry(writing_file)
        assert status == WritingFileStatus.COMPLETED

    def test_check_and_retry_file_removed(self, tmp_path):
        """Test that removed .writing files are detected as completed."""
        monitor = StaleWritingMonitor()
        writing_file = tmp_path / "nonexistent.parquet.writing"
        # File doesn't exist

        status = monitor.check_and_retry(writing_file)
        assert status == WritingFileStatus.COMPLETED

    def test_check_and_retry_first_retry(self, tmp_path):
        """Test first retry after 15 seconds."""
        monitor = StaleWritingMonitor()
        writing_file = tmp_path / "test.parquet.writing"
        writing_file.touch()

        # Track file with backdated first_seen
        with monitor._lock:
            monitor._tracked_files[writing_file] = StaleWritingFile(
                path=writing_file,
                first_seen=datetime.now() - timedelta(seconds=16),
            )

        status = monitor.check_and_retry(writing_file)
        assert status == WritingFileStatus.WAITING_SECOND_RETRY

    def test_check_and_retry_fault_detected(self, tmp_path):
        """Test fault detection after 45 seconds."""
        fault_callback = MagicMock()
        monitor = StaleWritingMonitor(on_fault_detected=fault_callback)
        writing_file = tmp_path / "test.parquet.writing"
        writing_file.touch()

        # Track file with backdated first_seen
        with monitor._lock:
            monitor._tracked_files[writing_file] = StaleWritingFile(
                path=writing_file,
                first_seen=datetime.now() - timedelta(seconds=46),
                retry_count=1,
                status=WritingFileStatus.WAITING_SECOND_RETRY,
            )

        status = monitor.check_and_retry(writing_file)
        assert status == WritingFileStatus.FAULT_DETECTED
        fault_callback.assert_called_once()

    def test_on_file_completed_callback(self, tmp_path):
        """Test callback when file completes."""
        completed_callback = MagicMock()
        monitor = StaleWritingMonitor(on_file_completed=completed_callback)

        writing_file = tmp_path / "test.parquet.writing"
        final_file = tmp_path / "test.parquet"

        # Track the .writing file
        monitor.track_writing_file(writing_file)

        # Create final file
        final_file.touch()

        # Check should trigger completed callback
        status = monitor.check_and_retry(writing_file)
        assert status == WritingFileStatus.COMPLETED
        completed_callback.assert_called_once_with(writing_file)

    def test_get_faulted_files(self, tmp_path):
        """Test getting list of faulted files."""
        monitor = StaleWritingMonitor()
        writing_file = tmp_path / "test.parquet.writing"
        writing_file.touch()

        # Track file with fault status
        with monitor._lock:
            monitor._tracked_files[writing_file] = StaleWritingFile(
                path=writing_file,
                first_seen=datetime.now() - timedelta(seconds=60),
                retry_count=2,
                status=WritingFileStatus.FAULT_DETECTED,
            )

        faulted = monitor.get_faulted_files()
        assert len(faulted) == 1
        assert faulted[0] == writing_file

    def test_clear(self, tmp_path):
        """Test clearing tracked files."""
        monitor = StaleWritingMonitor()
        writing_file = tmp_path / "test.parquet.writing"
        writing_file.touch()

        monitor.track_writing_file(writing_file)
        assert len(monitor.get_stale_files()) == 1

        monitor.clear()
        assert len(monitor.get_stale_files()) == 0


class TestParquetDataLayerStaleMonitoring:
    """Tests for stale file monitoring in ParquetDataLayer."""

    def test_writer_fault_callback(self, tmp_path):
        """Test that writer fault callback is invoked."""
        fault_callback = MagicMock()
        layer = ParquetDataLayer(on_writer_fault=fault_callback)
        layer.set_data_directory(tmp_path)

        # Simulate tracking a stale file
        writing_file = tmp_path / "parquet" / "PNORS" / "date=2026-01-01" / "test.parquet.writing"
        writing_file.parent.mkdir(parents=True, exist_ok=True)
        writing_file.touch()

        # Scan to pick up the .writing file
        layer.get_file_structure()

        # Force the file into fault state
        with layer._stale_monitor._lock:
            layer._stale_monitor._tracked_files[writing_file] = StaleWritingFile(
                path=writing_file,
                first_seen=datetime.now() - timedelta(seconds=60),
                retry_count=1,
                status=WritingFileStatus.WAITING_SECOND_RETRY,
            )

        # Check should trigger fault
        layer.check_stale_files()
        fault_callback.assert_called_once()
        layer.close()

    def test_get_writing_files(self, tmp_path):
        """Test getting list of .writing files."""
        layer = ParquetDataLayer()
        layer.set_data_directory(tmp_path)

        # Create a .writing file
        date_dir = tmp_path / "parquet" / "PNORS" / "date=2026-01-01"
        date_dir.mkdir(parents=True, exist_ok=True)
        writing_file = date_dir / "test.parquet.writing"
        writing_file.touch()

        # Scan to pick up the file
        layer.get_file_structure()

        writing_files = layer.get_writing_files()
        assert len(writing_files) == 1
        layer.close()

    def test_get_writer_faults_no_discovery(self):
        """Test get_writer_faults when no discovery is set."""
        layer = ParquetDataLayer()
        assert layer.get_writer_faults() == []
        layer.close()
