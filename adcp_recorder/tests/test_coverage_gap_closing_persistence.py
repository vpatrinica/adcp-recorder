import threading
import time
from collections.abc import Sized
from datetime import date, datetime
from pathlib import Path
from queue import Empty, Queue
from typing import cast
from unittest.mock import MagicMock, patch

import duckdb
import polars as pl

from adcp_recorder.export.binary_writer import BinaryBlobWriter
from adcp_recorder.export.file_writer import FileWriter
from adcp_recorder.export.parquet_writer import ParquetWriter
from adcp_recorder.serial.binary_chunk import BinaryChunk
from adcp_recorder.serial.consumer import MessageRouter, SerialConsumer
from adcp_recorder.ui.components.table_view import render_table_view
from adcp_recorder.ui.data_layer import ColumnMetadata, ColumnType, DataSource


def test_binary_writer_error_paths(tmp_path: Path):
    """Cover the new try-except blocks in BinaryBlobWriter."""
    writer = BinaryBlobWriter(str(tmp_path))

    with patch("builtins.open", side_effect=OSError("Disk full")):
        path = writer.start_blob(b"data")
        assert path == ""

    mock_file = MagicMock()
    mock_file.write.side_effect = OSError("Write failed")
    writer._current_file = mock_file
    writer._current_filepath = "test.dat"
    writer.append_chunk(b"more data")

    mock_file.close.side_effect = OSError("Close failed")
    writer.finish_blob()
    assert writer._current_file is None


def test_file_writer_error_paths(tmp_path: Path):
    """Cover the new try-except blocks in FileWriter."""
    writer = FileWriter(str(tmp_path))

    # Mock parquet_writer.flush_stale to fail (Line 123)
    mock_pq = MagicMock()
    mock_pq.flush_stale.side_effect = Exception("Flush failure")
    mock_pq.close.side_effect = Exception("PQ Close Error")
    writer.parquet_writer = mock_pq

    writer.flush_stale(0)  # Hits 123

    mock_handle = MagicMock()
    mock_handle.write.side_effect = OSError("Write failed")

    with patch.object(writer, "_get_file_handle", return_value=mock_handle):
        writer.write("test", "prefix")  # Hits error log in write

    writer.close()  # Hits 127-128


def test_parquet_writer_schema_alignment_coverage(tmp_path: Path):
    """Exercise the schema alignment logic in _write_to_parquet."""
    writer = ParquetWriter(str(tmp_path))

    # 1. Trigger float promotion (Line 206)
    date_str = time.strftime("%Y-%m-%d")
    existing_path = tmp_path / "parquet" / "TEST" / f"date={date_str}" / "data.parquet"
    existing_path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"val": [1.1, 2.2], "received_at": [1.0, 2.0]}).write_parquet(existing_path)

    writer.write_record("test", {"val": 1, "received_at": 3.0})  # 1 is int
    writer.flush("test")  # Should hit 206

    # 2. Trigger casting failure (Line 211-212)
    existing_path_fail = tmp_path / "parquet" / "FAIL" / f"date={date_str}" / "data.parquet"
    existing_path_fail.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"val": [1, 2], "received_at": [1.0, 2.0]}).write_parquet(existing_path_fail)

    writer.write_record("fail", {"val": "not_an_int", "received_at": 3.0})
    writer.flush("fail")


def test_parquet_writer_close_error(tmp_path: Path):
    """Cover the new try-except in ParquetWriter.close."""
    mock_conn = MagicMock()
    mock_conn.close.side_effect = Exception("DuckDB shutdown error")

    with patch("duckdb.connect", return_value=mock_conn):
        writer = ParquetWriter(str(tmp_path))
        writer.close()


def test_parquet_writer_flush_error(tmp_path: Path):
    """Cover Exception in ParquetWriter.flush."""
    writer = ParquetWriter(str(tmp_path))
    writer.write_record("test", {"val": 1})
    with patch.object(writer, "_write_to_parquet", side_effect=Exception("Write error")):
        writer.flush("test")


def test_parquet_writer_legacy_compaction_error(tmp_path: Path):
    """Cover Exception when reading legacy files in ParquetWriter."""
    writer = ParquetWriter(str(tmp_path))
    date_val = date.today()
    partition_dir = writer._get_partition_path("test", date_val)
    legacy_file = partition_dir / "test_legacy.parquet"
    legacy_file.write_text("not a parquet file")

    writer.write_record("test", {"val": 1})
    writer.flush("test")


