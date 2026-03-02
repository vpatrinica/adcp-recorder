import logging
import sys
from unittest.mock import patch

import pytest

from adcp_recorder.config import (
    CONFIG_DIR_NAME,
    CONFIG_FILE_NAME,
    RecorderConfig,
)


@pytest.fixture
def mock_config_path(tmp_path):
    """Mocks the config path to use a temporary directory."""
    config_dir = tmp_path / CONFIG_DIR_NAME
    config_file = config_dir / CONFIG_FILE_NAME

    with (
        patch.object(RecorderConfig, "get_default_config_dir", return_value=config_dir),
        patch.object(RecorderConfig, "get_config_path", return_value=config_file),
    ):
        yield config_file


def test_default_config():
    config = RecorderConfig()
    if sys.platform == "win32":
        assert config.serial_port == "COM6"
    else:
        assert config.serial_port == "/dev/ttyUSB0"
    assert config.baudrate == 9600
    assert config.timeout == 1.0
    # The autouse fixture in conftest.py sets ADCP_RECORDER_OUTPUT_DIR,
    # so the env var takes precedence over the platform default.
    assert "data" in config.output_dir


def test_load_non_existent(mock_config_path):
    # Should return default config if file doesn't exist
    config = RecorderConfig.load()
    if sys.platform == "win32":
        assert config.serial_port == "COM6"
    else:
        assert config.serial_port == "/dev/ttyUSB0"


def test_save_and_load(mock_config_path):
    config = RecorderConfig(serial_port="/dev/ttyUSB1", baudrate=115200)
    config.save()

    assert mock_config_path.exists()

    loaded_config = RecorderConfig.load()
    assert loaded_config.serial_port == "/dev/ttyUSB1"
    assert loaded_config.baudrate == 115200


def test_update(mock_config_path):
    config = RecorderConfig()
    config.update(serial_port="/dev/ttyUSB2", baudrate=4800)

    loaded_config = RecorderConfig.load()
    assert loaded_config.serial_port == "/dev/ttyUSB2"
    assert loaded_config.baudrate == 4800


def test_corrupted_config(mock_config_path, capsys):
    # Write invalid JSON
    mock_config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(mock_config_path, "w") as f:
        f.write("{invalid_json")

    config = RecorderConfig.load()
    # Should fall back to defaults
    if sys.platform == "win32":
        assert config.serial_port == "COM6"
    else:
        assert config.serial_port == "/dev/ttyUSB0"

    # Check if warning was printed
    captured = capsys.readouterr()
    assert "Warning: Could not load config" in captured.out


def test_env_overrides(mock_config_path, monkeypatch):
    # Persist a baseline config so load() reads from disk before applying env overrides
    baseline = RecorderConfig(
        serial_port="/dev/ttyUSB0",
        baudrate=9600,
        timeout=1.0,
        output_dir="/tmp/base",
        log_level="INFO",
        db_path=str(mock_config_path.parent / "base.duckdb"),
    )
    baseline.save()

    monkeypatch.setenv("ADCP_RECORDER_SERIAL_PORT", "/dev/ttyEnv")
    monkeypatch.setenv("ADCP_RECORDER_BAUDRATE", "19200")
    monkeypatch.setenv("ADCP_RECORDER_TIMEOUT", "2.5")
    monkeypatch.setenv("ADCP_RECORDER_OUTPUT_DIR", "/tmp/env")
    monkeypatch.setenv("ADCP_RECORDER_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("ADCP_RECORDER_DB_PATH", "/var/tmp/env.duckdb")

    loaded = RecorderConfig.load()

    assert loaded.serial_port == "/dev/ttyEnv"
    assert loaded.baudrate == 19200
    assert loaded.timeout == 2.5
    assert loaded.output_dir == "/tmp/env"
    assert loaded.log_level == "DEBUG"
    assert loaded.db_path == "/var/tmp/env.duckdb"


def test_invalid_env_override(monkeypatch, mock_config_path, caplog):
    baseline = RecorderConfig()
    baseline.save()

    monkeypatch.setenv("ADCP_RECORDER_BAUDRATE", "not-an-int")

    with caplog.at_level(logging.WARNING):
        loaded = RecorderConfig.load()

    assert "Ignoring ADCP_RECORDER_BAUDRATE" in caplog.text
    assert loaded.baudrate == baseline.baudrate


def test_windows_default_persistence(mock_config_path):
    """Verifies that on Windows, COM6 is defaulted and persisted if missing."""
    import json
    from adcp_recorder.config import RecorderConfig, get_default_serial_port

    with (
        patch("sys.platform", "win32"),
        patch.object(RecorderConfig, "get_config_path", return_value=mock_config_path),
    ):
        # Force re-evaluation of default port
        assert get_default_serial_port() == "COM6"

        # Load config when file doesn't exist
        # This will trigger config.save() which should use the mocked get_config_path()
        config = RecorderConfig.load()
        assert config.serial_port == "COM6"

        # Verify it was saved to disk
        assert mock_config_path.exists(), f"Config file not found at {mock_config_path}"

        with open(mock_config_path) as f:
            data = json.load(f)
        assert data["serial_port"] == "COM6"
