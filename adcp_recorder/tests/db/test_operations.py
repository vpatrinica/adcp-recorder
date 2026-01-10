"""Tests for database operations."""


from adcp_recorder.db import (
    DatabaseManager,
    insert_raw_line,
    batch_insert_raw_lines,
    insert_parse_error,
    update_raw_line_status,
    query_raw_lines,
    query_parse_errors,
)


class TestInsertOperations:
    """Test database insert operations."""

    def test_insert_raw_line(self):
        """Test inserting a single raw line."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        sentence = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E"
        line_id = insert_raw_line(conn, sentence, "OK", "PNORI", True, None)

        assert line_id > 0

        # Verify insertion
        result = conn.execute(
            "SELECT raw_sentence, parse_status, record_type FROM raw_lines WHERE line_id = ?",
            [line_id],
        ).fetchone()

        assert result[0] == sentence
        assert result[1] == "OK"
        assert result[2] == "PNORI"

    def test_insert_raw_line_with_defaults(self):
        """Test inserting raw line with default values."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        sentence = "$PNORI,4,Test*2E"
        line_id = insert_raw_line(conn, sentence)

        assert line_id > 0

        # Verify defaults
        result = conn.execute(
            "SELECT parse_status, record_type, checksum_valid FROM raw_lines WHERE line_id = ?",
            [line_id],
        ).fetchone()

        assert result[0] == "PENDING"
        assert result[1] is None
        assert result[2] is None

    def test_insert_raw_line_with_error(self):
        """Test inserting raw line with error message."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        sentence = "$INVALID*FF"
        error_msg = "Invalid checksum"
        line_id = insert_raw_line(conn, sentence, "FAIL", None, False, error_msg)

        assert line_id > 0

        # Verify error
        result = conn.execute(
            "SELECT error_message FROM raw_lines WHERE line_id = ?",
            [line_id],
        ).fetchone()

        assert result[0] == error_msg

    def test_batch_insert_raw_lines(self):
        """Test batch inserting multiple raw lines."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        records = [
            {
                "sentence": f"$PNORI,{i},Test*2E",
                "parse_status": "OK",
                "record_type": "PNORI",
                "checksum_valid": True,
                "error_message": None,
            }
            for i in range(10)
        ]

        count = batch_insert_raw_lines(conn, records)

        assert count == 10

        # Verify count in database
        result = conn.execute("SELECT COUNT(*) FROM raw_lines").fetchone()
        assert result[0] == 10

    def test_batch_insert_empty_list(self):
        """Test batch insert with empty list."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        count = batch_insert_raw_lines(conn, [])

        assert count == 0

    def test_insert_parse_error(self):
        """Test inserting a parse error."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        sentence = "$PNORI,4,Invalid*FF"
        error_id = insert_parse_error(
            conn,
            sentence,
            "CHECKSUM_FAILED",
            "Checksum mismatch",
            "PNORI",
            "2E",
            "FF",
        )

        assert error_id > 0

        # Verify insertion
        result = conn.execute(
            """
            SELECT raw_sentence, error_type, error_message, attempted_prefix,
                   checksum_expected, checksum_actual
            FROM parse_errors WHERE error_id = ?
            """,
            [error_id],
        ).fetchone()

        assert result[0] == sentence
        assert result[1] == "CHECKSUM_FAILED"
        assert result[2] == "Checksum mismatch"
        assert result[3] == "PNORI"
        assert result[4] == "2E"
        assert result[5] == "FF"


class TestUpdateOperations:
    """Test database update operations."""

    def test_update_raw_line_status(self):
        """Test updating raw line status."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Insert a line
        sentence = "$PNORI,4,Test*2E"
        line_id = insert_raw_line(conn, sentence, "PENDING")

        # Update status
        success = update_raw_line_status(conn, line_id, "OK")

        assert success

        # Verify update
        result = conn.execute(
            "SELECT parse_status FROM raw_lines WHERE line_id = ?",
            [line_id],
        ).fetchone()

        assert result[0] == "OK"

    def test_update_raw_line_status_with_error(self):
        """Test updating raw line status with error message."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Insert a line
        sentence = "$INVALID*FF"
        line_id = insert_raw_line(conn, sentence, "PENDING")

        # Update with error
        error_msg = "Parse failed"
        success = update_raw_line_status(conn, line_id, "FAIL", error_msg)

        assert success

        # Verify update
        result = conn.execute(
            "SELECT parse_status, error_message FROM raw_lines WHERE line_id = ?",
            [line_id],
        ).fetchone()

        assert result[0] == "FAIL"
        assert result[1] == error_msg