def test_file_writer_rotation_logic(tmp_path: Path):
    """Cover file rotation in FileWriter."""
    writer = FileWriter(str(tmp_path))
    writer.write("TEST", "line 1")

    # Force rotation by changing current date
    writer._current_date = date(2000, 1, 1)
    writer.write("TEST", "line 2")
    assert writer._current_date == datetime.now().date()


def test_consumer_binary_blob_full_coverage(tmp_path: Path):
    """Cover BinaryChunk handling in SerialConsumer."""
    queue: Queue = Queue()
    mock_db = MagicMock()
    mock_router = MagicMock()
    mock_writer = MagicMock()

    consumer = SerialConsumer(queue, mock_db, mock_router, file_writer=mock_writer)

    # Send start, middle, end chunks
    queue.put(BinaryChunk(b"start", start=True))
    queue.put(BinaryChunk(b"middle"))
    queue.put(BinaryChunk(b"end", end=True))

    # Process them
    conn = MagicMock()
    mock_db.get_connection.return_value = conn

    # We'll run the loop processing logic manually or via brief start/stop
    def run_briefly():
        consumer.start()
        time.sleep(1.0)
        consumer.stop()

    t = threading.Thread(target=run_briefly)
    t.start()
    t.join()


def test_consumer_unexpected_queue_error(tmp_path: Path):
    """Cover unexpected Exception in queue.get."""
    queue: MagicMock = MagicMock()
    queue.get.side_effect = [Exception("Queue error"), Empty()]
    mock_db = MagicMock()
    mock_router = MagicMock()

    consumer = SerialConsumer(queue, mock_db, mock_router)
    # This will hit 223
    consumer._consume_loop()


def test_consumer_file_writer_exceptions(tmp_path: Path):
    """Cover Exception blocks in SerialConsumer when calling FileWriter."""

    queue: Queue = Queue()
    mock_db = MagicMock()
    mock_router = MagicMock()
    mock_fw = MagicMock()

    # Force exceptions in all FileWriter methods called by consumer
    mock_fw.write_record.side_effect = Exception("error")
    mock_fw.write.side_effect = Exception("error")
    mock_fw.write_error.side_effect = Exception("error")
    mock_fw.write_invalid_record.side_effect = Exception("error")

    consumer = SerialConsumer(queue, mock_db, mock_router, file_writer=mock_fw)
    conn = MagicMock()

    # 1. Decode error path (354) -> write_error/write_record (367-382, 394-395)
    line_bytes = b"\xff\xff"  # Invalid ascii
    # 1. Decode error path (354) -> write_error/write_record (367-382, 394-395)
    line_bytes = b"\xff\xff"  # Invalid ascii

    # Ensure DB inserts don't fail, so we reach file writer code
    with patch("adcp_recorder.serial.consumer.insert_parse_error"):
        consumer._process_line(conn, line_bytes)

    # 2. Route success path (443) -> write/write_record (457-458, 471-472)
    mock_msg = MagicMock()
    mock_msg.to_dict.return_value = {"val": 1}
    mock_router.route.return_value = mock_msg

    # We need _store_parsed_message to succeed or just mock it?
    # It is called at 443. We want to reach 456.
    # Note: _store_parsed_message catches its own exceptions.
    with patch("adcp_recorder.serial.consumer.insert_raw_line"):
        consumer._process_line(conn, b"$PNORI,data\r\n")

    # 3. Parse error path (475) -> write_invalid_record/write_record (496-497, 509-510, 524-525)
    mock_router.route.side_effect = ValueError("parse fail")
    with patch("adcp_recorder.serial.consumer.insert_parse_error"):
        consumer._process_line(conn, b"$PNORI,bad\r\n")

    # 4. Route success but writer fails in _store_parsed_message (540-541)
    mock_router.route.side_effect = None
    mock_router.route.return_value = mock_msg
    mock_fw.write_record.side_effect = Exception("parquet fail")
    consumer._store_parsed_message(conn, "$PNORI,data", "PNORI", mock_msg)


