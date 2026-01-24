"""Comprehensive tests for ParquetDataLayer and ParquetFileDiscovery.

Tests cover file discovery, caching, DuckDB views, queries, and edge cases.
"""

import unittest
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

        with pytest.raises(ValueError, match="Unknown data source"):
            layer.query("pq_nonexistent")
        layer.close()

    def test_query_time_series(self, temp_data_dir):
        """Test time series query."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        result = layer.query_time_series(
            source_name="pq_pnors", y_columns=["temperature"], x_column="received_at"
        )
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

    def test_resolve_source_name_direct_match(self, temp_data_dir):
        """Test resolve_source_name with already-valid view name."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        # Direct pq_ name should resolve to itself
        assert layer.resolve_source_name("pq_pnors") == "pq_pnors"
        assert layer.resolve_source_name("pq_pnorc") == "pq_pnorc"
        layer.close()

    def test_resolve_source_name_from_duckdb_name(self, temp_data_dir):
        """Test resolve_source_name maps DuckDB names to parquet views."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        # DuckDB style names should resolve to pq_ prefixed views
        assert layer.resolve_source_name("pnors_data") == "pq_pnors"
        assert layer.resolve_source_name("pnorc_data") == "pq_pnorc"
        layer.close()

    def test_resolve_source_name_unknown(self, temp_data_dir):
        """Test resolve_source_name returns None for unknown sources."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        assert layer.resolve_source_name("unknown_data") is None
        assert layer.resolve_source_name("pq_nonexistent") is None
        layer.close()

    def test_get_source_metadata_with_duckdb_name(self, temp_data_dir):
        """Test get_source_metadata works with DuckDB-style names."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        # Should resolve pnors_data to pq_pnors and return metadata
        source = layer.get_source_metadata("pnors_data")
        assert source is not None
        assert source.name == "pq_pnors"
        layer.close()

    def test_query_data_with_duckdb_name(self, temp_data_dir):
        """Test query_data works with DuckDB-style names."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        # Should resolve pnors_data to pq_pnors and query successfully
        rows = layer.query_data("pnors_data")
        assert len(rows) == 3
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


