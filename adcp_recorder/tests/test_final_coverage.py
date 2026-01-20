import logging
import runpy
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import duckdb

from adcp_recorder.serial.consumer import SerialConsumer, BinaryChunk
from adcp_recorder.db.migration import (
    get_old_table_exists,
    get_table_row_count,
    migrate_pnorw_fields,
    copy_existing_tables,
    migrate_database,
    verify_migration,
)


# --- CLI and Service Main Execution Tests ---


def test_cli_main_execution():
    """Test executing adcp_recorder.cli.main as a script."""
    # We pass --help so it runs arguments parsing and exits with 0
    with patch("sys.argv", ["main.py", "--help"]):
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_module("adcp_recorder.cli.main", run_name="__main__")
        assert excinfo.value.code == 0


def test_supervisor_main_execution():
    """Test executing adcp_recorder.service.supervisor as a script."""
    # We patch the AdcpRecorder at the source so it gets picked up by the import in supervisor.py
    # We make start() raise an exception so the supervisor loop crashes and calls sys.exit(1)
    # avoiding an infinite loop.
    with (
        patch("sys.argv", ["supervisor.py"]),
        patch("adcp_recorder.core.recorder.AdcpRecorder") as mock_recorder_cls,
    ):
        mock_instance = mock_recorder_cls.return_value
        mock_instance.start.side_effect = RuntimeError("Force Crash")

        # Also need to patch config load to avoid file issues
        with patch("adcp_recorder.config.RecorderConfig.load"):
            with pytest.raises(SystemExit) as excinfo:
                runpy.run_module("adcp_recorder.service.supervisor", run_name="__main__")
            assert excinfo.value.code == 1


def test_supervisor_main_function():
    """Test the main() function in supervisor directly."""
    with (
        patch("adcp_recorder.service.supervisor.RecorderConfig.load"),
        patch("adcp_recorder.service.supervisor.ServiceSupervisor") as mock_supervisor_cls,
    ):
        from adcp_recorder.service.supervisor import main

        main()

        mock_supervisor_cls.return_value.run.assert_called_once()


# --- Serial Consumer Coverage Tests ---


def test_consumer_loop_outer_exception_handling():
    """Test the outer exception handler in _consume_loop (lines 241-242)."""
    mock_queue = MagicMock()

    # We must NOT raise from queue.get because it escapes the loop (bug/feature).
    # We must raise from within the processing block, e.g. BinaryChunk access.

    consumer = SerialConsumer(mock_queue, MagicMock(), MagicMock())
    consumer._running = True

    # Malicious chunk that raises on access
    malicious_item = MagicMock(spec=BinaryChunk)
    # The code checks `isinstance(item, BinaryChunk)`.
    # Then accesses `item.start`. We make that raise.
    type(malicious_item).start = PropertyMock(side_effect=Exception("Triggering line 241-242"))

    def side_effect(*args, **kwargs):
        if consumer._running:
            # First call: return malicious item
            if not hasattr(side_effect, "called"):
                side_effect.called = True
                return malicious_item

            # Second call: stop loop
            consumer._running = False
            from queue import Empty

            raise Empty
        from queue import Empty

        raise Empty

    mock_queue.get.side_effect = side_effect

    with patch("adcp_recorder.serial.consumer.logger") as mock_logger:
        consumer._consume_loop()

        # Verify log called
        assert mock_logger.error.call_count >= 1
        found = any(
            "Triggering line 241-242" in str(call[0][0])
            for call in mock_logger.error.call_args_list
        )
        assert found


from unittest.mock import PropertyMock


# --- DB Migration Coverage Tests ---