class TestQueryOperations:
    """Test database query operations."""

    def test_query_raw_lines_all(self):
        """Test querying all raw lines."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Insert test data
        for i in range(5):
            insert_raw_line(conn, f"$PNORI,{i},Test*2E", "OK", "PNORI", True)

        # Query all
        results = query_raw_lines(conn)

        assert len(results) == 5
        assert all(r["record_type"] == "PNORI" for r in results)

    def test_query_raw_lines_by_record_type(self):
        """Test querying by record type."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Insert mixed types
        insert_raw_line(conn, "$PNORI,1*2E", "OK", "PNORI", True)
        insert_raw_line(conn, "$PNORS,1*2E", "OK", "PNORS", True)
        insert_raw_line(conn, "$PNORI,2*2E", "OK", "PNORI", True)

        # Query PNORI only
        results = query_raw_lines(conn, record_type="PNORI")

        assert len(results) == 2
        assert all(r["record_type"] == "PNORI" for r in results)

    def test_query_raw_lines_by_parse_status(self):
        """Test querying by parse status."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Insert mixed statuses
        insert_raw_line(conn, "$PNORI,1*2E", "OK", "PNORI", True)
        insert_raw_line(conn, "$INVALID*FF", "FAIL", None, False)
        insert_raw_line(conn, "$PNORI,2*2E", "OK", "PNORI", True)

        # Query OK only
        results = query_raw_lines(conn, parse_status="OK")

        assert len(results) == 2
        assert all(r["parse_status"] == "OK" for r in results)

    def test_query_raw_lines_with_limit(self):
        """Test query limit parameter."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Insert 10 lines
        for i in range(10):
            insert_raw_line(conn, f"$PNORI,{i}*2E", "OK", "PNORI", True)

        # Query with limit
        results = query_raw_lines(conn, limit=5)

        assert len(results) == 5

    def test_query_raw_lines_empty_result(self):
        """Test query with no matching records."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Query empty database
        results = query_raw_lines(conn, record_type="NONEXISTENT")

        assert len(results) == 0
        assert isinstance(results, list)

    def test_query_parse_errors(self):
        """Test querying parse errors."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Insert errors
        insert_parse_error(
            conn, "$INVALID*FF", "CHECKSUM_FAILED", "Bad checksum", "PNORI"
        )
        insert_parse_error(conn, "$MALFORMED", "INVALID_FORMAT", "Malformed sentence")

        # Query all errors
        results = query_parse_errors(conn)

        assert len(results) == 2
        assert all("error_type" in r for r in results)

    def test_query_parse_errors_by_type(self):
        """Test querying parse errors by error type."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Insert mixed error types
        insert_parse_error(conn, "$INVALID*FF", "CHECKSUM_FAILED")
        insert_parse_error(conn, "$MALFORMED", "INVALID_FORMAT")
        insert_parse_error(conn, "$ANOTHER*00", "CHECKSUM_FAILED")

        # Query specific error type
        results = query_parse_errors(conn, error_type="CHECKSUM_FAILED")

        assert len(results) == 2
        assert all(r["error_type"] == "CHECKSUM_FAILED" for r in results)


class TestPerformance:
    """Test performance of batch operations."""

    def test_batch_insert_performance(self):
        """Test that batch insert is faster than individual inserts."""
        import time

        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Prepare data
        records = [
            {
                "sentence": f"$PNORI,{i},Test*2E",
                "parse_status": "OK",
                "record_type": "PNORI",
                "checksum_valid": True,
                "error_message": None,
            }
            for i in range(1000)
        ]

        # Batch insert
        start = time.time()
        batch_insert_raw_lines(conn, records)
        batch_time = time.time() - start

        # Clear database
        conn.execute("DELETE FROM raw_lines")
        conn.commit()

        # Individual inserts
        start = time.time()
        for r in records:
            insert_raw_line(
                conn,
                r["sentence"],
                r["parse_status"],
                r["record_type"],
                r["checksum_valid"],
                r["error_message"],
            )
        individual_time = time.time() - start

        # Batch should be faster
        assert batch_time < individual_time
        print(
            f"\nBatch: {batch_time:.3f}s, Individual: {individual_time:.3f}s, "
            f"Speedup: {individual_time / batch_time:.2f}x"
        )
