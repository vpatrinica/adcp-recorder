"""File writer for exporting NMEA data to files."""

import logging
import os
from datetime import datetime
from typing import TextIO

logger = logging.getLogger(__name__)


class FileWriter:
    """Writes NMEA sentences to files with daily rotation.

    Maintains separate files for each message type (e.g. PNORI, PNORS).
    Rotates files daily based on the current date.
    """

    def __init__(self, base_path: str):
        """Initialize file writer.

        Args:
            base_path: Base directory to write files to
        """
        self.base_path = base_path
        self._files: dict[str, TextIO] = {}
        self._current_date = datetime.now().date()
        self._ensure_base_path()

    def _ensure_base_path(self) -> None:
        """Ensure base directory exists."""
        os.makedirs(self.base_path, exist_ok=True)

    def _get_filename(self, prefix: str) -> str:
        """Get filename for a message type and current date.

        Format: {prefix}_{YYYYMMDD}.nmea
        For errors: ERRORS_{YYYYMMDD}.log
        """
        date_str = self._current_date.strftime("%Y%m%d")
        return os.path.join(self.base_path, f"{prefix}_{date_str}.nmea")

    def _check_rotation(self) -> None:
        """Check if files need to be rotated (new day)."""
        now = datetime.now().date()
        if now != self._current_date:
            logger.info(f"Rotating files from {self._current_date} to {now}")
            self.close()
            self._current_date = now
            self._files = {}

    def _get_file_handle(self, prefix: str) -> TextIO:
        """Get or create file handle for message type."""
        self._check_rotation()

        if prefix not in self._files:
            filename = self._get_filename(prefix)
            self._files[prefix] = open(filename, "a", encoding="utf-8", buffering=1)
            logger.debug(f"Opened log file: {filename}")

        return self._files[prefix]

    def write(self, prefix: str, data: str) -> None:
        """Write data to file for message type.

        Args:
            prefix: Message type prefix (e.g. 'PNORI') or 'ERRORS'
            data: Data string to write (should include newlines if needed)
        """
        if not prefix or not data:
            return

        try:
            f = self._get_file_handle(prefix)
            f.write(data)
            if not data.endswith("\n"):
                f.write("\n")
            f.flush()
        except Exception as e:
            logger.error(f"Failed to write to file for {prefix}: {e}")

    def write_error(self, message: str) -> None:
        """Write error message to error log."""
        timestamp = datetime.now().isoformat()
        self.write("ERRORS", f"[{timestamp}] {message}")

    def close(self) -> None:
        """Close all open files."""
        for prefix, f in self._files.items():
            try:
                f.close()
            except Exception as e:
                logger.error(f"Error closing file for {prefix}: {e}")
        self._files.clear()