@pytest.fixture
def mock_duckdb_conn():
    with patch("duckdb.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        yield mock_conn


def test_get_old_table_exists_exception(mock_duckdb_conn):
    """Test get_old_table_exists exception handler."""
    mock_duckdb_conn.execute.side_effect = Exception("DB Error")
    exists = get_old_table_exists(mock_duckdb_conn, "some_table")
    assert exists is False


def test_get_table_row_count_exception(mock_duckdb_conn):
    """Test get_table_row_count exception handler."""
    mock_duckdb_conn.execute.side_effect = Exception("DB Error")
    count = get_table_row_count(mock_duckdb_conn, "some_table")
    assert count == 0


def test_migrate_pnorw_fields_table_not_found(mock_duckdb_conn):
    """Test migrate_pnorw_fields when table doesn't exist."""
    mock_duckdb_conn.execute.return_value.fetchone.return_value = [0]
    with patch("adcp_recorder.db.migration.logger") as mock_logger:
        count = migrate_pnorw_fields(mock_duckdb_conn)
        assert count == 0
        mock_logger.info.assert_called_with("pnorw_data table not found, skipping migration")


def test_migrate_pnorw_fields_column_check_exception(mock_duckdb_conn):
    """Test migrate_pnorw_fields exception during column check."""

    def execute_side_effect(query, *args, **kwargs):
        m = MagicMock()
        if "information_schema.tables" in query:
            m.fetchone.return_value = [1]
            return m
        if "information_schema.columns" in query:
            raise Exception("Metadata Error")
        return m

    mock_duckdb_conn.execute.side_effect = execute_side_effect
    count = migrate_pnorw_fields(mock_duckdb_conn)
    assert count == 0


def test_migrate_pnorw_fields_empty_table(mock_duckdb_conn):
    """Test migrate_pnorw_fields with empty table."""

    def execute_side_effect(query, *args, **kwargs):
        m = MagicMock()
        if "information_schema.tables" in query:
            m.fetchone.return_value = [1]
        elif "information_schema.columns" in query:
            m.fetchone.return_value = ["mean_dir"]
        elif "SELECT COUNT(*)" in query:
            m.fetchone.return_value = [0]
        return m

    mock_duckdb_conn.execute.side_effect = execute_side_effect

    with patch("adcp_recorder.db.migration.logger") as mock_logger:
        count = migrate_pnorw_fields(mock_duckdb_conn)
        assert count == 0
        mock_logger.info.assert_called_with("pnorw_data is empty, skipping migration")


def test_copy_existing_tables_missing_table(mock_duckdb_conn):
    """Test copy_existing_tables when source table is missing."""
    mock_duckdb_conn.execute.return_value.fetchone.return_value = [0]
    counts = copy_existing_tables(mock_duckdb_conn)
    assert all(c == 0 for c in counts.values())


def test_migrate_database_exception_handler(tmp_path):
    """Test migrate_database generic exception handler."""
    source = tmp_path / "source.db"
    source.touch()

    # We must patch something INSIDE the try block (e.g. create_new_schema)
    # duckdb.connect is outside the try block (found during debugging)

    # Patch connect to succeed
    with (
        patch("duckdb.connect"),
        patch(
            "adcp_recorder.db.migration.create_new_schema", side_effect=Exception("Schema Error")
        ),
    ):
        from adcp_recorder.db.migration import MigrationError

        with pytest.raises(MigrationError) as excinfo:
            migrate_database(source)
        assert "Migration failed: Schema Error" in str(excinfo.value)


def test_migration_main_verification(tmp_path):
    """Test migration.py main() execution via direct call to allow patching."""
    source = tmp_path / "source.db"
    source.touch()

    with (
        patch(
            "adcp_recorder.db.migration.migrate_database", return_value={"table": 10}
        ) as mock_migrate,
        patch(
            "adcp_recorder.db.migration.verify_migration", return_value={"table": 10}
        ) as mock_verify,
        patch("sys.argv", ["migration.py", str(source), "--verify", "--target", "tgt.db"]),
    ):
        from adcp_recorder.db.migration import main

        main()

        mock_migrate.assert_called_once()
        mock_verify.assert_called_once()


def test_migration_main_inplace(tmp_path):
    """Test migration.py main() with in-place flag."""
    source = tmp_path / "source.db"
    source.touch()

    with (
        patch("adcp_recorder.db.migration.migrate_database", return_value={}) as mock_migrate,
        patch("sys.argv", ["migration.py", str(source), "-i", "-v"]),
        patch("adcp_recorder.db.migration.verify_migration", return_value={}),
    ):
        from adcp_recorder.db.migration import main

        main()

        args, kwargs = mock_migrate.call_args
        assert kwargs["in_place"] is True


def test_migration_main_block():
    """Test the if __name__ == '__main__': block using runpy using --help."""
    # We pass --help so it runs arguments parsing and exits with 0
    with patch("sys.argv", ["adcp_recorder/db/migration.py", "--help"]):
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_module("adcp_recorder.db.migration", run_name="__main__")
        assert excinfo.value.code == 0
