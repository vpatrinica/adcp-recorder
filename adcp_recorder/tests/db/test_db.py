"""Tests for database manager and schema initialization."""

import pytest

from adcp_recorder.db import DatabaseManager


class TestDatabaseManager:
    """Test DatabaseManager initialization and schema creation."""

    def test_initialize_with_memory_database(self):
        """Test initialization with in-memory database."""
        db = DatabaseManager(":memory:")
        assert db.db_path == ":memory:"
        conn = db.get_connection()
        assert conn is not None

    def test_initialize_with_file_database(self, tmp_path):
        """Test initialization with file-based database."""
        db_path = tmp_path / "test.db"
        db = DatabaseManager(str(db_path))

        assert db.db_path == str(db_path)
        assert db_path.exists()

    def test_schema_creation_raw_lines_table(self):
        """Test that raw_lines table is created with correct schema."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Query table schema
        result = conn.execute(
            """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'raw_lines'
            ORDER BY ordinal_position
            """
        ).fetchall()

        column_names = [row[0] for row in result]

        assert "line_id" in column_names
        assert "received_at" in column_names
        assert "raw_sentence" in column_names
        assert "parse_status" in column_names
        assert "record_type" in column_names
        assert "checksum_valid" in column_names
        assert "error_message" in column_names

    def test_schema_creation_parse_errors_table(self):
        """Test that parse_errors table is created with correct schema."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Query table schema
        result = conn.execute(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'parse_errors'
            ORDER BY ordinal_position
            """
        ).fetchall()

        column_names = [row[0] for row in result]

        assert "error_id" in column_names
        assert "received_at" in column_names
        assert "raw_sentence" in column_names
        assert "error_type" in column_names
        assert "error_message" in column_names
        assert "attempted_prefix" in column_names
        assert "checksum_expected" in column_names
        assert "checksum_actual" in column_names

    def test_indexes_created(self):
        """Test that indexes are created."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Query indexes from DuckDB's system catalog
        # DuckDB uses duckdb_indexes() function
        result = conn.execute(
            """
            SELECT index_name 
            FROM duckdb_indexes()
            WHERE table_name IN ('raw_lines', 'parse_errors')
            """
        ).fetchall()

        index_names = [row[0] for row in result]

        # Check for expected indexes
        assert any("idx_raw_lines_received_at" in idx for idx in index_names)
        assert any("idx_raw_lines_record_type" in idx for idx in index_names)
        assert any("idx_raw_lines_parse_status" in idx for idx in index_names)
        assert any("idx_errors_received_at" in idx for idx in index_names)
        assert any("idx_errors_type" in idx for idx in index_names)

    def test_connection_reuse(self):
        """Test that get_connection returns the same connection for the same thread."""
        db = DatabaseManager(":memory:")

        conn1 = db.get_connection()
        conn2 = db.get_connection()

        assert conn1 is conn2

    def test_schema_initialization_idempotent(self):
        """Test that initialize_schema can be called multiple times without errors."""
        db = DatabaseManager(":memory:")

        # Call initialize multiple times
        db.initialize_schema()
        db.initialize_schema()
        db.initialize_schema()

        # Should not raise any errors
        conn = db.get_connection()
        result = conn.execute("SELECT COUNT(*) FROM raw_lines").fetchone()
        assert result[0] == 0

    def test_close_connection(self):
        """Test that close() properly closes the connection."""
        db = DatabaseManager(":memory:")
        _ = db.get_connection()

        # Close the connection
        db.close()

        # Getting connection again should create a new one
        new_conn = db.get_connection()
        assert new_conn is not None

    def test_checkpoint(self):
        """Test checkpoint operation."""
        db = DatabaseManager(":memory:")

        # Should not raise any errors
        db.checkpoint()

    def test_vacuum(self):
        """Test vacuum operation."""
        db = DatabaseManager(":memory:")

        # Should not raise any errors
        db.vacuum()


class TestDatabaseConstraints:
    """Test database constraints and validations."""

    def test_parse_status_constraint(self):
        """Test CHECK constraint on parse_status field."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Valid values should work
        conn.execute(
            """
            INSERT INTO raw_lines (line_id, raw_sentence, parse_status)
            VALUES (nextval('raw_lines_seq'), 'test', 'OK')
            """
        )
        conn.commit()

        conn.execute(
            """
            INSERT INTO raw_lines (line_id, raw_sentence, parse_status)
            VALUES (nextval('raw_lines_seq'), 'test', 'FAIL')
            """
        )
        conn.commit()

        conn.execute(
            """
            INSERT INTO raw_lines (line_id, raw_sentence, parse_status)
            VALUES (nextval('raw_lines_seq'), 'test', 'PENDING')
            """
        )
        conn.commit()

        # Invalid value should fail
        with pytest.raises(Exception):
            conn.execute(
                """
                INSERT INTO raw_lines (line_id, raw_sentence, parse_status)
                VALUES (nextval('raw_lines_seq'), 'test', 'INVALID')
                """
            )
            conn.commit()

    def test_not_null_constraints(self):
        """Test NOT NULL constraints."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Missing raw_sentence should fail
        with pytest.raises(Exception):
            conn.execute(
                """
                INSERT INTO raw_lines (line_id, parse_status)
                VALUES (nextval('raw_lines_seq'), 'OK')
                """
            )
            conn.commit()

        # Missing raw_sentence in parse_errors should fail
        with pytest.raises(Exception):
            conn.execute(
                """
                INSERT INTO parse_errors (error_id, error_type)
                VALUES (nextval('parse_errors_seq'), 'TEST')
                """
            )
            conn.commit()
