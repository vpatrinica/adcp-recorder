"""Serial port management for ADCP recorder.

Provides functionality for:
- Enumerating available serial ports
- Opening and managing serial connections
- Reconnection logic with exponential backoff
"""

import time
from dataclasses import dataclass

import serial
import serial.tools.list_ports


@dataclass(frozen=True)
class PortInfo:
    """Information about a serial port.

    Attributes:
        device: Device name (e.g., /dev/ttyUSB0 or COM3)
        description: Human-readable description
        hwid: Hardware ID string
    """

    device: str
    description: str
    hwid: str


def list_serial_ports() -> list[PortInfo]:
    """List all available serial ports on the system.

    Returns:
        List of PortInfo objects for each available port

    Example:
        >>> ports = list_serial_ports()
        >>> for port in ports:
        ...     print(f"{port.device}: {port.description}")
    """
    ports = []
    for port in serial.tools.list_ports.comports():
        ports.append(
            PortInfo(
                device=port.device,
                description=port.description or "Unknown",
                hwid=port.hwid or "Unknown",
            )
        )
    return ports


class SerialConnectionManager:
    """Manages serial port connections with reconnection logic.

    Provides reliable serial port connection with automatic reconnection
    using exponential backoff.

    Attributes:
        port: Serial port device name
        baudrate: Baud rate for communication
        timeout: Read timeout in seconds
        bytesize: Number of data bits
        parity: Parity setting
        stopbits: Number of stop bits

    Example:
        >>> manager = SerialConnectionManager('/dev/ttyUSB0', baudrate=115200)
        >>> if manager.connect():
        ...     line = manager.read_line()
        ...     manager.disconnect()
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        timeout: float = 1.0,
        bytesize: int = serial.EIGHTBITS,
        parity: str = serial.PARITY_NONE,
        stopbits: float = serial.STOPBITS_ONE,
    ):
        """Initialize serial connection manager.

        Args:
            port: Serial port device name
            baudrate: Baud rate (default: 115200)
            timeout: Read timeout in seconds (default: 1.0)
            bytesize: Number of data bits (default: 8)
            parity: Parity setting (default: None)
            stopbits: Number of stop bits (default: 1)
        """
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._bytesize = bytesize
        self._parity = parity
        self._stopbits = stopbits
        self._serial: serial.Serial | None = None

    @property
    def port(self) -> str:
        """Get port device name."""
        return self._port

    @property
    def baudrate(self) -> int:
        """Get baud rate."""
        return self._baudrate

    @property
    def timeout(self) -> float:
        """Get timeout."""
        return self._timeout

    @property
    def bytesize(self) -> int:
        """Get number of data bits."""
        return self._bytesize

    @property
    def parity(self) -> str:
        """Get parity setting."""
        return self._parity

    @property
    def stopbits(self) -> float:
        """Get number of stop bits."""
        return self._stopbits

    def connect(self) -> bool:
        """Open serial connection.

        Returns:
            True if connection successful, False otherwise
        """
        if self._serial is not None and self._serial.is_open:
            return True

        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                timeout=self._timeout,
                bytesize=self._bytesize,
                parity=self._parity,
                stopbits=self._stopbits,
            )
            return True
        except (serial.SerialException, OSError):
            self._serial = None
            return False

    def disconnect(self) -> None:
        """Close serial connection."""
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
        self._serial = None

    def is_connected(self) -> bool:
        """Check if serial connection is open.

        Returns:
            True if connected, False otherwise
        """
        return self._serial is not None and self._serial.is_open

    def reconnect(self, max_retries: int = 5, backoff_base: float = 2.0) -> bool:
        """Attempt to reconnect with exponential backoff.

        Args:
            max_retries: Maximum number of retry attempts
            backoff_base: Base for exponential backoff calculation

        Returns:
            True if reconnection successful, False if all retries exhausted

        Example:
            >>> manager = SerialConnectionManager('/dev/ttyUSB0')
            >>> if not manager.is_connected():
            ...     manager.reconnect(max_retries=3)
        """
        self.disconnect()

        for attempt in range(max_retries):
            if self.connect():
                return True

            # Exponential backoff
            wait_time = min(backoff_base**attempt, 60.0)  # Cap at 60 seconds
            time.sleep(wait_time)

        return False

    def read_line(self, timeout: float | None = None) -> bytes | None:
        """Read a single line from the serial port.

        Args:
            timeout: Optional timeout override (uses default if None)

        Returns:
            Line as bytes (including line terminator) or None if timeout/error

        Example:
            >>> manager = SerialConnectionManager('/dev/ttyUSB0')
            >>> manager.connect()
            >>> line = manager.read_line()
            >>> if line:
            ...     print(line.decode('ascii').strip())
        """
        if not self.is_connected():
            return None

        try:
            # Temporarily override timeout if specified
            if timeout is not None:
                old_timeout = self._serial.timeout
                self._serial.timeout = timeout

            line = self._serial.readline()

            # Restore original timeout
            if timeout is not None:
                self._serial.timeout = old_timeout

            return line if line else None

        except (serial.SerialException, OSError):
            self.disconnect()
            return None
