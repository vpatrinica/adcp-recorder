"""FIFO producer - reads from serial port and pushes to queue.

The producer runs in a separate thread, continuously reading from the serial
port and buffering lines to push to a FIFO queue for consumption by the parser.
"""

import logging
import threading
import time
from queue import Full, Queue

from adcp_recorder.core.nmea import is_binary_data
from adcp_recorder.serial.binary_chunk import BinaryChunk
from adcp_recorder.serial.port_manager import SerialConnectionManager

logger = logging.getLogger(__name__)


class SerialProducer:
    """Reads NMEA sentences from serial port and produces to FIFO queue.

    The producer runs in a background thread, reading lines from the serial port,
    buffering partial lines, detecting binary data, and pushing complete lines
    to a queue for consumption.

    Attributes:
        connection_manager: Serial connection manager
        queue: FIFO queue for pushing lines
        heartbeat_interval: Seconds between heartbeat updates
        max_queue_size: Maximum queue depth before dropping oldest

    Example:
        >>> manager = SerialConnectionManager('/dev/ttyUSB0')
        >>> queue = Queue(maxsize=1000)
        >>> producer = SerialProducer(manager, queue)
        >>> producer.start()
        >>> # ... later ...
        >>> producer.stop()
    """

    def __init__(
        self,
        connection_manager: SerialConnectionManager,
        queue: Queue,
        heartbeat_interval: float = 5.0,
        max_line_length: int = 1024,
    ):
        """Initialize serial producer.

        Args:
            connection_manager: Serial connection manager
            queue: Queue to push lines to
            heartbeat_interval: Seconds between heartbeat updates
            max_line_length: Maximum allowed line length (for safety)
        """
        self._connection_manager = connection_manager
        self._queue = queue
        self._heartbeat_interval = heartbeat_interval
        self._max_line_length = max_line_length

        self._running = False
        self._thread: threading.Thread | None = None
        self._last_heartbeat = time.time()
        self._line_buffer = b""
        self._blob_mode = False

    @property
    def is_running(self) -> bool:
        """Check if producer is running."""
        return self._running

    @property
    def last_heartbeat(self) -> float:
        """Get timestamp of last heartbeat update."""
        return self._last_heartbeat

    def start(self) -> None:
        """Start the producer thread."""
        if self._running:
            logger.warning("Producer already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        logger.info("Serial producer started")

    def stop(self) -> None:
        """Stop the producer thread gracefully."""
        if not self._running:
            return

        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        logger.info("Serial producer stopped")

    def _update_heartbeat(self) -> None:
        """Update heartbeat timestamp."""
        self._last_heartbeat = time.time()

    def _read_loop(self) -> None:
        """Main read loop (runs in thread)."""
        logger.info("Producer read loop starting")

        while self._running:
            # Ensure connection
            if not self._connection_manager.is_connected():
                logger.warning("Not connected, attempting reconnection...")
                if not self._connection_manager.reconnect(max_retries=3):
                    logger.error("Reconnection failed, waiting before retry")
                    time.sleep(5.0)
                    continue

            # Read data
            line_bytes = self._connection_manager.read_line(timeout=1.0)

            if line_bytes is None:
                # Timeout or error - continue
                continue

            if not line_bytes:
                # Empty line - continue
                continue

            # Check for binary data
            if is_binary_data(line_bytes):
                logger.warning(f"Binary data detected: {line_bytes[:50]}")
                # Enter blob mode and stream binary chunks to the consumer
                if not self._blob_mode:
                    self._blob_mode = True
                    chunk = BinaryChunk(data=line_bytes, start=True)
                else:
                    chunk = BinaryChunk(data=line_bytes)

                self._push_to_queue(chunk)
                self._update_heartbeat()
                continue

            # Decode and buffer
            try:
                line_str = line_bytes.decode("ascii").strip()
            except UnicodeDecodeError:
                logger.warning(f"Failed to decode ASCII: {line_bytes[:50]}")
                # Treat as binary (enter blob mode)
                if not self._blob_mode:
                    self._blob_mode = True
                    chunk = BinaryChunk(data=line_bytes, start=True)
                else:
                    chunk = BinaryChunk(data=line_bytes)

                self._push_to_queue(chunk)
                self._update_heartbeat()
                continue

            # Push complete line
            if line_str:
                # If we were in blob mode but now have a printable line, mark blob end
                if self._blob_mode:
                    # push explicit end marker then the recovered line
                    end_chunk = BinaryChunk(data=b"", end=True)
                    self._push_to_queue(end_chunk)
                    self._blob_mode = False

                self._push_to_queue(line_str.encode("ascii"))
                self._update_heartbeat()

        logger.info("Producer read loop exiting")

    def _push_to_queue(self, data: bytes) -> None:
        """Push data to queue, dropping oldest if full.

        Args:
            data: Line data to push (as bytes)
        """
        try:
            # Non-blocking put
            self._queue.put_nowait(data)
        except Full:
            # Queue is full - drop oldest and retry
            logger.warning("Queue full, dropping oldest item")
            try:
                self._queue.get_nowait()  # Remove oldest
                self._queue.put_nowait(data)  # Add new
            except Exception as e:
                logger.error(f"Failed to push to queue: {e}")
