import json
from pathlib import Path
from unittest.mock import patch

import pytest
from adcp_recorder.config import RecorderConfig, CONFIG_DIR_NAME, CONFIG_FILE_NAME

@pytest.fixture
def mock_config_path(tmp_path):
    """Mocks the config path to use a temporary directory."""
    config_dir = tmp_path / CONFIG_DIR_NAME
    config_file = config_dir / CONFIG_FILE_NAME
    
    with patch.object(RecorderConfig, 'get_default_config_dir', return_value=config_dir), \
         patch.object(RecorderConfig, 'get_config_path', return_value=config_file):
        yield config_file

def test_default_config():
    config = RecorderConfig()
    assert config.serial_port == "/dev/ttyUSB0"
    assert config.baudrate == 9600
    assert config.timeout == 1.0
    assert "adcp_data" in config.output_dir

def test_load_non_existent(mock_config_path):
    # Should return default config if file doesn't exist
    config = RecorderConfig.load()
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
    assert config.serial_port == "/dev/ttyUSB0"
    
    # Check if warning was printed
    captured = capsys.readouterr()
    assert "Warning: Could not load config" in captured.out
