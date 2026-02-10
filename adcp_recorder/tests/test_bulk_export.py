from pathlib import Path
from unittest.mock import patch

import duckdb

from adcp_recorder.export.bulk_export import BulkExporter


def test_bulk_exporter_init(tmp_path):
    db_path = str(tmp_path / "test.duckdb")
    out_path = str(tmp_path / "parquet")
    exporter = BulkExporter(db_path, out_path)
    assert exporter.db_path == db_path
    assert exporter.output_path == Path(out_path)
    assert exporter.table_map["pnore_data"] == "PNORE"


def test_bulk_exporter_db_not_found(tmp_path):
    db_path = str(tmp_path / "nonexistent.duckdb")
    out_path = str(tmp_path / "parquet")
    exporter = BulkExporter(db_path, out_path)
    stats = exporter.export_all()
    assert stats == {}


def test_bulk_exporter_export_all(tmp_path):
    db_path = str(tmp_path / "test.duckdb")
    out_path = str(tmp_path / "parquet")

    # Create a dummy DuckDB with some data
    conn = duckdb.connect(db_path)
    conn.execute(
        "CREATE TABLE pnore_data (val INTEGER, measurement_date DATE, measurement_time TIME)"
    )
    conn.execute("INSERT INTO pnore_data VALUES (1, '2023-01-01', '12:00:00')")
    conn.execute("INSERT INTO pnore_data VALUES (2, '2023-01-01', '12:01:00')")
    conn.execute("CREATE TABLE unmapped_table (val INTEGER)")
    conn.close()

    exporter = BulkExporter(db_path, out_path)

    # Mock ParquetWriter to avoid actual file writing issues or dependency complexity
    with patch("adcp_recorder.export.bulk_export.ParquetWriter") as mock_writer_cls:
        mock_writer_instance = mock_writer_cls.return_value
        exporter.writer = mock_writer_instance

        stats = exporter.export_all()

        assert stats["pnore_data"] == 2
        assert "unmapped_table" not in stats

        # Verify calls
        assert mock_writer_instance.write_record.call_count == 2
        mock_writer_instance.flush.assert_called_with("PNORE")
        mock_writer_instance.close.assert_called_once()


def test_bulk_exporter_export_table_empty(tmp_path):
    db_path = str(tmp_path / "test.duckdb")
    out_path = str(tmp_path / "parquet")
    conn = duckdb.connect(db_path)
    conn.execute("CREATE TABLE empty_table (val INTEGER)")
    conn.close()

    exporter = BulkExporter(db_path, out_path)
    conn = duckdb.connect(db_path, read_only=True)

    count = exporter.export_table(conn, "empty_table", "EMPTY")
    assert count == 0
    conn.close()


def test_bulk_exporter_progress_logging(tmp_path, caplog):
    db_path = str(tmp_path / "test.duckdb")
    out_path = str(tmp_path / "parquet")

    conn = duckdb.connect(db_path)
    conn.execute("CREATE TABLE large_table (val INTEGER)")
    # Insert enough rows to trigger the 10000 log message
    # We can't easily insert 10000 rows quickly without a loop or generate_series
    conn.execute("INSERT INTO large_table SELECT * FROM range(10001)")
    conn.close()

    exporter = BulkExporter(db_path, out_path)

    with patch("adcp_recorder.export.bulk_export.ParquetWriter"):
        import logging

        with caplog.at_level(logging.INFO):
            conn = duckdb.connect(db_path, read_only=True)
            exporter.export_table(conn, "large_table", "LARGE")
            conn.close()


def test_bulk_exporter_main():
    with patch("sys.argv", ["bulk_export.py", "--db", "test.db", "--out", "out_dir"]):
        with patch("adcp_recorder.export.bulk_export.BulkExporter") as mock_exporter_cls:
            mock_instance = mock_exporter_cls.return_value
            mock_instance.export_all.return_value = {"table1": 100}

            # Call main
            from adcp_recorder.export.bulk_export import main

            main()

            mock_exporter_cls.assert_called_with("test.db", "out_dir", buffer_size=10000)
            mock_instance.export_all.assert_called_once()


def test_bulk_exporter_script_execution():
    import subprocess
    import sys

    # Just run help to verify the script is executable
    result = subprocess.run(
        [sys.executable, "-m", "adcp_recorder.export.bulk_export", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout
