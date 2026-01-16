"""Tests for serial port management."""

from unittest.mock import MagicMock, Mock, patch

import serial

from adcp_recorder.serial import (
    PortInfo,
    SerialConnectionManager,
    list_serial_ports,
)


class TestListSerialPorts:
    """Test serial port enumeration."""

    def test_list_ports_returns_port_info(self):
        """Test that list_serial_ports returns PortInfo objects."""
        mock_port = MagicMock()
        mock_port.device = "/dev/ttyUSB0"
        mock_port.description = "USB Serial"
        mock_port.hwid = "USB VID:PID=0403:6001"

        with patch("serial.tools.list_ports.comports", return_value=[mock_port]):
            ports = list_serial_ports()

            assert len(ports) == 1
            assert isinstance(ports[0], PortInfo)
            assert ports[0].device == "/dev/ttyUSB0"
            assert ports[0].description == "USB Serial"
            assert ports[0].hwid == "USB VID:PID=0403:6001"

    def test_list_ports_handles_missing_description(self):
        """Test that missing description is handled gracefully."""
        mock_port = MagicMock()
        mock_port.device = "/dev/ttyUSB0"
        mock_port.description = None
        mock_port.hwid = "USB VID:PID=0403:6001"

        with patch("serial.tools.list_ports.comports", return_value=[mock_port]):
            ports = list_serial_ports()

            assert ports[0].description == "Unknown"

    def test_list_ports_handles_missing_hwid(self):
        """Test that missing hwid is handled gracefully."""
        mock_port = MagicMock()
        mock_port.device = "/dev/ttyUSB0"
        mock_port.description = "USB Serial"
        mock_port.hwid = None

        with patch("serial.tools.list_ports.comports", return_value=[mock_port]):
            ports = list_serial_ports()

            assert ports[0].hwid == "Unknown"

    def test_list_ports_empty(self):
        """Test listing ports when none are available."""
        with patch("serial.tools.list_ports.comports", return_value=[]):
            ports = list_serial_ports()

            assert len(ports) == 0
            assert isinstance(ports, list)


class TestSerialConnectionManager:
    """Test SerialConnectionManager."""

    def test_init_sets_properties(self):
        """Test that initialization sets properties correctly."""
        manager = SerialConnectionManager(
            "/dev/ttyUSB0",
            baudrate=9600,
            timeout=2.0,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_TWO,
        )

        assert manager.port == "/dev/ttyUSB0"
        assert manager.baudrate == 9600
        assert manager.timeout == 2.0
        assert manager.bytesize == serial.SEVENBITS
        assert manager.parity == serial.PARITY_EVEN
        assert manager.stopbits == serial.STOPBITS_TWO

    def test_init_uses_defaults(self):
        """Test that initialization uses default values."""
        manager = SerialConnectionManager("/dev/ttyUSB0")

        assert manager.baudrate == 115200
        assert manager.timeout == 1.0
        assert manager.bytesize == serial.EIGHTBITS
        assert manager.parity == serial.PARITY_NONE
        assert manager.stopbits == serial.STOPBITS_ONE

    def test_connect_success(self):
        """Test successful connection."""
        manager = SerialConnectionManager("/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = Mock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            result = manager.connect()

            assert result is True
            assert manager.is_connected()
            mock_serial.assert_called_once_with(
                port="/dev/ttyUSB0",
                baudrate=115200,
                timeout=1.0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )

    def test_connect_failure(self):
        """Test connection failure."""
        manager = SerialConnectionManager("/dev/nonexistent")

        with patch("serial.Serial", side_effect=serial.SerialException("Port not found")):
            result = manager.connect()

            assert result is False
            assert not manager.is_connected()

    def test_connect_already_connected(self):
        """Test connecting when already connected."""
        manager = SerialConnectionManager("/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = Mock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            # First connection
            manager.connect()

            # Second connection attempt (should return True without reopening)
            result = manager.connect()

            assert result is True
            # Serial should only be created once
            assert mock_serial.call_count == 1

    def test_disconnect(self):
        """Test disconnection."""
        manager = SerialConnectionManager("/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = Mock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            manager.connect()
            manager.disconnect()

            mock_instance.close.assert_called_once()
            assert not manager.is_connected()

    def test_disconnect_when_not_connected(self):
        """Test disconnecting when not connected."""
        manager = SerialConnectionManager("/dev/ttyUSB0")

        # Should not raise an error
        manager.disconnect()
        assert not manager.is_connected()

    def test_reconnect_success_first_try(self):
        """Test successful reconnection on first try."""
        manager = SerialConnectionManager("/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = Mock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            result = manager.reconnect(max_retries=3)

            assert result is True
            assert manager.is_connected()

    def test_reconnect_success_after_retries(self):
        """Test successful reconnection after a few retries."""
        manager = SerialConnectionManager("/dev/ttyUSB0")

        call_count = 0

        def connect_on_third_try(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise serial.SerialException("Connection failed")
            mock_instance = Mock()
            mock_instance.is_open = True
            return mock_instance

        with patch("serial.Serial", side_effect=connect_on_third_try):
            with patch("time.sleep"):  # Speed up test
                result = manager.reconnect(max_retries=5, backoff_base=2.0)

                assert result is True
                assert manager.is_connected()

    def test_reconnect_exhausts_retries(self):
        """Test reconnection when all retries are exhausted."""
        manager = SerialConnectionManager("/dev/ttyUSB0")

        with patch("serial.Serial", side_effect=serial.SerialException("Always fail")):
            with patch("time.sleep"):  # Speed up test
                result = manager.reconnect(max_retries=3, backoff_base=2.0)

                assert result is False
                assert not manager.is_connected()

    def test_reconnect_exponential_backoff(self):
        """Test that reconnect uses exponential backoff."""
        manager = SerialConnectionManager("/dev/ttyUSB0")

        sleep_times = []

        def track_sleep(duration) -> None:
            sleep_times.append(duration)

        with patch("serial.Serial", side_effect=serial.SerialException("Fail")):
            with patch("time.sleep", side_effect=track_sleep):
                manager.reconnect(max_retries=4, backoff_base=2.0)

                # Should have slept 4 times (after each failed attempt)
                assert len(sleep_times) == 4
                # Exponential backoff: 1, 2, 4, 8 seconds
                assert sleep_times[0] == 1.0  # 2^0
                assert sleep_times[1] == 2.0  # 2^1
                assert sleep_times[2] == 4.0  # 2^2
                assert sleep_times[3] == 8.0  # 2^3

    def test_reconnect_caps_backoff_at_60_seconds(self):
        """Test that backoff is capped at 60 seconds."""
        manager = SerialConnectionManager("/dev/ttyUSB0")

        sleep_times = []

        def track_sleep(duration) -> None:
            sleep_times.append(duration)

        with patch("serial.Serial", side_effect=serial.SerialException("Fail")):
            with patch("time.sleep", side_effect=track_sleep):
                manager.reconnect(max_retries=10, backoff_base=2.0)

                # Later retries should be capped at 60 seconds
                assert max(sleep_times) == 60.0

    def test_read_line_success(self):
        """Test reading a line successfully."""
        manager = SerialConnectionManager("/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = Mock()
            mock_instance.is_open = True
            mock_instance.readline.return_value = b"$PNORI,4,Test*2E\\r\\n"
            mock_serial.return_value = mock_instance

            manager.connect()
            line = manager.read_line()

            assert line == b"$PNORI,4,Test*2E\\r\\n"
            mock_instance.readline.assert_called_once()

    def test_read_line_timeout(self):
        """Test read_line when timeout occurs."""
        manager = SerialConnectionManager("/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = Mock()
            mock_instance.is_open = True
            mock_instance.readline.return_value = b""  # Empty = timeout
            mock_serial.return_value = mock_instance

            manager.connect()
            line = manager.read_line()

            assert line is None

    def test_read_line_not_connected(self):
        """Test read_line when not connected."""
        manager = SerialConnectionManager("/dev/ttyUSB0")

        line = manager.read_line()

        assert line is None

    def test_read_line_with_timeout_override(self):
        """Test read_line with custom timeout."""
        manager = SerialConnectionManager("/dev/ttyUSB0", timeout=1.0)

        with patch("serial.Serial") as mock_serial:
            mock_instance = Mock()
            mock_instance.is_open = True
            mock_instance.timeout = 1.0
            mock_instance.readline.return_value = b"$TEST*00\\r\\n"
            mock_serial.return_value = mock_instance

            manager.connect()
            line = manager.read_line(timeout=5.0)

            # Timeout should be set to 5.0 and restored to 1.0
            assert mock_instance.timeout == 1.0
            assert line == b"$TEST*00\\r\\n"

    def test_read_line_handles_serial_exception(self):
        """Test read_line handles SerialException by disconnecting."""
        manager = SerialConnectionManager("/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = Mock()
            mock_instance.is_open = True
            mock_instance.readline.side_effect = serial.SerialException("Read error")
            mock_serial.return_value = mock_instance

            manager.connect()
            line = manager.read_line()

            assert line is None
            assert not manager.is_connected()
