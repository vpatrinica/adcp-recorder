"""Extra coverage tests for config.py."""

import json
from unittest.mock import patch

from adcp_recorder.config import RecorderConfig, get_default_serial_port


def test_default_serial_port_linux():
    """Cover line 39 in config.py."""
    with patch("sys.platform", "linux"):
        assert get_default_serial_port() == "/dev/ttyUSB0"


def test_load_missing_serial_port(tmp_path):
    """Cover line 116 in config.py.

    Triggers config.save() when loaded data is missing 'serial_port'.
    """
    config_dir = tmp_path / "conf"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True)

    # Create config file without serial_port
    with open(config_file, "w") as f:
        json.dump({"baudrate": 115200}, f)

    with patch.object(RecorderConfig, "get_config_path", return_value=config_file):
        config = RecorderConfig.load()
        assert config.serial_port == get_default_serial_port()

        # Verify it was saved with 'serial_port'
        with open(config_file) as f:
            data = json.load(f)
        assert "serial_port" in data
