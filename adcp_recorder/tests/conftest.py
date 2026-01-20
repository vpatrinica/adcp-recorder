import os

import pytest

from adcp_recorder.config import RecorderConfig


@pytest.fixture(autouse=True)
def isolate_test_env(tmp_path, monkeypatch):
    """Ensure tests don't touch real user config or data.

    This redirects the config directory and default output directory to a
    temporary location for every test.
    """
    # Redirect config directory
    temp_config_dir = tmp_path / ".adcp-recorder"
    temp_config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(RecorderConfig, "get_default_config_dir", lambda: temp_config_dir)

    # Override the default output directory
    test_output_dir = str(tmp_path / "adcp_data")
    monkeypatch.setenv("ADCP_RECORDER_OUTPUT_DIR", test_output_dir)

    # Clear other environment variables that might interfere
    for env_var in list(os.environ.keys()):
        if env_var.startswith("ADCP_RECORDER_") and env_var != "ADCP_RECORDER_OUTPUT_DIR":
            monkeypatch.delenv(env_var, raising=False)

    return tmp_path