def test_parquet_writer_schema_alignment_failure(tmp_path: Path):
    """Cover Exception in _write_to_parquet schema alignment (212-215)."""
    writer = ParquetWriter(str(tmp_path))
    date_val = date.today()
    existing_path = (
        tmp_path / "parquet" / "ALIGN_FAIL" / f"date={date_val.isoformat()}" / "ALIGN_FAIL.parquet"
    )
    existing_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a file with a column that will cause cast failure
    pl.DataFrame({"val": [1, 2]}).write_parquet(existing_path)

    # Try to write a record with a string that can't be cast to int
    # We need to mock polars cast to fail specifically for this column
    writer.write_record("ALIGN_FAIL", {"val": "not_an_int"})
    writer.flush("ALIGN_FAIL")


def test_consumer_loop_exceptions(tmp_path: Path):
    """Cover Exception blocks in _consume_loop."""
    queue: Queue = Queue()
    mock_db = MagicMock()
    mock_router = MagicMock()
    mock_fw = MagicMock()
    mock_fw.flush_stale.side_effect = Exception("flush fail")

    consumer = SerialConsumer(queue, mock_db, mock_router, file_writer=mock_fw)

    # 1. Empty queue but flush_stale fails (219-220)
    # We'll just run one iteration of the loop by putting an item then stopping
    consumer._running = True

    def stop_later():
        time.sleep(0.1)
        consumer._running = False

    threading.Thread(target=stop_later).start()
    consumer._consume_loop()  # This will hit Empty, then flush_stale (which fails)


def test_consumer_robust_error_logging(tmp_path: Path):
    """Cover additional try-except blocks in SerialConsumer."""

    queue: Queue = Queue()
    mock_writer = MagicMock()
    mock_db = MagicMock()
    mock_router = MessageRouter()

    # Force failures in writer methods
    mock_writer.write_error.side_effect = Exception("Log failure")
    mock_writer.write_record.side_effect = Exception("Parquet failure")
    mock_writer.flush_stale.side_effect = Exception("Flush failure")

    with (
        patch("adcp_recorder.serial.consumer.logger"),
        patch(
            "adcp_recorder.serial.consumer.insert_velocity_data",
            side_effect=Exception("Insert failure"),
        ),
        patch(
            "adcp_recorder.serial.consumer.insert_pnora_data",
            side_effect=Exception("Insert failure"),
        ),
        patch(
            "adcp_recorder.serial.consumer.insert_pnorb_data",
            side_effect=Exception("Insert failure"),
        ),
        patch(
            "adcp_recorder.serial.consumer.insert_pnore_data",
            side_effect=Exception("Insert failure"),
        ),
        patch(
            "adcp_recorder.serial.consumer.insert_pnorf_data",
            side_effect=Exception("Insert failure"),
        ),
        patch(
            "adcp_recorder.serial.consumer.insert_pnori_configuration",
            side_effect=Exception("Insert failure"),
        ),
        patch(
            "adcp_recorder.serial.consumer.insert_sensor_data",
            side_effect=Exception("Insert failure"),
        ),
        patch(
            "adcp_recorder.serial.consumer.insert_pnorw_data",
            side_effect=Exception("Insert failure"),
        ),
        patch(
            "adcp_recorder.serial.consumer.insert_pnorwd_data",
            side_effect=Exception("Insert failure"),
        ),
        patch(
            "adcp_recorder.serial.consumer.insert_header_data",
            side_effect=Exception("Insert failure"),
        ),
    ):
        consumer = SerialConsumer(queue, mock_db, mock_router, file_writer=mock_writer)

        record_types = [
            "PNORI",
            "PNORS",
            "PNORC",
            "PNORH",
            "PNORW",
            "PNORB",
            "PNORE",
            "PNORF",
            "PNORWD",
            "PNORA",
        ]

        for rt in record_types:
            mock_msg = MagicMock()
            mock_msg.record_type = rt
            mock_msg.to_dict.return_value = {"received_at": 1.0, "data": 1}
            with patch.object(mock_router, "route", return_value=mock_msg):
                queue.put(f"${rt},data\r\n".encode("ascii"))

        # Trigger second try-except in _process_line
        queue.put(b"\xff\xff\r\n")

        def run_briefly():
            consumer.start()
            time.sleep(2.0)
            consumer.stop()

        t = threading.Thread(target=run_briefly)
        t.start()
        t.join()


