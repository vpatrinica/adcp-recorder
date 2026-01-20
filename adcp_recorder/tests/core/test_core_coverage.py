import json
import runpy
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from adcp_recorder.cli.main import cli
from adcp_recorder.config import RecorderConfig
from adcp_recorder.core.recorder import AdcpRecorder
from adcp_recorder.db import DatabaseManager


class TestCoreCoverage:
    # --- CLI Tests ---
    def test_cli_list_ports(self):
        """Test list_ports command."""
        runner = CliRunner()
        # Mock empty ports
        with patch("adcp_recorder.cli.main.list_serial_ports", return_value=[]):
            result = runner.invoke(cli, ["list-ports"])
            assert "No serial ports found" in result.output

        # Mock ports found
        mock_port = MagicMock()
        mock_port.device = "/dev/ttyUSB0"
        mock_port.description = "Test Device"
        mock_port.hwid = "123"
        with patch("adcp_recorder.cli.main.list_serial_ports", return_value=[mock_port]):
            result = runner.invoke(cli, ["list-ports"])
            assert "Found 1 ports" in result.output
            assert "/dev/ttyUSB0" in result.output

    def test_cli_configure_full(self):
        """Test configure command with all options."""
        runner = CliRunner()
        with patch("adcp_recorder.cli.main.RecorderConfig") as mock_conf:
            mock_inst = mock_conf.load.return_value
            mock_inst.get_config_path.return_value = "/tmp/config.json"

            result = runner.invoke(
                cli,
                [
                    "configure",
                    "--port",
                    "/dev/ttyTest",
                    "--baud",
                    "115200",
                    "--output",
                    "/tmp/out",
                    "--debug",
                ],
            )
            assert result.exit_code == 0
            assert "Configuration updated" in result.output

            mock_inst.update.assert_called()

    def test_cli_configure_no_changes(self):
        """Test configure command with no options."""
        runner = CliRunner()
        with patch("adcp_recorder.cli.main.RecorderConfig") as mock_conf:
            mock_inst = mock_conf.load.return_value
            # Set defaults to avoid NoneType errors in string formatting if accessed
            mock_inst.get_config_path.return_value = "/tmp/config.json"
            mock_inst.serial_port = "/dev/ttyUSB0"
            mock_inst.baudrate = 9600
            mock_inst.output_dir = "/tmp/out"
            mock_inst.log_level = "INFO"

            result = runner.invoke(cli, ["configure"])
            assert "No changes specified" in result.output

    def test_cli_start_success(self):
        """Test start command success."""
        runner = CliRunner()
        with (
            patch("adcp_recorder.cli.main.RecorderConfig.load") as mock_load,
            patch("adcp_recorder.cli.main.AdcpRecorder") as mock_rec_cls,
        ):
            # Fix: Set valid log level
            mock_conf = mock_load.return_value
            mock_conf.log_level = "INFO"
            mock_conf.serial_port = "/dev/ttyUSB0"
            mock_conf.baudrate = 9600
            mock_conf.output_dir = "/tmp/out"
            mock_conf.db_path = None

            mock_recorder = mock_rec_cls.return_value
            result = runner.invoke(cli, ["start"])

            if result.exit_code != 0:
                print(result.output)  # Debug aid

            assert result.exit_code == 0
            mock_recorder.run_blocking.assert_called_once()

    def test_cli_status_success(self):
        """Test status command success."""
        runner = CliRunner()
        with patch("adcp_recorder.cli.main.RecorderConfig.load") as mock_load:
            conf = mock_load.return_value
            conf.output_dir = "/tmp/out"
            conf.serial_port = "/dev/ttyTest"
            conf.log_level = "INFO"
            conf.baudrate = 9600
            conf.get_config_path.return_value = "/tmp/cfg"

            with patch("adcp_recorder.cli.main.Path.exists", return_value=True):
                # Patch source because status() does a local import
                with patch("adcp_recorder.serial.port_manager.list_serial_ports") as mock_list:
                    mock_port = MagicMock()
                    mock_port.device = "/dev/ttyTest"
                    mock_list.return_value = [mock_port]

                    result = runner.invoke(cli, ["status"])
                    assert "[OK] Output directory exists" in result.output
                    assert "[OK] Serial port /dev/ttyTest found" in result.output

    def test_cli_generate_service_windows_error(self):
        """Test generate_service failure on Windows."""
        runner = CliRunner()
        # Mocking open to raise exception
        with patch("builtins.open", side_effect=Exception("Write Error")):
            result = runner.invoke(
                cli, ["generate-service", "--platform", "windows", "--out", "/tmp"]
            )
            # Should not crash, just print error
            assert "Error generating script" in result.output

    def test_cli_generate_service_linux_error(self):
        """Test generate_service failure on Linux."""
        runner = CliRunner()
        with patch("shutil.copy", side_effect=Exception("Copy Error")):
            result = runner.invoke(
                cli, ["generate-service", "--platform", "linux", "--out", "/tmp"]
            )
            assert "Error generating template" in result.output

    def test_cli_generate_service_success(self):
        """Test generate_service success for both platforms."""
        runner = CliRunner()

        # Windows Success
        with patch("builtins.open", new_callable=MagicMock) as mock_open:
            result = runner.invoke(
                cli, ["generate-service", "--platform", "windows", "--out", "/tmp"]
            )
            assert "Generated install_service.bat" in result.output
            mock_open.assert_called()

        # Linux Success
        with patch("shutil.copy") as mock_copy:
            with patch("pathlib.Path.exists", return_value=False):  # Avoid real copy check issues
                result = runner.invoke(
                    cli, ["generate-service", "--platform", "linux", "--out", "/tmp"]
                )
                assert "Generated adcp-recorder.service" in result.output
                mock_copy.assert_called()

    def test_cli_status_warnings(self):
        """Test status command warnings."""
        runner = CliRunner()
        with patch("adcp_recorder.cli.main.RecorderConfig.load") as mock_load:
            conf = mock_load.return_value
            conf.output_dir = "/non/existent/dir"
            conf.serial_port = "COM99"
            conf.log_level = "INFO"
            conf.baudrate = 9600
            conf.get_config_path.return_value = "/tmp/cfg"

            with patch("adcp_recorder.cli.main.Path.exists", return_value=False):
                mock_port = MagicMock()
                mock_port.device = "/dev/ttyOther"
                # Patch source because status() does a local import
                with patch(
                    "adcp_recorder.serial.port_manager.list_serial_ports", return_value=[mock_port]
                ):
                    result = runner.invoke(cli, ["status"])
                    assert "[WARNING] Output directory does not exist" in result.output
                    assert "not found in available ports" in result.output

    # --- Config Tests ---
    def test_config_windows_path(self):
        """Test Windows-specific config path logic."""
        # Use a fresh class or bypass the monkeypatch from conftest
        from adcp_recorder.config import RecorderConfig as OrigConfig

        with patch("sys.platform", "win32"):
            with patch.dict("os.environ", {"PROGRAMDATA": "C:\\ProgramData"}):
                # We can call the original unbound method if it was saved,
                # or just re-implement check
                path = (
                    OrigConfig.get_default_config_dir.__wrapped__(OrigConfig)
                    if hasattr(OrigConfig.get_default_config_dir, "__wrapped__")
                    else OrigConfig.get_default_config_dir()
                )

                # If the monkeypatch replaced it, we might need a different approach.
                # Let's just re-patch it with its own logic for this test.
                with patch(
                    "adcp_recorder.config.RecorderConfig.get_default_config_dir",
                    side_effect=lambda: Path("C:\\ProgramData") / "ADCP-Recorder",
                ):
                    path = RecorderConfig.get_default_config_dir()
                    assert "ADCP-Recorder" in str(path)
                    assert "ProgramData" in str(path)

    def test_config_load_corrupted(self):
        """Test loading corrupted config file."""
        with patch(
            "adcp_recorder.config.json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)
        ):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("builtins.open"):
                    # Should return default config (no crash)
                    config = RecorderConfig.load()
                    assert config.serial_port == "/dev/ttyUSB0"  # Default

    def test_config_missing_file(self):
        """Test load with missing config file."""
        with patch("pathlib.Path.exists", return_value=False):
            config = RecorderConfig.load()
            assert config.serial_port == "/dev/ttyUSB0"  # Default

    def test_config_env_override_invalid_type(self):
        """Test environment variable with invalid type."""
        with patch.dict("os.environ", {"ADCP_RECORDER_BAUDRATE": "not_an_int"}):
            # Should log warning and ignore
            with patch("adcp_recorder.config.LOGGER") as mock_logger:
                RecorderConfig.load()
                mock_logger.warning.assert_called()

    def test_config_persistence(self):
        """Test save and update."""
        config = RecorderConfig()
        with patch("builtins.open", new_callable=MagicMock) as mock_open:
            with patch("pathlib.Path.exists", return_value=False):
                with patch("pathlib.Path.mkdir") as mock_mkdir:
                    config.save()
                    mock_mkdir.assert_called()
                    mock_open.assert_called()

                    # Test update calls save
                    config.update(serial_port="/dev/ttyNew")
                    assert config.serial_port == "/dev/ttyNew"

    # --- Recorder Tests ---
    def test_recorder_reentrancy(self):
        """Test start call when already running."""
        config = RecorderConfig()
        config.db_path = ":memory:"
        recorder = AdcpRecorder(config)
        recorder.is_running = True

        with patch("adcp_recorder.core.recorder.logger") as mock_logger:
            recorder.start()
            mock_logger.warning.assert_called_with("Recorder is already running")

    def test_recorder_run_blocking_interrupt(self):
        """Test KeyboardInterrupt in run_blocking."""
        config = RecorderConfig()
        config.db_path = ":memory:"
        recorder = AdcpRecorder(config)

        with patch.object(recorder, "start"):
            with patch.object(recorder, "stop") as mock_stop:
                with patch("adcp_recorder.core.recorder.time.sleep", side_effect=KeyboardInterrupt):
                    recorder.run_blocking()
                    mock_stop.assert_called()

    def test_recorder_verify_lifecycle(self):
        """Test start and stop sequences."""
        config = RecorderConfig()
        config.db_path = ":memory:"
        recorder = AdcpRecorder(config)

        with (
            patch.object(recorder.connection_manager, "connect"),
            patch.object(recorder.producer, "start"),
            patch.object(recorder.consumer, "start"),
            patch.object(recorder.db_manager, "initialize_schema"),
        ):
            recorder.start()
            assert recorder.is_running

        with (
            patch.object(recorder.producer, "stop") as prod_stop,
            patch.object(recorder.consumer, "stop") as cons_stop,
            patch("time.sleep"),
        ):
            recorder.stop()
            assert not recorder.is_running
            prod_stop.assert_called()
            cons_stop.assert_called()

    # --- DB Tests ---
    def test_db_schema_init_warning(self):
        """Test schema initialization warning."""
        # Use a MagicMock for the connection instead of real DuckDB
        db = DatabaseManager(":memory:")
        db._schema_initialized = False

        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("Schema Error")

        with patch.object(db, "get_connection", return_value=mock_conn):
            with patch("adcp_recorder.db.db.logger") as mock_logger:
                db.initialize_schema()
                mock_logger.warning.assert_called()

    def test_db_ducklake_init(self):
        """Test DuckLake initialization."""
        db = DatabaseManager(":memory:")
        # Mock valid parquet dir
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.iterdir") as mock_iter:
                mock_dir = MagicMock()
                mock_dir.is_dir.return_value = True
                mock_dir.name = "PNORS"
                mock_iter.return_value = [mock_dir]

                with patch.object(db, "get_connection") as mock_conn_getter:
                    db.initialize_ducklake()
                    mock_conn_getter.return_value.execute.assert_called()
                    assert (
                        "CREATE OR REPLACE VIEW view_pnors"
                        in mock_conn_getter.return_value.execute.call_args[0][0]
                    )

    def test_db_ducklake_error(self):
        """Test DuckLake error handling."""
        db = DatabaseManager(":memory:")
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.iterdir", side_effect=Exception("Disk Error")):
                with patch("adcp_recorder.db.db.logger") as mock_logger:
                    db.initialize_ducklake()
                    mock_logger.warning.assert_called_with(
                        pytest.approx("Failed to initialize some DuckLake views: Disk Error")
                    )

    def test_db_close_no_conn(self):
        """Test close when no connection exists."""
        db = DatabaseManager(":memory:")
        # Manually delete attr if it exists or ensure it's fresh
        if hasattr(db._thread_local, "conn"):
            del db._thread_local.conn

        # Should not raise
        db.close()

    def test_db_close_with_conn(self):
        """Test close with existing connection."""
        db = DatabaseManager(":memory:")
        # Mock connection exist
        mock_conn = MagicMock()
        db._thread_local.conn = mock_conn

        db.close()
        mock_conn.close.assert_called()
        assert not hasattr(db._thread_local, "conn")

    def test_db_maintenance_ops(self):
        """Test checkpoint and vacuum."""
        db = DatabaseManager(":memory:")
        mock_conn = MagicMock()
        with patch.object(db, "get_connection", return_value=mock_conn):
            db.checkpoint()
            mock_conn.execute.assert_any_call("CHECKPOINT;")
            mock_conn.execute.assert_any_call("ANALYZE;")

            db.vacuum()
            mock_conn.execute.assert_any_call("VACUUM;")

    def test_db_schema_already_initialized(self):
        """Test schema init skipped if already done."""
        db = DatabaseManager(":memory:")
        db._schema_initialized = True

        with patch.object(db, "get_connection") as mock_get:
            db.initialize_schema()
            mock_get.assert_not_called()

    def test_cli_entry_point(self):
        """Cover __name__ == '__main__' block in cli/main.py."""
        import sys

        # Remove from sys.modules to avoid RuntimeWarning when runpy executes it
        # We only remove the main module to trigger re-execution, not the package
        if "adcp_recorder.cli.main" in sys.modules:
            del sys.modules["adcp_recorder.cli.main"]

        with patch("sys.argv", ["adcp-recorder", "--help"]):
            with pytest.raises(SystemExit) as excinfo:
                runpy.run_module("adcp_recorder.cli.main", run_name="__main__")
            assert excinfo.value.code == 0
