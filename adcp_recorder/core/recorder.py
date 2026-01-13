import logging
import threading
import time
from pathlib import Path
from queue import Queue

from adcp_recorder.config import RecorderConfig
from adcp_recorder.db import DatabaseManager
from adcp_recorder.export.file_writer import FileWriter
from adcp_recorder.parsers import (
    PNORA,
    PNORB,
    PNORC,
    PNORC1,
    PNORC2,
    PNORC3,
    PNORC4,
    PNORE,
    PNORF,
    PNORH3,
    PNORH4,
    PNORI,
    PNORI1,
    PNORI2,
    PNORS,
    PNORS1,
    PNORS2,
    PNORS3,
    PNORS4,
    PNORW,
    PNORWD,
)
from adcp_recorder.serial.consumer import MessageRouter, SerialConsumer
from adcp_recorder.serial.port_manager import SerialConnectionManager
from adcp_recorder.serial.producer import SerialProducer

logger = logging.getLogger(__name__)


class AdcpRecorder:
    def __init__(self, config: RecorderConfig):
        self.config = config
        self.is_running = False
        self._stop_event = threading.Event()

        # Ensure output directory exists
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

        # Initialize database
        self.db_path = config.db_path or str(Path(config.output_dir) / "adcp.duckdb")
        self.db_manager = DatabaseManager(self.db_path)

        # Shared Queue
        self.queue = Queue(maxsize=1000)

        # Setup Connection Manager and Producer
        self.connection_manager = SerialConnectionManager(
            port=config.serial_port, baudrate=config.baudrate, timeout=config.timeout
        )

        self.producer = SerialProducer(connection_manager=self.connection_manager, queue=self.queue)

        # Setup File Writer
        self.file_writer = FileWriter(base_path=config.output_dir)

        # Setup Router and Consumer
        self.router = self._setup_router()

        self.consumer = SerialConsumer(
            queue=self.queue,
            db_manager=self.db_manager,
            router=self.router,
            file_writer=self.file_writer,
        )

    def _setup_router(self) -> MessageRouter:
        router = MessageRouter()

        # PNORI - Configuration
        router.register_parser("PNORI", PNORI)
        router.register_parser("PNORI1", PNORI1)
        router.register_parser("PNORI2", PNORI2)

        # PNORS - Sensor Data
        router.register_parser("PNORS", PNORS)
        router.register_parser("PNORS1", PNORS1)
        router.register_parser("PNORS2", PNORS2)
        router.register_parser("PNORS3", PNORS3)
        router.register_parser("PNORS4", PNORS4)

        # PNORC - Current Data
        router.register_parser("PNORC", PNORC)
        router.register_parser("PNORC1", PNORC1)
        router.register_parser("PNORC2", PNORC2)
        router.register_parser("PNORC3", PNORC3)
        router.register_parser("PNORC4", PNORC4)

        # PNORH - Header
        router.register_parser("PNORH3", PNORH3)
        router.register_parser("PNORH4", PNORH4)

        # Other
        router.register_parser("PNORA", PNORA)
        router.register_parser("PNORW", PNORW)
        router.register_parser("PNORB", PNORB)
        router.register_parser("PNORE", PNORE)
        router.register_parser("PNORF", PNORF)
        router.register_parser("PNORWD", PNORWD)

        return router

    def start(self):
        """Starts the recording process."""
        if self.is_running:
            logger.warning("Recorder is already running")
            return

        logger.info("Starting ADCP Recorder...")

        # Initialize database schema
        self.db_manager.initialize_schema()

        # Start components
        self.producer.start()
        self.consumer.start()

        self.is_running = True
        self._stop_event.clear()

        logger.info(
            f"Recording started. Port: {self.config.serial_port}, Output: {self.config.output_dir}"
        )

    def stop(self):
        """Stops the recording process."""
        if not self.is_running:
            return

        logger.info("Stopping ADCP Recorder...")

        self._stop_event.set()

        # Stop components in reverse order
        self.producer.stop()
        self.consumer.stop()

        # Give consumer thread time to fully exit and release file handles
        # This is especially important on Windows where file handles may be locked
        time.sleep(0.5)

        self.file_writer.close()
        self.db_manager.close()

        self.is_running = False
        logger.info("Recorder stopped")

    def run_blocking(self):
        """Runs the recorder and blocks until interrupted."""
        self.start()
        try:
            while not self._stop_event.is_set():
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()
