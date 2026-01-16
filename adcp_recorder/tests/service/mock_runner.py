import sys
from unittest.mock import MagicMock, patch

# Mock AdcpRecorder and RecorderConfig before importing supervisor logic if possible,
# or patch where it is used.
# Since we import supervisor, it imports AdcpRecorder.
# We need to patch 'adcp_recorder.service.supervisor.AdcpRecorder'


def run_mock_service():
    """Runs the supervisor main loop with mocked internals."""
    # Create the mock
    mock_recorder = MagicMock()
    mock_recorder.is_running = True

    # We need to simulate running state
    def stop_recorder() -> None:
        mock_recorder.is_running = False

    mock_recorder.stop.side_effect = stop_recorder

    # Patch the class in the module
    # We must patch PRE-IMPORT or patch the module attribute after import
    with (
        patch("adcp_recorder.service.supervisor.AdcpRecorder", return_value=mock_recorder),
        patch("adcp_recorder.service.supervisor.RecorderConfig") as mock_conf_cls,
    ):
        # Setup config defaults
        mock_config = mock_conf_cls.load.return_value
        mock_config.log_level = "INFO"

        # Import and run
        from adcp_recorder.service.supervisor import main

        print("Mock Service Starting")
        sys.stdout.flush()
        main()
        print("Mock Service Clean Exit")


if __name__ == "__main__":
    run_mock_service()
