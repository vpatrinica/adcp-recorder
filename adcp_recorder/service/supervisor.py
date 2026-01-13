import logging
import signal
import sys
import threading
import time

from adcp_recorder.config import RecorderConfig
from adcp_recorder.core.recorder import AdcpRecorder

logger = logging.getLogger(__name__)


class ServiceSupervisor:
    """Supervises the ADCP Recorder execution.

    Handles signal interception (SIGTERM, SIGINT) and ensures
    clean shutdown of the recorder components.
    """

    def __init__(self, config: RecorderConfig):
        self.config = config
        self.recorder = AdcpRecorder(config)
        self._shutdown_event = threading.Event()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle incoming signals."""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received signal {sig_name}, initiating shutdown...")
        self._shutdown_event.set()

    def run(self):
        """Run the service loop."""
        try:
            logger.info("Service supervisor starting...")
            self.recorder.start()

            # Monitoring loop
            while not self._shutdown_event.is_set():
                # Check health of components
                if not self.recorder.is_running:
                    logger.error("Recorder stopped unexpectedly!")
                    self._shutdown_event.set()
                    break

                # Check producer/consumer threads if accessible
                if hasattr(self.recorder, "producer") and not self.recorder.producer.is_running:
                    logger.warning("Producer thread is dead!")

                time.sleep(1.0)

        except Exception as e:
            logger.error(f"Service crashed: {e}", exc_info=True)
            sys.exit(1)
        finally:
            self._shutdown()

    def _shutdown(self):
        """Perform graceful shutdown."""
        logger.info("Service shutting down...")
        try:
            self.recorder.stop()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        logger.info("Service stopped.")


def main():
    """Entry point for the service."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    config = RecorderConfig.load()
    supervisor = ServiceSupervisor(config)
    supervisor.run()


if __name__ == "__main__":
    main()
