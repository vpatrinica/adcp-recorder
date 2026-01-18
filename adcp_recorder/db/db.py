import logging
from pathlib import Path
from threading import local

import duckdb

from .schema import ALL_SCHEMA_SQL

logger = logging.getLogger(__name__)


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
            try:
                conn.execute(sql_statement)
            except Exception as e:
                # Log a warning instead of crashing. This is common when
                # existing tables have a different schema than expected by views.
                logger.warning(f"Schema initialization warning: {e}")

        conn.commit()
        self._schema_initialized = True

        # After structural schema is ready, attempt to link DuckLake (Parquet)
        self.initialize_ducklake()

    def initialize_ducklake(self) -> None:
        """Initialize DuckLake views pointing to Parquet files if they exist."""
        conn = self.get_connection()

        # We look for parquet files in the standard output directory
        # This assumes the DB is sibling to 'parquet' folder or we can derive it
        # Real implementation should probably get this from config
        base_path = Path(self.db_path).parent
        parquet_path = base_path / "parquet"

        if not parquet_path.exists():
            return

        logger.info(f"Initializing DuckLake views from {parquet_path}")

        # Register a view for each record type found in parquet folder
        try:
            for record_type_dir in parquet_path.iterdir():
                if record_type_dir.is_dir():
                    prefix = record_type_dir.name.lower()
                    view_name = f"view_{prefix}"
                    parquet_glob = str(record_type_dir / "**" / "*.parquet")

                    conn.execute(
                        f"CREATE OR REPLACE VIEW {view_name} "
                        f"AS SELECT * FROM read_parquet('{parquet_glob}')"
                    )
                    logger.debug(f"Created DuckLake view: {view_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize some DuckLake views: {e}")

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
