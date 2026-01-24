"""File writer for exporting NMEA data to files."""

import logging
import os
from datetime import datetime
from typing import Any, TextIO

from adcp_recorder.export.parquet_writer import ParquetWriter

logger = logging.getLogger(__name__)


class FileWriter:
    """Writes NMEA sentences to files and structured records to Parquet.

    Maintains separate files for each message type and rotates daily.
    Also handles Parquet export for structured ADCP data.
    """

    def __init__(self, base_path: str):
        """Initialize file writer.

        Args:
            base_path: Base directory to write files to

        """
        self.base_path = base_path
        self._files: dict[str, TextIO] = {}
        self._current_date = datetime.now().date()
        self._closed = False
        self._ensure_base_path()
        self.parquet_writer = ParquetWriter(base_path)

    def _ensure_base_path(self) -> None:
        """Ensure base directory exists."""
        os.makedirs(self.base_path, exist_ok=True)

    def _get_filename(self, prefix: str) -> str:
        """Get filename for a message type and current date."""

        # Format: nmea/{prefix}/{prefix}_{YYYYMMDD}.nmea
        date_str = self._current_date.strftime("%Y%m%d")

        # Ensure directory exists
        file_dir = os.path.join(self.base_path, "nmea", prefix)
        os.makedirs(file_dir, exist_ok=True)

        return os.path.join(file_dir, f"{prefix}_{date_str}.nmea")

    def _check_rotation(self) -> None:
        """Check if files need to be rotated (new day)."""
        now = datetime.now().date()
        if now != self._current_date:
            logger.info(f"Rotating files from {self._current_date} to {now}")
            # Do not call self.close() here as it sets _closed=True
            # Instead, just close internal handles
            self._close_handles()
            self._current_date = now
            self._files = {}

    def _get_file_handle(self, prefix: str) -> TextIO | None:
        """Get or create file handle for message type."""
        if self._closed:
            return None

        self._check_rotation()

        if prefix not in self._files:
            filename = self._get_filename(prefix)
            try:
                self._files[prefix] = open(filename, "a", encoding="utf-8", buffering=1)
                logger.debug(f"Opened log file: {filename}")
            except OSError as e:
                logger.error(f"Failed to open log file {filename}: {e}")
                return None

        return self._files[prefix]

    def write(self, prefix: str, data: str) -> None:
        """Write data to file for message type.

        Args:
            prefix: Message type prefix (e.g. 'PNORI') or 'ERRORS'
            data: Data string to write (should include newlines if needed)

        """
        if self._closed or not prefix or not data:
            return

        try:
            f = self._get_file_handle(prefix)
            if f:
                f.write(data)
                if not data.endswith("\n"):
                    f.write("\n")
                f.flush()
        except Exception as e:
            logger.error(f"Failed to write to file for {prefix}: {e}")

    def write_record(self, prefix: str, record: dict[str, Any]) -> None:
        """Write structured record to Parquet.

        Args:
            prefix: Message type prefix
            record: Data dictionary

        """
        if self._closed:
            return

        try:
            self.parquet_writer.write_record(prefix, record)
        except Exception as e:
            logger.error(f"Failed to write record for {prefix} to Parquet: {e}")

    def write_invalid_record(self, prefix: str, data: str) -> None:
        """Write invalid record to error file.

        Args:
            prefix: Message type prefix
            data: Invalid data string

        """
        if self._closed or not prefix or not data:
            return

        try:
            date_str = self._current_date.strftime("%d%m%y")
            error_dir = os.path.join(self.base_path, "errors", "nmea")
            os.makedirs(error_dir, exist_ok=True)

            # Consolidate BINARY and unknown prefixes into ERROR_{date}.nmea
            # Known prefixes (PNORI, PNORS, etc.) use {prefix}_error_{date}.nmea
            known_prefixes = {
                "PNORI",
                "PNORS",
                "PNORC",
                "PNORH",
                "PNORW",
                "PNORB",
                "PNORE",
                "PNORF",
                "PNORWD",
                "PNORA",
            }
            if prefix == "BINARY" or prefix not in known_prefixes:
                filename = os.path.join(error_dir, f"ERROR_{date_str}.nmea")
            else:
                filename = os.path.join(error_dir, f"{prefix}_error_{date_str}.nmea")

            # Append to file
            # Note: For error files we open/close immediately to avoid keeping many handles open
            # This is less efficient but error rate should be low
            with open(filename, "a", encoding="utf-8", buffering=1) as f:
                f.write(data)
                if not data.endswith("\n"):
                    f.write("\n")
                f.flush()
        except Exception as e:
            logger.error(f"Failed to write invalid record for {prefix}: {e}")

    def write_error(self, message: str) -> None:
        """Write error message to error log."""
        timestamp = datetime.now().isoformat()
        self.write_invalid_record("SYSTEM", f"[{timestamp}] {message}")

    def _close_handles(self) -> None:
        """Close all open file handles."""
        for prefix, f in self._files.items():
            try:
                f.close()
            except Exception as e:
                logger.error(f"Error closing file for {prefix}: {e}")

    def close(self) -> None:
        """Close all open files and writers."""
        self._closed = True
        self._close_handles()
        self._files.clear()

        try:
            self.parquet_writer.close()
        except Exception as e:
            logger.error(f"Error closing parquet writer: {e}")
