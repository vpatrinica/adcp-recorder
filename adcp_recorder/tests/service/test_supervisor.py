import signal
import threading
import time
from unittest.mock import MagicMock, patch

import pytest
from adcp_recorder.config import RecorderConfig
from adcp_recorder.service.supervisor import ServiceSupervisor

@pytest.fixture
def mock_recorder():
    with patch('adcp_recorder.service.supervisor.AdcpRecorder') as MockRecorder:
         instance = MockRecorder.return_value
         instance.is_running = True
         yield instance

def test_supervisor_init_starts_recorder(mock_recorder):
    config = RecorderConfig()
    supervisor = ServiceSupervisor(config)
    
    # We mock run loops to avoid blocking
    with patch.object(supervisor, '_shutdown_event') as mock_event:
        mock_event.is_set.side_effect = [False, True] # Run once then stop
        
        supervisor.run()
        
        mock_recorder.start.assert_called_once()
        mock_recorder.stop.assert_called_once()

def test_signal_handling(mock_recorder):
    config = RecorderConfig()
    supervisor = ServiceSupervisor(config)
    
    # Simulate signal
    supervisor._handle_signal(signal.SIGTERM, None)
    
    assert supervisor._shutdown_event.is_set()

def test_supervisor_stops_on_recorder_crash(mock_recorder):
    config = RecorderConfig()
    supervisor = ServiceSupervisor(config)
    
    # Recorder is running first check, then not running
    mock_recorder.is_running = False 
    
    supervisor.run()
    
    # Should have stopped
    mock_recorder.stop.assert_called()
