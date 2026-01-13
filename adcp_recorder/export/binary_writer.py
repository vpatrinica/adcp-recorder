"""Binary blob writer: writes raw binary streams to timestamped .dat files.

This writer creates a dedicated `errors_binary` folder under the provided
base path and writes binary data into timestamped files with a sequential
identifier when multiple blobs start in the same second.
"""

import os
from datetime import UTC, datetime
from pathlib import Path


class BinaryBlobWriter:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.binary_dir = os.path.join(self.base_path, "errors_binary")
        Path(self.binary_dir).mkdir(parents=True, exist_ok=True)
        self._current_file = None
        self._current_filepath = None
        self._timestamp = None
        self._identifier = 0

    def _next_filepath(self) -> str:
        now = datetime.now(UTC)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        if self._timestamp != timestamp:
            self._timestamp = timestamp
            self._identifier = 1
        else:
            self._identifier += 1

        filename = f"{timestamp}_bin_{self._identifier:03d}.dat"
        return os.path.join(self.binary_dir, filename)

    def start_blob(self, initial_chunk: bytes) -> str:
        """Start a new binary blob file and write the initial chunk.

        Returns the path to the created file.
        """
        if self._current_file is not None:
            # If a blob was open, close it first
            self.finish_blob()

        path = self._next_filepath()
        f = open(path, "wb")
        f.write(initial_chunk)
        f.flush()

        self._current_file = f
        self._current_filepath = path

        return path

    def append_chunk(self, chunk: bytes) -> None:
        if self._current_file is None:
            # If append called without start, start a new blob
            self.start_blob(chunk)
            return

        self._current_file.write(chunk)
        self._current_file.flush()

    def finish_blob(self) -> str | None:
        """Finish current blob and close file. Returns path or None."""
        if self._current_file is None:
            return None

        try:
            self._current_file.flush()
            self._current_file.close()
        finally:
            path = self._current_filepath
            self._current_file = None
            self._current_filepath = None
            self._timestamp = None
            self._identifier = 0

        return path

    def close(self) -> None:
        """Close the writer and any open files."""
        self.finish_blob()
