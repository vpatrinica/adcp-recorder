import runpy
from unittest.mock import MagicMock, PropertyMock, patch

import pytest


@pytest.fixture
def migration_utils():
    from adcp_recorder.db import migration

    return migration


# --- CLI and Service Main Execution Tests ---


def test_cli_main_execution():
    """Test executing adcp_recorder.cli.main as a script."""
    # We pass --help so it runs arguments parsing and exits with 0
    # Remove from sys.modules to avoid RuntimeWarning when runpy executes it
    import sys

    if "adcp_recorder.cli.main" in sys.modules:
        del sys.modules["adcp_recorder.cli.main"]
    if "adcp_recorder.cli" in sys.modules:
        del sys.modules["adcp_recorder.cli"]

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
            # Remove from sys.modules to avoid RuntimeWarning when runpy executes it
            import sys

            if "adcp_recorder.service.supervisor" in sys.modules:
                del sys.modules["adcp_recorder.service.supervisor"]
            if "adcp_recorder.service" in sys.modules:
                del sys.modules["adcp_recorder.service"]

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

    from adcp_recorder.serial.consumer import BinaryChunk, SerialConsumer

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
            if not getattr(side_effect, "called", False):
                setattr(side_effect, "called", True)
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
    from adcp_recorder.db.migration import get_old_table_exists

    exists = get_old_table_exists(mock_duckdb_conn, "some_table")
    assert exists is False


def test_get_table_row_count_exception(mock_duckdb_conn):
    """Test get_table_row_count exception handler."""
    mock_duckdb_conn.execute.side_effect = Exception("DB Error")
    from adcp_recorder.db.migration import get_table_row_count

    count = get_table_row_count(mock_duckdb_conn, "some_table")
    assert count == 0


def test_migrate_pnorw_fields_table_not_found(mock_duckdb_conn):
    """Test migrate_pnorw_fields when table doesn't exist."""
    mock_duckdb_conn.execute.return_value.fetchone.return_value = [0]
    from adcp_recorder.db.migration import migrate_pnorw_fields

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

    from adcp_recorder.db.migration import migrate_pnorw_fields

    migrate_pnorw_fields(mock_duckdb_conn)


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

    from adcp_recorder.db.migration import migrate_pnorw_fields

    with patch("adcp_recorder.db.migration.logger") as mock_logger:
        count = migrate_pnorw_fields(mock_duckdb_conn)
        assert count == 0
        mock_logger.info.assert_called_with("pnorw_data is empty, skipping migration")


def test_copy_existing_tables_missing_table(mock_duckdb_conn):
    """Test copy_existing_tables when source table is missing."""
    mock_duckdb_conn.execute.return_value.fetchone.return_value = [0]
    from adcp_recorder.db.migration import copy_existing_tables

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
        from adcp_recorder.db.migration import MigrationError, migrate_database

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
        patch(
            "sys.argv",
            ["migration.py", str(source), "--verify", "--target", "adcp_recorder/tests/tgt.db"],
        ),
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


@pytest.mark.filterwarnings(
    "ignore:'adcp_recorder.db.migration' found in sys.modules:RuntimeWarning"
)
def test_migration_main_block():
    """Test the if __name__ == '__main__': block using runpy using --help."""
    # Remove from sys.modules to avoid RuntimeWarning when runpy executes it
    import sys

    # Clean up all db-related modules for a fresh import
    modules_to_remove = [k for k in list(sys.modules.keys()) if k.startswith("adcp_recorder.db")]
    for mod in modules_to_remove:
        del sys.modules[mod]

    # We pass --help so it runs arguments parsing and exits with 0
    with patch("sys.argv", ["adcp_recorder/db/migration.py", "--help"]):
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_module("adcp_recorder.db.migration", run_name="__main__")
        assert excinfo.value.code == 0


# --- Config Coverage Tests ---


def test_config_get_default_config_dir_windows():
    """Test get_default_config_dir on Windows platform (lines 59-63)."""
    import importlib
    import sys

    # Remove cached modules to get fresh import
    modules_to_remove = [k for k in sys.modules.keys() if k.startswith("adcp_recorder.config")]
    for mod in modules_to_remove:
        del sys.modules[mod]

    # Now patch before importing
    with patch.dict("os.environ", {"PROGRAMDATA": "C:\\ProgramData"}, clear=False):
        with patch("sys.platform", "win32"):
            # Import fresh - this will use the patched sys.platform
            import adcp_recorder.config as config_module

            # Reload to ensure we use the patched value
            config_module = importlib.reload(config_module)

            # Now call the method
            config_dir = config_module.RecorderConfig.get_default_config_dir()
            # Should use ProgramData on Windows
            assert "ADCP-Recorder" in str(config_dir)
            assert "ProgramData" in str(config_dir)


def test_config_get_default_config_dir_windows_fallback():
    """Test get_default_config_dir on Windows with fallback path."""
    import importlib
    import os
    import sys

    # Remove cached modules to get fresh import
    modules_to_remove = [
        k for k in list(sys.modules.keys()) if k.startswith("adcp_recorder.config")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    # Remove PROGRAMDATA to test fallback
    env_without_programdata = {k: v for k, v in os.environ.items() if k != "PROGRAMDATA"}

    with patch.dict("os.environ", env_without_programdata, clear=True):
        with patch("sys.platform", "win32"):
            # Import fresh - this will use the patched sys.platform
            import adcp_recorder.config as config_module

            # Reload to ensure we use the patched value
            config_module = importlib.reload(config_module)

            # Now call the method
            config_dir = config_module.RecorderConfig.get_default_config_dir()
            # Should fallback to C:\ProgramData
            assert "ADCP-Recorder" in str(config_dir)
            assert "ProgramData" in str(config_dir)


def test_config_get_default_config_dir_linux():
    """Test get_default_config_dir on Linux platform (line 63)."""
    import importlib
    import sys

    # Remove cached modules to get fresh import
    modules_to_remove = [
        k for k in list(sys.modules.keys()) if k.startswith("adcp_recorder.config")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    # Patch to ensure not Windows
    with patch("sys.platform", "linux"):
        # Import fresh
        import adcp_recorder.config as config_module

        # Reload to ensure we use the patched value
        config_module = importlib.reload(config_module)

        # Now call the method
        config_dir = config_module.RecorderConfig.get_default_config_dir()
        # Should use home directory with CONFIG_DIR_NAME
        assert ".adcp-recorder" in str(config_dir)


# --- Migration Column Check Exception Test ---


def test_migrate_pnorw_fields_column_check_exception_handling(mock_duckdb_conn):
    """Test migrate_pnorw_fields exception during column check (lines 324-325)."""

    # Table exists
    def execute_side_effect(query, *args, **kwargs):
        m = MagicMock()
        if "information_schema.tables" in query:
            m.fetchone.return_value = [1]
            return m
        if "information_schema.columns" in query:
            # This triggers lines 324-325
            raise Exception("Column check failed")
        return m

    mock_duckdb_conn.execute.side_effect = execute_side_effect

    from adcp_recorder.db.migration import migrate_pnorw_fields

    # Should return 0 since old_schema becomes False due to exception
    count = migrate_pnorw_fields(mock_duckdb_conn)
    assert count == 0
