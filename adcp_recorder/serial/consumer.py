"""FIFO consumer - pulls from queue, routes to parsers, stores to database.

The consumer runs in a separate thread, pulling lines from the FIFO queue,
routing them to appropriate parsers, and storing parsed data to the database.
"""

import logging
import threading
import time
from queue import Empty, Queue
from typing import Any, Callable, Dict, Optional, Type

import duckdb

from adcp_recorder.core.nmea import extract_prefix, is_binary_data
from adcp_recorder.db import (
    DatabaseManager,
    insert_parse_error,
    insert_pnori_configuration,
    insert_raw_line,
    insert_sensor_data,
    insert_velocity_data,
    insert_header_data,
    insert_pnorw_data,
    insert_pnorb_data,
    insert_pnorf_data,
    insert_pnorwd_data,
    insert_pnora_data,
    insert_echo_data,
)

logger = logging.getLogger(__name__)


class MessageRouter:
    """Routes NMEA sentences to appropriate parsers.

    Maps NMEA prefixes (e.g., 'PNORI', 'PNORS') to parser classes.
    """

    def __init__(self):
        """Initialize message router with empty registry."""
        self._parsers: Dict[str, Type] = {}

    def register_parser(self, prefix: str, parser_class: Type) -> None:
        """Register a parser for a message type.

        Args:
            prefix: NMEA prefix (e.g., 'PNORI')
            parser_class: Parser class with from_nmea() classmethod

        Example:
            >>> from adcp_recorder.parsers import PNORI
            >>> router = MessageRouter()
            >>> router.register_parser('PNORI', PNORI)
        """
        self._parsers[prefix.upper()] = parser_class
        logger.debug(f"Registered parser for {prefix}")

    def route(self, sentence: str) -> Optional[Any]:
        """Route sentence to appropriate parser.

        Args:
            sentence: NMEA sentence string

        Returns:
            Parsed message object or None if parser not found

        Raises:
            ValueError: If parsing fails
        """
        prefix = extract_prefix(sentence)
        if prefix is None:
            return None

        prefix = prefix.upper()
        if prefix not in self._parsers:
            return None

        parser_class = self._parsers[prefix]
        return parser_class.from_nmea(sentence)


