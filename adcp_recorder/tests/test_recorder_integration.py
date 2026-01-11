import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from adcp_recorder.config import RecorderConfig
from adcp_recorder.core.recorder import AdcpRecorder

def test_recorder_init():
    # Create temp dir
    with tempfile.TemporaryDirectory() as tmp_dir:
        config = RecorderConfig(
            serial_port="/dev/ttyUSB0",
            output_dir=tmp_dir,
            db_path=":memory:"
        )
        
        # We need to mock SerialConnectionManager because it might try to open port or validation?
        # SerialConnectionManager init doesn't open port.
        
        recorder = AdcpRecorder(config)
        
        assert recorder.connection_manager is not None
        assert recorder.producer is not None
        assert recorder.consumer is not None
        assert recorder.file_writer is not None
        assert recorder.router is not None
        
        # Verify router has registered parsers
        assert "PNORI" in recorder.router._parsers
        assert "PNORS" in recorder.router._parsers

def test_recorder_start_stop():
    with tempfile.TemporaryDirectory() as tmp_dir:
        config = RecorderConfig(
            serial_port="/dev/loop0", # Fake port
            output_dir=tmp_dir,
            db_path=":memory:"
        )
        
        recorder = AdcpRecorder(config)
        
        # Mock internal start/stop to avoid actual thread spawn or serial access issues in test env
        recorder.producer.start = MagicMock()
        recorder.consumer.start = MagicMock()
        recorder.producer.stop = MagicMock()
        recorder.consumer.stop = MagicMock()
        recorder.file_writer.close = MagicMock()
        recorder.db_manager.close = MagicMock()
        recorder.db_manager.initialize_schema = MagicMock()

        recorder.start()
        assert recorder.is_running
        recorder.producer.start.assert_called_once()

        recorder.stop()
        assert not recorder.is_running
        recorder.producer.stop.assert_called_once()