def test_table_view_coverage_gaps():
    """Cover missing lines in table_view.py (128, 139, 146-147)."""

    mock_st = MagicMock()

    def side_effect(n):
        count = n if isinstance(n, int) else len(cast(Sized, n))
        return [MagicMock() for _ in range(count)]

    mock_st.columns.side_effect = side_effect

    # Hit 128 and 146-147
    source = DataSource(
        "test",
        "Test",
        [
            ColumnMetadata("received_at", ColumnType.TIMESTAMP, False),
            ColumnMetadata("measurement_datetime", ColumnType.TIMESTAMP, False),
        ],
        10,
        True,
        "received_at",
    )
    mock_dl = MagicMock()
    mock_dl.get_source_metadata.return_value = source
    mock_dl.query_data.return_value = [{"received_at": 1.0}]

    # Second call to render_table_view will hit index fallback (146-147) and 128
    with patch("adcp_recorder.ui.components.table_view.st", mock_st):
        render_table_view(mock_dl, "test", default_time_range="invalid_range")

    # Hit 139: fallback when no known ts cols are present
    source_no_ts = DataSource(
        "test", "Test", [ColumnMetadata("val", ColumnType.NUMERIC, False)], 10, True, "val"
    )
    mock_dl.get_source_metadata.return_value = source_no_ts
    mock_dl.query_data.return_value = ["not a dict"]

    with patch("adcp_recorder.ui.components.table_view.st", mock_st):
        render_table_view(mock_dl, "test")


def test_data_layer_final_gaps(tmp_path: Path):
    """Cover lines 957-958 in data_layer.py and minor gaps in parquet_data_layer."""
    from adcp_recorder.ui.data_layer import DataLayer
    from adcp_recorder.ui.parquet_data_layer import ParquetDataLayer

    # 1. data_layer.py 957-958: Trigger exception in get_quality_metrics
    mock_conn = MagicMock()
    # Mock get_source_metadata to return a valid source for parse_errors
    mock_source = MagicMock(spec=DataSource)
    mock_source.name = "parse_errors"
    mock_source.has_timestamp = True
    mock_source.timestamp_column = "received_at"

    with (
        patch.object(DataLayer, "get_available_sources", return_value=[]),
        patch.object(DataLayer, "get_source_metadata", return_value=mock_source),
    ):
        dl = DataLayer(mock_conn)
        # First call succeeds
        mock_conn.execute.return_value.fetchone.return_value = (100,)
        metrics = dl.get_quality_metrics()
        assert metrics["error_count"] == 100

        # Second call fails (hits except block)
        mock_conn.execute.return_value.fetchone.side_effect = Exception("Metrics failure")
        metrics = dl.get_quality_metrics()
        # Should not have error_count or it remains what it was?
        # Actually it returns a new metrics dict with total_records: 0
        assert "error_count" not in metrics

    # 2. parquet_data_layer.py gaps (574, 862, 869, 877)
    conn = MagicMock()
    with patch("adcp_recorder.ui.parquet_data_layer.duckdb.connect", return_value=conn):
        pdl = ParquetDataLayer(str(tmp_path))

        # Hit 574: load_data with a 'time' column to trigger measurement_time creation
        # We need to mock get_file_structure/scan to return some files
        mock_struct = MagicMock()
        mock_struct.record_types = {"TEST": {date.today(): [Path("test.parquet")]}}
        mock_struct.get_files_for_selection.return_value = [Path("test.parquet")]

        with patch.object(pdl, "get_file_structure", return_value=mock_struct):
            # Mock DESCRIBE to return a 'time' column but no 'measurement_time'
            conn.execute.return_value.fetchall.side_effect = [
                # First call: DESCRIBE base_view
                [("time", "VARCHAR", "YES", None, None, None)],
                # Second call: COUNT(*)
                [(100,)],
            ]
            pdl.load_data(["TEST"])

        # Hit duckdb.Error paths (862, 869, 877)
        # These lines are in _get_join_condition and _get_view_columns
        # We can trigger them by calling create_joined_views or
        # get_source_metadata with failing conn
        conn.execute.side_effect = duckdb.Error("Mock DuckDB Error")
        pdl._create_joined_views()
        pdl.get_source_metadata("test")
