"""Tests for various ADCP Recorder CLI commands."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from adcp_recorder.cli.main import cli


class TestCliCommands:
    """Tests for general CLI commands."""

    def test_list_ports(self):
        """Test list-ports command."""
        runner = CliRunner()
        mock_port1 = MagicMock(device="COM1", description="Port 1", hwid="VID:PID 1")
        mock_port2 = MagicMock(device="COM2", description="Port 2", hwid="VID:PID 2")

        with patch(
            "adcp_recorder.cli.main.list_serial_ports",
            return_value=[mock_port1, mock_port2],
        ):
            result = runner.invoke(cli, ["list-ports"])
            assert result.exit_code == 0
            assert "COM1" in result.output
            assert "COM2" in result.output

    def test_list_ports_empty(self):
        """Test list-ports command with no ports."""
        runner = CliRunner()
        with patch("adcp_recorder.cli.main.list_serial_ports", return_value=[]):
            result = runner.invoke(cli, ["list-ports"])
            assert result.exit_code == 0
            assert "No serial ports found." in result.output

    def test_configure(self, tmp_path):
        """Test configure command with various options."""
        runner = CliRunner()
        with patch("pathlib.Path.home", return_value=tmp_path):
            # Test full updates including debug
            result = runner.invoke(
                cli,
                [
                    "configure",
                    "--port",
                    "COM3",
                    "--baud",
                    "115200",
                    "--output",
                    "/tmp/data",
                    "--debug",
                ],
            )
            assert result.exit_code == 0
            assert "Configuration updated" in result.output
            assert "Port: COM3" in result.output
            assert "Baud: 115200" in result.output
            assert "Output: /tmp/data" in result.output
            assert "Level: DEBUG" in result.output

            # Test no-debug
            result = runner.invoke(cli, ["configure", "--no-debug"])
            assert "Level: INFO" in result.output

            # Test no changes
            result = runner.invoke(cli, ["configure"])
            assert "No changes specified." in result.output

    def test_status(self, tmp_path):
        """Test status command with OK paths."""
        runner = CliRunner()
        mock_config = MagicMock()
        mock_config.get_config_path.return_value = "/tmp/config.json"
        mock_config.serial_port = "COM1"
        mock_config.baudrate = 9600
        mock_config.output_dir = str(tmp_path)
        mock_config.log_level = "INFO"

        with patch("adcp_recorder.cli.main.RecorderConfig.load", return_value=mock_config):
            mock_port = MagicMock(device="COM1")
            with patch("adcp_recorder.cli.main.list_serial_ports", return_value=[mock_port]):
                result = runner.invoke(cli, ["status"])
                assert result.exit_code == 0
                assert "[OK] Output directory exists" in result.output
                assert "[OK] Serial port COM1 found" in result.output

    def test_generate_service(self, tmp_path):
        """Test generate-service command."""
        runner = CliRunner()
        # Mock adcp_recorder.templates file location
        with patch("adcp_recorder.templates.__file__", str(tmp_path / "__init__.py")):
            (tmp_path / "linux").mkdir(parents=True)
            (tmp_path / "linux" / "adcp-recorder.service").touch()

            result = runner.invoke(
                cli, ["generate-service", "--platform", "linux", "--out", str(tmp_path)]
            )
            assert result.exit_code == 0
            assert "Generated adcp-recorder.service" in result.output

    def test_generate_service_windows(self, tmp_path):
        """Test generate-service command for windows."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["generate-service", "--platform", "windows", "--out", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Generated install_service.bat" in result.output

    def test_start_mock(self):
        """Test start command (mocked)."""
        runner = CliRunner()
        with patch("adcp_recorder.cli.main.AdcpRecorder") as mock_recorder:
            # Mock run_blocking to return immediately
            mock_instance = mock_recorder.return_value

            result = runner.invoke(cli, ["start"])
            assert result.exit_code == 0
            assert "Starting recorder" in result.output
            mock_instance.run_blocking.assert_called_once()

    def test_generate_service_error(self, tmp_path):
        """Test generate-service error handling."""
        runner = CliRunner()
        # Mock shutil.copy to fail
        with patch("shutil.copy", side_effect=RuntimeError("Copy failure")):
            result = runner.invoke(
                cli, ["generate-service", "--platform", "linux", "--out", str(tmp_path)]
            )
            assert "Error generating template: Copy failure" in result.output

    def test_status_warnings(self, tmp_path):
        """Test status command with warning paths."""
        runner = CliRunner()
        mock_config = MagicMock()
        mock_config.get_config_path.return_value = "/tmp/config.json"
        mock_config.serial_port = "NONEXISTENT"
        mock_config.baudrate = 9600
        mock_config.output_dir = str(tmp_path / "nonexistent_dir")
        mock_config.log_level = "INFO"

        with patch("adcp_recorder.cli.main.RecorderConfig.load", return_value=mock_config):
            with patch("adcp_recorder.cli.main.list_serial_ports", return_value=[]):
                result = runner.invoke(cli, ["status"])
                assert result.exit_code == 0
                assert "[WARNING] Output directory does not exist" in result.output
                assert "[WARNING] Serial port NONEXISTENT not found" in result.output
