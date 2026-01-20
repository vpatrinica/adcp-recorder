import signal
from unittest.mock import PropertyMock, patch

import pytest

from adcp_recorder.config import RecorderConfig


@pytest.fixture
def service_supervisor():
    from adcp_recorder.service.supervisor import ServiceSupervisor

    return ServiceSupervisor


@pytest.fixture
def mock_recorder():
    with patch("adcp_recorder.service.supervisor.AdcpRecorder") as mock_recorder_cls:
        instance = mock_recorder_cls.return_value
        # Use side_effect to behave like a property if needed,
        # but simple attribute is usually enough
        # unless the code uses it in a loop condition.
        instance.is_running = True
        yield instance


def test_supervisor_init_starts_recorder(mock_recorder, service_supervisor):
    config = RecorderConfig()
    supervisor = service_supervisor(config)

    # Recorder is running first check, then not running
    with (
        patch(
            "adcp_recorder.service.supervisor.AdcpRecorder.is_running", new_callable=PropertyMock
        ) as mock_is_running,
        patch("time.sleep"),
    ):
        mock_is_running.side_effect = [True, False]

        supervisor.run()

        mock_recorder.start.assert_called_once()
        mock_recorder.stop.assert_called_once()


def test_signal_handling(mock_recorder, service_supervisor):
    config = RecorderConfig()
    supervisor = service_supervisor(config)

    # Simulate signal
    supervisor._handle_signal(signal.SIGTERM, None)

    assert supervisor._shutdown_event.is_set()


def test_supervisor_stops_on_recorder_crash(mock_recorder, service_supervisor):
    config = RecorderConfig()
    supervisor = service_supervisor(config)

    # Recorder is running first check, then not running
    mock_recorder.is_running = False

    supervisor.run()

    # Should have stopped
    mock_recorder.stop.assert_called()
