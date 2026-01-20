from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli():
    from adcp_recorder.cli.main import cli

    return cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_config(tmp_path):
    """Mocks config to use tmp path."""
    with patch("adcp_recorder.cli.main.RecorderConfig") as mock_config_cls:
        instance = MagicMock()
        instance.serial_port = "/dev/ttyUSB0"
        instance.baudrate = 9600
        instance.output_dir = str(tmp_path)
        instance.log_level = "INFO"
        instance.db_path = ":memory:"
        instance.get_config_path.return_value = str(tmp_path / "config.json")

        # Setup load() to return the mock instance
        mock_config_cls.load.return_value = instance

        yield mock_config_cls


def test_list_ports_empty(runner, cli):
    with patch("adcp_recorder.cli.main.list_serial_ports", return_value=[]):
        result = runner.invoke(cli, ["list-ports"])
        assert result.exit_code == 0
        assert "No serial ports found" in result.output


def test_list_ports_found(runner, cli):
    mock_port = MagicMock()
    mock_port.device = "/dev/ttyUSB0"
    mock_port.description = "FTDI Serial"
    mock_port.hwid = "12345"

    with patch("adcp_recorder.cli.main.list_serial_ports", return_value=[mock_port]):
        result = runner.invoke(cli, ["list-ports"])
        assert result.exit_code == 0
        assert "Found 1 ports" in result.output
        assert "/dev/ttyUSB0" in result.output


def test_configure_no_args(runner, mock_config, cli):
    result = runner.invoke(cli, ["configure"])
    assert result.exit_code == 0
    assert "No changes specified" in result.output
    assert "Current configuration" in result.output


def test_configure_update(runner, mock_config, cli):
    result = runner.invoke(cli, ["configure", "--port", "/dev/ttyS1", "--baud", "19200"])
    assert result.exit_code == 0

    # Check if update was called on the return value of load() (which is our mock instance)
    mock_config.load.return_value.update.assert_called_with(
        serial_port="/dev/ttyS1", baudrate=19200
    )
    assert "Configuration updated" in result.output


def test_start(runner, mock_config, cli):
    with patch("adcp_recorder.cli.main.AdcpRecorder") as mock_recorder_cls:
        result = runner.invoke(cli, ["start"])
        assert result.exit_code == 0
        assert "Starting recorder" in result.output

        mock_recorder_cls.assert_called_once()
        mock_recorder_cls.return_value.run_blocking.assert_called_once()


def test_status(runner, mock_config, cli):
    # Mock list_serial_ports for the check inside status
    with patch("adcp_recorder.cli.main.list_serial_ports", return_value=[]):
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "ADCP Recorder Status" in result.output
        assert "Serial Port:       /dev/ttyUSB0" in result.output
        # Since we returned empty ports list, it should warn
        assert "[WARNING] Serial port /dev/ttyUSB0 not found" in result.output
