import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_DIR_NAME = ".adcp-recorder"
CONFIG_FILE_NAME = "config.json"


@dataclass
class RecorderConfig:
    """Configuration for the ADCP Recorder."""
    
    serial_port: str = "/dev/ttyUSB0"
    baudrate: int = 9600
    timeout: float = 1.0
    output_dir: str = str(Path.home() / "adcp_data")
    log_level: str = "INFO"
    
    # Database settings
    db_path: Optional[str] = None  # If None, will default to output_dir/adcp.duckdb

    @classmethod
    def get_default_config_dir(cls) -> Path:
        """Returns the default configuration directory path."""
        return Path.home() / CONFIG_DIR_NAME

    @classmethod
    def get_config_path(cls) -> Path:
        """Returns the full path to the configuration file."""
        return cls.get_default_config_dir() / CONFIG_FILE_NAME

    @classmethod
    def load(cls) -> "RecorderConfig":
        """Loads configuration from file or returns defaults if not found."""
        config_path = cls.get_config_path()
        
        if not config_path.exists():
            return cls()

        try:
            with open(config_path, "r") as f:
                data = json.load(f)
            # Filter out keys that might not be in the dataclass anymore
            # This is a basic way to handle schema evolution/extra keys
            valid_keys = cls.__annotations__.keys()
            filtered_data = {k: v for k, v in data.items() if k in valid_keys}
            return cls(**filtered_data)
        except (json.JSONDecodeError, OSError) as e:
            # Fallback to default if corrupted, maybe log warning in future
            print(f"Warning: Could not load config, using defaults. Error: {e}")
            return cls()

    def save(self) -> None:
        """Saves current configuration to file."""
        config_path = self.get_config_path()
        config_dir = config_path.parent
        
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
            
        with open(config_path, "w") as f:
            json.dump(asdict(self), f, indent=4)

    def update(self, **kwargs: Any) -> None:
        """Updates configuration with provided values."""
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        self.save()
