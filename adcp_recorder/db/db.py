"""Database management for DuckDB backend.

Provides database connection management, schema initialization, and thread-safe access.
"""

from pathlib import Path
from threading import local

import duckdb

from .schema import ALL_SCHEMA_SQL


class DatabaseManager:
    """Manages DuckDB database connections and schema initialization.

    Provides thread-safe connection pooling and automatic schema creation.
    Each thread gets its own connection via thread-local storage.

    Example:
        >>> db = DatabaseManager('./data/adcp_recorder.db')
        >>> conn = db.get_connection()
        >>> conn.execute("SELECT COUNT(*) FROM raw_lines")
    """

    def __init__(self, db_path: str = "./data/adcp_recorder.db", create_if_missing: bool = True):
        """Initialize database manager.

        Args:
            db_path: Path to DuckDB database file, or ':memory:'
                     for in-memory database
            create_if_missing: If True, create database file and parent
                               directories if they don't exist

        Raises:
            ValueError: If db_path is invalid or parent directory doesn't exist
                        and create_if_missing is False
        """
        self.db_path = db_path
        self._thread_local = local()
        self._schema_initialized = False

        # Create parent directory if needed
        if db_path != ":memory:" and create_if_missing:
            db_file = Path(db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize schema on first connection
        self.initialize_schema()

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get thread-local database connection.

        Returns a connection object that is unique to the calling thread.
        This ensures thread safety for multi-threaded applications.

        Returns:
            DuckDB connection object for the current thread
        """
        if not hasattr(self._thread_local, "conn"):
            self._thread_local.conn = duckdb.connect(self.db_path)
        return self._thread_local.conn

    def initialize_schema(self) -> None:
        """Create all required tables and indexes if they don't exist.

        This method is idempotent and safe to call multiple times.
        Uses IF NOT EXISTS clauses to avoid errors on existing tables.
        """
        if self._schema_initialized:
            return

        conn = self.get_connection()

        # Execute all schema creation statements
        for sql_statement in ALL_SCHEMA_SQL:
            conn.execute(sql_statement)

        conn.commit()
        self._schema_initialized = True

    def close(self) -> None:
        """Close all database connections.

        Closes the connection for the current thread if it exists.
        Should be called when shutting down the application or when
        the database manager is no longer needed.
        """
        if hasattr(self._thread_local, "conn"):
            self._thread_local.conn.close()
            delattr(self._thread_local, "conn")

    def checkpoint(self) -> None:
        """Perform checkpoint and optimize database.

        Forces a checkpoint to flush write-ahead log to disk and
        optimizes the database by analyzing tables for better query performance.
        """
        conn = self.get_connection()
        conn.execute("CHECKPOINT;")
        conn.execute("ANALYZE;")
        conn.commit()

    def vacuum(self) -> None:
        """Reclaim unused space in the database.

        Rebuilds the database file to reclaim space from deleted rows.
        This can be slow on large databases and should be run during
        low-activity periods.
        """
        conn = self.get_connection()
        conn.execute("VACUUM;")
        conn.commit()