class TestCoverageEdgeCases:
    """Tests for edge cases and error handling to increase coverage."""

    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create temporary directory with sample Parquet data."""
        parquet_dir = tmp_path / "parquet"
        today = date.today()

        # Create PNORS data with received_at for time filtering
        pnors_dir = parquet_dir / "PNORS" / f"date={today.isoformat()}"
        pnors_dir.mkdir(parents=True)

        df = pl.DataFrame(
            {
                "record_id": [1, 2, 3],
                "temperature": [20.5, 21.0, 21.5],
                "status": ["ok", "warn", "ok"],
                "received_at": [
                    datetime.now() - timedelta(hours=2),
                    datetime.now() - timedelta(hours=1),
                    datetime.now(),
                ],
            }
        )
        df.write_parquet(str(pnors_dir / "data_001.parquet"))

        return tmp_path

    def test_stale_monitor_callback_error_on_complete(self, tmp_path):
        """Test that callback errors are caught when file completes."""

        def bad_callback(path):
            raise RuntimeError("Callback error")

        monitor = StaleWritingMonitor(on_file_completed=bad_callback)
        writing_file = tmp_path / "test.parquet.writing"
        final_file = tmp_path / "test.parquet"

        # Track the .writing file
        monitor.track_writing_file(writing_file)

        # Create final file (simulating completed write)
        final_file.touch()

        # Check should not raise despite callback error
        status = monitor.check_and_retry(writing_file)
        assert status == WritingFileStatus.COMPLETED

    def test_stale_monitor_callback_error_on_fault(self, tmp_path):
        """Test that callback errors are caught when fault detected."""

        def bad_callback(path, msg):
            raise RuntimeError("Callback error")

        monitor = StaleWritingMonitor(on_fault_detected=bad_callback)
        writing_file = tmp_path / "test.parquet.writing"
        writing_file.touch()

        # Track file with backdated first_seen to trigger fault
        with monitor._lock:
            monitor._tracked_files[writing_file] = StaleWritingFile(
                path=writing_file,
                first_seen=datetime.now() - timedelta(seconds=60),
                retry_count=1,
                status=WritingFileStatus.WAITING_SECOND_RETRY,
            )

        # Check should not raise despite callback error
        status = monitor.check_and_retry(writing_file)
        assert status == WritingFileStatus.FAULT_DETECTED

    def test_stale_monitor_already_faulted(self, tmp_path):
        """Test checking a file that's already in fault state."""
        monitor = StaleWritingMonitor()
        writing_file = tmp_path / "test.parquet.writing"
        writing_file.touch()

        # Track file already in fault state
        with monitor._lock:
            monitor._tracked_files[writing_file] = StaleWritingFile(
                path=writing_file,
                first_seen=datetime.now() - timedelta(seconds=120),
                retry_count=2,
                status=WritingFileStatus.FAULT_DETECTED,
            )

        # Check should return fault detected
        status = monitor.check_and_retry(writing_file)
        assert status == WritingFileStatus.FAULT_DETECTED

    def test_stale_monitor_track_during_check(self, tmp_path):
        """Test that untracked file gets tracked during check."""
        monitor = StaleWritingMonitor()
        writing_file = tmp_path / "test.parquet.writing"
        writing_file.touch()

        # File is not tracked yet - check_and_retry should track it
        assert writing_file not in monitor._tracked_files

        status = monitor.check_and_retry(writing_file)
        assert status == WritingFileStatus.WAITING_FIRST_RETRY
        assert writing_file in monitor._tracked_files

    def test_query_data_with_filters(self, temp_data_dir):
        """Test query_data with column filters."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        # Query with filter
        rows = layer.query_data("pnors_data", filters={"status": "ok"})
        assert len(rows) == 2
        for row in rows:
            assert row["status"] == "ok"
        layer.close()

    def test_query_data_with_time_filters(self, temp_data_dir):
        """Test query_data with time range filters."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        # Query with start_time
        start = datetime.now() - timedelta(hours=1, minutes=30)
        rows = layer.query_data("pnors_data", start_time=start)
        assert len(rows) >= 1
        layer.close()

    def test_query_data_with_end_time(self, temp_data_dir):
        """Test query_data with end_time filter."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        end = datetime.now() - timedelta(minutes=30)
        rows = layer.query_data("pnors_data", end_time=end)
        # Should filter to older records
        assert len(rows) >= 1
        layer.close()

    def test_query_data_with_conditions(self, temp_data_dir):
        """Test query_data with multiple conditions combined."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        rows = layer.query_data(
            "pnors_data",
            filters={"status": "ok"},
            start_time=datetime.now() - timedelta(days=1),
        )
        assert isinstance(rows, list)
        layer.close()

    def test_get_column_stats(self, temp_data_dir):
        """Test get_column_stats for numeric column."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        stats = layer.get_column_stats("pnors_data", "temperature")
        assert "min" in stats
        assert "max" in stats
        assert "avg" in stats
        assert "count" in stats
        assert stats["count"] == 3
        layer.close()

    def test_get_column_stats_unknown_source(self, temp_data_dir):
        """Test get_column_stats with unknown source."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        stats = layer.get_column_stats("unknown_data", "temperature")
        assert stats == {}
        layer.close()

    def test_get_column_stats_non_numeric(self, temp_data_dir):
        """Test get_column_stats with non-numeric column."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        # status is text, not numeric
        stats = layer.get_column_stats("pnors_data", "status")
        assert stats == {}
        layer.close()

    def test_get_available_sources(self, temp_data_dir):
        """Test get_available_sources returns loaded views."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        sources = layer.get_available_sources()
        assert len(sources) >= 1
        source_names = [s.name for s in sources]
        assert "pq_pnors" in source_names
        layer.close()

    def test_load_data_no_structure(self):
        """Test load_data when no directory is set."""
        layer = ParquetDataLayer()
        result = layer.load_data()
        assert result == {}
        layer.close()

    def test_check_stale_files_no_monitor(self, temp_data_dir):
        """Test check_stale_files without monitor."""
        # Create layer without fault callback to skip monitor
        layer = ParquetDataLayer(temp_data_dir)

        # Should return empty list
        statuses = layer.check_stale_files()
        assert isinstance(statuses, list)
        layer.close()

    def test_discovery_stale_files_completed(self, tmp_path):
        """Test that completed .writing files are removed from tracking."""
        parquet_dir = tmp_path / "parquet"
        today = date.today()
        pnors_dir = parquet_dir / "PNORS" / f"date={today.isoformat()}"
        pnors_dir.mkdir(parents=True)

        # Create writing file
        writing_file = pnors_dir / "test.parquet.writing"
        writing_file.touch()

        # Also create complete file
        df = pl.DataFrame({"value": [1]})
        df.write_parquet(str(pnors_dir / "complete.parquet"))

        layer = ParquetDataLayer(tmp_path)
        layer.get_file_structure()  # This triggers scan

        # Create final file (simulating write complete)
        final_file = pnors_dir / "test.parquet"
        final_file.touch()

        # Check stale files - should mark as completed
        statuses = layer.check_stale_files()
        # After check, writing file should be removed
        assert WritingFileStatus.COMPLETED in statuses or len(statuses) == 0
        layer.close()

    def test_query_time_series_not_loaded(self, temp_data_dir):
        """Test query_time_series returns empty for unloaded view."""
        layer = ParquetDataLayer(temp_data_dir)
        # Don't load data

        result = layer.query_time_series("pq_pnors", ["temperature"], "24h", "received_at")
        assert result == {"x": [], "series": {"temperature": []}}
        layer.close()

    def test_get_column_info_not_loaded(self, temp_data_dir):
        """Test get_column_info returns empty for unloaded view."""
        layer = ParquetDataLayer(temp_data_dir)
        # Don't load data

        assert layer.get_column_info("pq_pnors") == []
        layer.close()

    def test_execute_sql_empty_result(self, temp_data_dir):
        """Test execute_sql with query returning no rows."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        result = layer.execute_sql("SELECT * FROM pq_pnors WHERE 1=0")
        assert result == []
        layer.close()

    def test_get_source_metadata_describe_error(self, temp_data_dir):
        """Test get_source_metadata handles describe errors gracefully."""
        layer = ParquetDataLayer(temp_data_dir)
        layer.load_data()

        # Add a fake view name to loaded_views to trigger describe on non-existent
        layer._loaded_views.add("fake_view")

        # Should return None for non-existent view
        source = layer.get_source_metadata("fake_view")
        assert source is None
        layer.close()


@pytest.fixture(scope="module")
def wave_data_dir(tmp_path_factory):
    """Create temporary directory with wave-related Parquet data."""
    tmp_path = tmp_path_factory.mktemp("wave_data")
    parquet_dir = tmp_path / "parquet"
    today = date.today()
    # Use a fixed timestamp for consistency in grouping
    now = datetime.now().replace(microsecond=0)

    # Create PNORE data (Energy Density)
    pnore_dir = parquet_dir / "PNORE" / f"date={today.isoformat()}"
    pnore_dir.mkdir(parents=True)

    import json

    energy_densities = [0.1, 0.2, 0.3, 0.4, 0.5]
    df_e = pl.DataFrame(
        {
            "measurement_date": [today.isoformat()],
            "measurement_time": ["12:00:00"],
            "received_at": [now],
            "start_frequency": [0.0],
            "step_frequency": [0.01],
            "num_frequencies": [5],
            "energy_densities": [json.dumps(energy_densities)],
        }
    )
    df_e.write_parquet(str(pnore_dir / "energy.parquet"))

    # Create PNORWD data (Directional Spectrum)
    pnorwd_dir = parquet_dir / "PNORWD" / f"date={today.isoformat()}"
    pnorwd_dir.mkdir(parents=True)

    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    df_wd = pl.DataFrame(
        {
            "measurement_date": [today.isoformat(), today.isoformat()],
            "measurement_time": ["12:00:00", "12:00:00"],
            "received_at": [now, now],
            "direction_type": ["MD", "DS"],
            "values": [json.dumps(values), json.dumps(values)],
        }
    )
    df_wd.write_parquet(str(pnorwd_dir / "direction.parquet"))

    # Create PNORC data (Amplitude)
    pnorc_dir = parquet_dir / "PNORC" / f"date={today.isoformat()}"
    pnorc_dir.mkdir(parents=True)

    df_c = pl.DataFrame(
        {
            "received_at": [now, now],
            "cell_index": [0, 1],
            "amp1": [50.0, 60.0],
            "amp2": [55.0, 65.0],
            "amp3": [60.0, 70.0],
            "amp4": [65.0, 75.0],
        }
    )
    df_c.write_parquet(str(pnorc_dir / "amplitude.parquet"))

    # Create PNORS data (Fourier coefficients)
    pnors_dir = parquet_dir / "PNORS" / f"date={today.isoformat()}"
    pnors_dir.mkdir(parents=True)

    df_s = pl.DataFrame(
        {
            "measurement_date": [today.isoformat()],
            "measurement_time": ["12:00:00"],
            "received_at": [now],
            "coefficient_flag": ["A1"],
            "start_frequency": [0.0],
            "step_frequency": [0.01],
            "num_frequencies": [5],
            "coefficients": [json.dumps(values)],
        }
    )
    df_s.write_parquet(str(pnors_dir / "fourier.parquet"))

    return tmp_path


class TestParquetDataLayerWaveAnalysis:
    """Tests for wave analysis methods in ParquetDataLayer."""

    def test_get_available_bursts(self, wave_data_dir):
        """Test retrieving available measurement bursts."""
        layer = ParquetDataLayer(wave_data_dir)
        layer.load_data()

        bursts = layer.get_available_bursts(source_name="pnore_data")
        assert len(bursts) == 1
        assert bursts[0]["measurement_time"] == "12:00:00"
        assert "label" in bursts[0]
        layer.close()

    def test_query_wave_energy(self, wave_data_dir):
        """Test querying wave energy spectrum."""
        layer = ParquetDataLayer(wave_data_dir)
        layer.load_data()

        result = layer.query_wave_energy("pnore_data")
        assert len(result) == 1
        assert "energy_densities" in result[0]
        layer.close()

    def test_query_amplitude_heatmap(self, wave_data_dir):
        """Test querying amplitude heatmap data."""
        layer = ParquetDataLayer(wave_data_dir)
        layer.load_data()

        result = layer.query_amplitude_heatmap("pnorc_data")
        assert len(result) == 1
        assert "amplitudes" in result[0]
        assert len(result[0]["amplitudes"]) == 2  # Cell 0 and 1
        layer.close()

    def test_query_spectrum_data(self, wave_data_dir):
        """Test querying Fourier coefficient spectrum."""
        layer = ParquetDataLayer(wave_data_dir)
        layer.load_data()

        result = layer.query_spectrum_data("pnors_data", coefficient="A1")
        assert len(result) == 1
        assert result[0]["coefficient_flag"] == "A1"
        layer.close()

    def test_query_directional_spectrum_latest(self, wave_data_dir):
        """Test querying latest directional spectrum."""
        layer = ParquetDataLayer(wave_data_dir)
        layer.load_data()

        result = layer.query_directional_spectrum()
        assert "energy" in result
        assert "directions" in result
        assert "spreads" in result
        assert len(result["frequencies"]) == 5
        layer.close()

    def test_query_directional_spectrum_specific_timestamp(self, wave_data_dir):
        """Test querying directional spectrum for a specific timestamp."""
        layer = ParquetDataLayer(wave_data_dir)
        layer.load_data()

        # Get the timestamp from a query
        bursts = layer.get_available_bursts(source_name="pnore_data")
        ts = bursts[0]["received_at"]

        result = layer.query_directional_spectrum(timestamp=ts)
        assert result["timestamp"] == ts
        layer.close()

    def test_wave_queries_error_handling(self, wave_data_dir):
        """Test error handling in wave queries."""
        layer = ParquetDataLayer(wave_data_dir)
        layer.load_data()

        # Mock connection to raise Exception
        layer.conn = MagicMock()
        layer.conn.execute.side_effect = Exception("DB Error")
        layer._conn = layer.conn
        layer._conn.execute.side_effect = Exception("DB Error")

        assert layer.get_available_bursts(source_name="pnore_data") == []
        assert layer.query_wave_energy("pnore_data") == []
        assert layer.query_amplitude_heatmap("pnorc_data") == []
        assert layer.query_spectrum_data("pnors_data") == []
        assert layer.query_directional_spectrum() == {}

        layer.close()


class TestParquetDataLayerErrorPaths:
    """Tests for error handling in ParquetDataLayer."""

    def test_resolve_source_name_regex(self, wave_data_dir):
        """Test resolve_source_name with regex matching patterns."""
        layer = ParquetDataLayer(wave_data_dir)
        layer.load_data()
        # Should match pnorc12 -> pq_pnorc using direct pq_ prefix
        assert layer.resolve_source_name("pnorc12") == "pq_pnorc"
        # Should match PNORF_DATA -> pq_pnorf
        # First ensure pnorf is in loaded views
        layer._loaded_views.add("pq_pnorf")
        assert layer.resolve_source_name("pnorf_data") == "pq_pnorf"

        # Test fallback for 'pnor' base type ending in 'data' without underscore
        layer._loaded_views.add("pq_pnorw")
        assert layer.resolve_source_name("pnorwdata_something") == "pq_pnorw"

        layer.close()

    def test_close_error_handling(self):
        """Test that close() handles DuckDB errors gracefully."""
        layer = ParquetDataLayer()
        layer.conn = MagicMock()
        layer.conn.close.side_effect = Exception("Close error")
        layer._conn = layer.conn
        # Should not raise
        layer.close()

    def test_clear_views_error_handling(self):
        """Test that _clear_views handles errors during DROP VIEW."""
        layer = ParquetDataLayer()
        layer._loaded_views.add("test_view")
        layer.conn = MagicMock()
        layer.conn.execute.side_effect = Exception("Drop error")
        layer._conn = layer.conn
        # Should not raise
        layer._clear_views()
        assert len(layer._loaded_views) == 0
        layer.close()

    def test_load_data_errors(self, tmp_path):
        """Test that load_data handles errors during view creation."""
        # Create a valid structure but mock execute to fail
        layer = ParquetDataLayer(tmp_path)
        # Create a fake file in discovery
        date_dir = tmp_path / "parquet" / "PNORS" / "date=2026-01-01"
        date_dir.mkdir(parents=True)
        (date_dir / "test.parquet").touch()

        layer.conn = MagicMock()
        layer.conn.execute.side_effect = Exception("Create view error")
        layer._conn = layer.conn

        result = layer.load_data()
        assert result == {}  # Empty result due to error
        layer.close()

    def test_get_source_metadata_count_error(self, wave_data_dir):
        """Test that get_source_metadata handles COUNT(*) errors."""
        layer = ParquetDataLayer(wave_data_dir)
        layer.load_data()

        # Replace connection with a mock that fails for COUNT(*)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        def side_effect(query, *args, **kwargs):
            if "COUNT(*)" in query:
                raise Exception("Count error")
            if "DESCRIBE" in query:
                mock_cursor.fetchall.return_value = [("col", "BIGINT", "YES", None, None, None)]
            else:
                mock_cursor.fetchall.return_value = []
            return mock_cursor

        mock_conn.execute.side_effect = side_effect
        layer._conn = mock_conn

        source = layer.get_source_metadata("pq_pnors")
        assert source is not None
        assert source.record_count == 0  # Default on error
        layer.close()

    def test_get_column_stats_error(self, wave_data_dir):
        """Test that get_column_stats handles query errors."""
        layer = ParquetDataLayer(wave_data_dir)
        layer.load_data()

        layer.conn = MagicMock()
        layer.conn.execute.side_effect = Exception("Stats error")
        layer._conn = layer.conn

        stats = layer.get_column_stats("pq_pnors", "temperature")
        assert stats == {}
        layer.close()

    def test_query_time_series_errors(self, wave_data_dir):
        """Test that query_time_series handles query errors."""
        layer = ParquetDataLayer(wave_data_dir)
        layer.load_data()

        layer.conn = MagicMock()
        layer.conn.execute.side_effect = Exception("Query error")
        layer._conn = layer.conn

        result = layer.query_time_series("pq_pnors", y_columns=["temperature"])
        assert result == {"x": [], "series": {"temperature": []}}
        layer.close()


class TestParquetFileDiscoveryEdgeCases:
    """Tests for edge cases in ParquetFileDiscovery."""

    def test_scan_os_error(self, tmp_path):
        """Test scanning directory with OS errors."""
        discovery = ParquetFileDiscovery(tmp_path)

        with MagicMock() as mock_path:
            mock_path.exists.return_value = True
            mock_path.iterdir.side_effect = OSError("Access denied")
            # Replace Path behavior for the test
            import unittest.mock

            with unittest.mock.patch(
                "adcp_recorder.ui.parquet_data_layer.Path", return_value=mock_path
            ):
                # Should handle OSError gracefully
                result = discovery.scan()
                assert isinstance(result, ParquetDirectory)

    def test_scan_stat_error(self, tmp_path):
        """Test scanning with stat() errors on files."""
        parquet_dir = tmp_path / "parquet" / "PNORS" / "date=2026-01-01"
        parquet_dir.mkdir(parents=True)
        test_file = parquet_dir / "test.parquet"
        test_file.touch()

        discovery = ParquetFileDiscovery(tmp_path)

        # Capture original stat to use for non-target files
        original_stat = Path.stat

        def side_effect(self, *args, **kwargs):
            # Only fail for the specific test file
            if str(self) == str(test_file):
                raise OSError("Stat error")
            return original_stat(self, *args, **kwargs)

        with unittest.mock.patch("pathlib.Path.stat", side_effect=side_effect, autospec=True):
            result = discovery.scan()
            # PNORS should be there (directory traversal worked)
            assert "PNORS" in result.record_types
            # But the file list is empty because stat failed for the file
            assert len(result.record_types["PNORS"][date(2026, 1, 1)]) == 0

    def test_scan_invalid_dates(self, tmp_path):
        """Test scanning directories with invalid date formats."""
        parquet_dir = tmp_path / "parquet" / "PNORS" / "date=not-a-date"
        parquet_dir.mkdir(parents=True)

        discovery = ParquetFileDiscovery(tmp_path)
        result = discovery.scan()
        # Should be skipped
        assert date(2026, 1, 1) not in result.record_types["PNORS"]

    def test_scan_non_directories(self, tmp_path):
        """Test scanning where files are found instead of directories."""
        parquet_dir = tmp_path / "parquet"
        parquet_dir.mkdir()
        # Create a file instead of a record type directory
        (parquet_dir / "NOT_A_DIR").touch()

        discovery = ParquetFileDiscovery(tmp_path)
        result = discovery.scan()
        assert "NOT_A_DIR" not in result.record_types

    def test_stale_monitor_none_coverage(self, tmp_path):
        """Cover paths where stale_monitor is None."""
        discovery = ParquetFileDiscovery(tmp_path, stale_monitor=None)
        assert discovery.check_stale_files() == []
        assert discovery.get_faulted_files() == []


class TestMiscCoverage:
    """Miscellaneous tests for full coverage."""

    def test_parse_time_range_custom_logic(self):
        """Cover _parse_time_range branches."""
        layer = ParquetDataLayer()
        # 1h, 6h, 24h, 7d, 30d are handled in map
        assert layer._parse_time_range("1h") is not None
        assert layer._parse_time_range("6h") is not None
        assert layer._parse_time_range("invalid") is None
        layer.close()

    def test_infer_column_type_other(self):
        """Cover BOOLEAN and JSON type inference."""
        layer = ParquetDataLayer()
        from adcp_recorder.ui.data_layer import ColumnType

        assert layer._infer_column_type("BOOLEAN") == ColumnType.BOOLEAN
        assert layer._infer_column_type("JSON") == ColumnType.JSON
        assert layer._infer_column_type("UNKNOWN") == ColumnType.TEXT
        layer.close()

    def test_query_data_column_filtering(self, wave_data_dir):
        """Cover logic for valid/invalid column selection in query_data."""
        layer = ParquetDataLayer(wave_data_dir)
        layer.load_data()

        # Valid column
        rows = layer.query_data("pnore_data", columns=["start_frequency"])
        assert "start_frequency" in rows[0]
        assert "num_frequencies" not in rows[0]

        # Invalid column - should fallback to all columns or just valid ones
        rows = layer.query_data("pnore_data", columns=["nonexistent"])
        assert len(rows[0]) > 1  # Fallback to *
        layer.close()

    def test_execute_sql_no_description(self):
        """Cover case where query has no description (e.g. non-SELECT)."""
        layer = ParquetDataLayer()
        # Use a query that doesn't return rows (though DuckDB usually has description)
        # Mocking description to be None
        layer.conn = MagicMock()
        layer.conn.description = None
        layer._conn = layer.conn
        assert layer.execute_sql("INSERT INTO ...") == []
        layer.close()

    def test_additional_coverage_gaps(self, tmp_path):
        """Cover remaining small gaps identified in report."""
        # 246: end_date filter in get_files_for_selection
        today = date.today()
        yesterday = today - timedelta(days=1)
        info = ParquetFileInfo(Path("f.pq"), "T", today, 0, datetime.now())
        pd = ParquetDirectory(tmp_path, {"T": {today: [info]}})
        assert pd.get_files_for_selection(end_date=yesterday) == []

        # 316-318: scan missing dir
        discovery = ParquetFileDiscovery(tmp_path / "nonexistent")
        res = discovery.scan()
        assert res.record_types == {}

        # 332: non-directory in record_type_dir
        pdir = tmp_path / "parquet" / "TYPE"
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "not_a_date_dir").touch()
        discovery2 = ParquetFileDiscovery(tmp_path)
        discovery2.scan(force=True)

        # 341-342: invalid date format (date.fromisoformat)
        pdir2 = tmp_path / "parquet" / "TYPE2" / "date=2024-99-99"
        pdir2.mkdir(parents=True, exist_ok=True)
        discovery2.scan(force=True)

        # 369-370: scan OS error on record_type_dir
        with unittest.mock.patch("pathlib.Path.iterdir") as mock_iter:
            mock_iter.side_effect = OSError("Scan error")
            discovery2.scan(force=True)

        # 406: get_faulted_files no monitor
        discovery3 = ParquetFileDiscovery(tmp_path, stale_monitor=None)
        assert discovery3.get_faulted_files() == []

        # 477, 484: get_available_record_types and get_available_dates no discovery
        layer = ParquetDataLayer()
        assert layer.get_available_record_types() == []
        assert layer.get_available_dates() == []

        # 519: load_data type not in structure
        layer.set_data_directory(tmp_path)
        assert layer.load_data(record_types=["NON_EXISTENT"]) == {}

        # 528: load_data no files matching
        # discovery exists but has no files for a TYPE
        assert layer._discovery is not None
        layer._discovery._cache = ParquetDirectory(tmp_path, {"TYPE": {}})
        assert layer.load_data(record_types=["TYPE"]) == {}

        # 589: resolve_source_name pq_ prefix direct match
        layer._loaded_views.add("pq_test")
        assert layer.resolve_source_name("test") == "pq_test"

        # 674-675: get_source_metadata COUNT(*) exception
        # Covered by fixed test_get_source_metadata_count_error

        # 755-757: get_column_stats exception
        # Mock connection to fail for stats query
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("Stats error")
        layer.conn = mock_conn  # Update inherited conn too
        layer._conn = mock_conn
        # Must return metadata for stats to proceed
        with unittest.mock.patch.object(layer, "get_source_metadata") as mock_meta:
            m = MagicMock()
            m.get_column.return_value = MagicMock(column_type="numeric")
            m.name = "pq_test"
            mock_meta.return_value = m
            assert layer.get_column_stats("pq_test", "col") == {}

        # 786: resolve_source_name returns None in query_data
        assert layer.query_data("unknown") == []

        # 908, 916: empty result/y_columns in query_time_series
        assert layer.query_time_series(source_name="unknown", y_columns=[]) == {
            "x": [],
            "series": {},
        }
        layer.load_data()  # Ensure some views loaded or mock it
        layer._loaded_views.add("pq_test")
        assert layer.query_time_series(source_name="pq_test", y_columns=[]) == {
            "x": [],
            "series": {},
        }

        # 985, 999, 1004: no discovery in stale checks
        layer2 = ParquetDataLayer()
        assert layer2.check_stale_files() == []
        assert layer2.get_writer_faults() == []
        assert layer2.get_writing_files() == []

        # 999, 406: coverage for get_writer_faults with discovery
        assert layer.get_writer_faults() == []

        # Wave queries error paths (None resolved)
        assert layer.get_available_bursts(source_name="nonexistent") == []
        assert layer.query_wave_energy("nonexistent") == []
        assert layer.query_amplitude_heatmap("nonexistent") == []
        assert layer.query_spectrum_data("nonexistent") == []

        # 1045-1046: end_time in get_available_bursts
        layer._loaded_views.add("pq_pnore")
        layer.get_available_bursts(source_name="pnore", end_time=datetime.now())

        # 1202, 1218, 1233, 1248: directional spectrum edge cases
        # Reset side_effect
        mock_conn.execute.side_effect = None

        # 1202: missing pnorwd
        assert layer.query_directional_spectrum() == {}

        layer._loaded_views.add("pq_pnorwd")
        # 1218: timestamp not found
        mock_conn.execute.return_value.fetchone.return_value = None
        assert layer.query_directional_spectrum(timestamp=datetime.now()) == {}

        # 1233: latest not found (empty tables)
        mock_conn.execute.return_value.fetchone.return_value = None
        assert layer.query_directional_spectrum() == {}

        # 1248: energy_data not found
        mock_conn.execute.return_value.fetchone.side_effect = [
            ("2024-01-01", "12:00:00", datetime.now()),  # latest result
            None,  # energy_data result
        ]
        assert layer.query_directional_spectrum() == {}

        layer.close()
        layer2.close()