class SerialConsumer:
    """Consumes NMEA sentences from queue, parses, and stores to database.

    The consumer runs in a background thread, pulling lines from the queue,
    routing them to parsers, and inserting parsed data to the database.

    Attributes:
        queue: FIFO queue to consume from
        db_manager: Database manager
        router: Message router
        heartbeat_interval: Seconds between heartbeat updates

    Example:
        >>> from adcp_recorder.parsers import PNORI
        >>> queue = Queue(maxsize=1000)
        >>> db = DatabaseManager(':memory:')
        >>> router = MessageRouter()
        >>> router.register_parser('PNORI', PNORI)
        >>> consumer = SerialConsumer(queue, db, router)
        >>> consumer.start()
        >>> # ... later ...
        >>> consumer.stop()
    """

    def __init__(
        self,
        queue: Queue,
        db_manager: DatabaseManager,
        router: MessageRouter,
        heartbeat_interval: float = 5.0,
    ):
        """Initialize serial consumer.

        Args:
            queue: Queue to consume from
            db_manager: Database manager
            router: Message router
            heartbeat_interval: Seconds between heartbeat updates
        """
        self._queue = queue
        self._db_manager = db_manager
        self._router = router
        self._heartbeat_interval = heartbeat_interval

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_heartbeat = time.time()

    @property
    def is_running(self) -> bool:
        """Check if consumer is running."""
        return self._running

    @property
    def last_heartbeat(self) -> float:
        """Get timestamp of last heartbeat update."""
        return self._last_heartbeat

    def start(self) -> None:
        """Start the consumer thread."""
        if self._running:
            logger.warning("Consumer already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._thread.start()
        logger.info("Serial consumer started")

    def stop(self) -> None:
        """Stop the consumer thread gracefully."""
        if not self._running:
            return

        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        logger.info("Serial consumer stopped")

    def _update_heartbeat(self) -> None:
        """Update heartbeat timestamp."""
        self._last_heartbeat = time.time()

    def _consume_loop(self) -> None:
        """Main consume loop (runs in thread)."""
        logger.info("Consumer loop starting")
        conn = self._db_manager.get_connection()

        while self._running:
            try:
                # Pull from queue with timeout
                line_bytes = self._queue.get(timeout=1.0)
            except Empty:
                # Queue empty - continue
                continue

            # Process line
            try:
                self._process_line(conn, line_bytes)
            except Exception as e:
                logger.error(f"Error processing line: {e}", exc_info=True)
                # Try to keep going
            
            self._update_heartbeat()

        logger.info("Consumer loop exiting")

    def _process_line(self, conn: duckdb.DuckDBPyConnection, line_bytes: bytes) -> None:
        """Process a single line from the queue.

        Args:
            conn: Database connection
            line_bytes: Line data as bytes
        """
        # Check for binary data
        if is_binary_data(line_bytes):
            logger.warning("Binary data in queue, logging to errors")
            insert_parse_error(
                conn,
                line_bytes.decode("ascii", errors="replace"),
                error_type="BINARY_DATA",
                error_message="Binary data detected",
            )
            insert_raw_line(
                conn,
                line_bytes.decode("ascii", errors="replace"),
                parse_status="FAIL",
                error_message="Binary data",
            )
            return

        # Decode to string
        try:
            sentence = line_bytes.decode("ascii").strip()
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode line: {e}")
            insert_parse_error(
                conn,
                line_bytes.decode("ascii", errors="replace"),
                error_type="DECODE_ERROR",
                error_message=str(e),
            )
            return

        if not sentence:
            return

        # Route to parser
        prefix = "UNKNOWN"
        try:
            # Extract prefix
            prefix = extract_prefix(sentence)
            
            parsed = self._router.route(sentence)
            
            if parsed is None:
                # Unknown message type
                logger.debug(f"Unknown message type: {prefix}")
                insert_raw_line(
                    conn,
                    sentence,
                    parse_status="PENDING",
                    record_type=prefix,
                    checksum_valid=None,
                    error_message=f"No parser for {prefix}",
                )
                return

            # Successfully parsed - insert to database
            self._store_parsed_message(conn, sentence, prefix, parsed)

            # Also insert to raw_lines
            insert_raw_line(
                conn,
                sentence,
                parse_status="OK",
                record_type=prefix,
                checksum_valid=True,
            )

        except ValueError as e:
            # Parse failed
            logger.warning(f"Parse failed for {prefix}: {e}")
            insert_parse_error(
                conn,
                sentence,
                error_type="PARSE_ERROR",
                error_message=str(e),
                attempted_prefix=prefix,
            )
            insert_raw_line(
                conn,
                sentence,
                parse_status="FAIL",
                record_type=prefix,
                error_message=str(e),
            )

    def _store_parsed_message(
        self, conn: duckdb.DuckDBPyConnection, sentence: str, prefix: str, parsed: Any
    ) -> None:
        """Store parsed message to appropriate table."""
        data = parsed.to_dict()
        if prefix in ("PNORI", "PNORI1", "PNORI2"):
            insert_pnori_configuration(conn, data, sentence)
        elif prefix in ("PNORS", "PNORS1", "PNORS2", "PNORS3", "PNORS4"):
            insert_sensor_data(conn, sentence, data)
        elif prefix in ("PNORC", "PNORC1", "PNORC2", "PNORC3", "PNORC4"):
            insert_velocity_data(conn, sentence, data)
        elif prefix in ("PNORH3", "PNORH4"):
            insert_header_data(conn, sentence, data)
        elif prefix == "PNORW":
            insert_pnorw_data(conn, sentence, data)
        elif prefix == "PNORB":
            insert_pnorb_data(conn, sentence, data)
        elif prefix == "PNORE":
            insert_echo_data(conn, sentence, data)
        elif prefix == "PNORF":
            insert_pnorf_data(conn, sentence, data)
        elif prefix == "PNORWD":
            insert_pnorwd_data(conn, sentence, data)
        elif prefix == "PNORA":
            insert_pnora_data(conn, sentence, data)
        else:
            logger.warning(f"No database insert for {prefix}")
