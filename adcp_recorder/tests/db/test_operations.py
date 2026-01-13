"""Tests for database operations."""

from adcp_recorder.db import (
    DatabaseManager,
    batch_insert_raw_lines,
    insert_parse_error,
    insert_pnori_configuration,
    insert_raw_line,
    query_parse_errors,
    query_pnori_configurations,
    query_raw_lines,
    update_raw_line_status,
)
from adcp_recorder.parsers import PNORI, PNORI1, PNORI2


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
        insert_parse_error(conn, "$INVALID*FF", "CHECKSUM_FAILED", "Bad checksum", "PNORI")
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
            for i in range(5000)
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


class TestPNORIConfigurationOperations:
    """Test PNORI configuration database operations."""

    def test_insert_pnori_configuration(self):
        """Test inserting PNORI configuration."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        sentence = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E"
        config = PNORI.from_nmea(sentence)
        config_id = insert_pnori_configuration(conn, config.to_dict(), sentence)

        assert config_id > 0

        # Verify insertion
        result = conn.execute(
            """
            SELECT instrument_type_name, head_id, beam_count,
                   coord_system_name
            FROM pnori WHERE config_id = ?
            """,
            [config_id],
        ).fetchone()

        assert result[0] == "SIGNATURE"
        assert result[1] == "Signature1000900001"
        assert result[2] == 4
        assert result[3] == "ENU"

    def test_insert_pnori1_configuration(self):
        """Test inserting PNORI1 configuration."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        sentence = "$PNORI1,4,123456,4,30,1.00,5.00,BEAM*5B"
        config = PNORI1.from_nmea(sentence)
        config_id = insert_pnori_configuration(conn, config.to_dict(), sentence)

        assert config_id > 0

        # Verify insertion with string coordinate system
        result = conn.execute(
            """
            SELECT coord_system_name, coord_system_code
            FROM pnori1 WHERE config_id = ?
            """,
            [config_id],
        ).fetchone()

        assert result[0] == "BEAM"
        assert result[1] == 2  # BEAM maps to 2

    def test_insert_pnori2_configuration(self):
        """Test inserting PNORI2 tagged configuration."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        sentence = "$PNORI2,IT=4,SN=789012,NB=4,NC=25,BD=0.50,CS=2.00,CY=XYZ*00"
        config = PNORI2.from_nmea(sentence)
        config_id = insert_pnori_configuration(conn, config.to_dict(), sentence)

        assert config_id > 0

        # Verify tagged variant
        result = conn.execute(
            """
            SELECT head_id, coord_system_name
            FROM pnori2 WHERE config_id = ?
            """,
            [config_id],
        ).fetchone()

        assert result[0] == "789012"
        assert result[1] == "XYZ"

    def test_query_pnori_configurations_all(self):
        """Test querying all PNORI configurations."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Insert multiple configurations
        sentences = [
            "$PNORI,4,12345,4,20,0.20,1.00,0*00",
            "$PNORI1,4,12346,4,30,0.50,2.00,ENU*00",
            "$PNORI2,IT=4,SN=12347,NB=4,NC=25,BD=1.00,CS=3.00,CY=BEAM*00",
        ]

        for sentence in sentences:
            if "PNORI2" in sentence:
                config = PNORI2.from_nmea(sentence)
            elif "PNORI1" in sentence:
                config = PNORI1.from_nmea(sentence)
            else:
                config = PNORI.from_nmea(sentence)
            insert_pnori_configuration(conn, config.to_dict(), sentence)

        # Query all
        results = query_pnori_configurations(conn)

        assert len(results) == 3
        assert all("sentence_type" in r for r in results)
        assert all("head_id" in r for r in results)

    def test_query_pnori_by_head_id(self):
        """Test querying PNORI configurations by head ID."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Insert configurations with different head IDs
        sentence1 = "$PNORI,4,1001,4,20,0.20,1.00,0*00"
        sentence2 = "$PNORI,4,1002,4,20,0.20,1.00,0*00"

        config1 = PNORI.from_nmea(sentence1)
        config2 = PNORI.from_nmea(sentence2)

        insert_pnori_configuration(conn, config1.to_dict(), sentence1)
        insert_pnori_configuration(conn, config2.to_dict(), sentence2)

        # Query specific head ID
        results = query_pnori_configurations(conn, head_id="1001")

        assert len(results) == 1
        assert results[0]["head_id"] == "1001"

    def test_query_pnori_by_sentence_type(self):
        """Test querying PNORI configurations by sentence type."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Insert mixed sentence types
        sentence1 = "$PNORI,4,2001,4,20,0.20,1.00,0*00"
        sentence2 = "$PNORI1,4,2002,4,30,0.50,2.00,ENU*00"
        sentence3 = "$PNORI,4,2003,4,25,0.30,1.50,0*00"

        config1 = PNORI.from_nmea(sentence1)
        config2 = PNORI1.from_nmea(sentence2)
        config3 = PNORI.from_nmea(sentence3)

        insert_pnori_configuration(conn, config1.to_dict(), sentence1)
        insert_pnori_configuration(conn, config2.to_dict(), sentence2)
        insert_pnori_configuration(conn, config3.to_dict(), sentence3)

        # Query only PNORI
        results = query_pnori_configurations(conn, sentence_type="PNORI")

        assert len(results) == 2
        assert all(r["sentence_type"] == "PNORI" for r in results)

        # Query only PNORI1
        results = query_pnori_configurations(conn, sentence_type="PNORI1")

        assert len(results) == 1
        assert results[0]["sentence_type"] == "PNORI1"

    def test_query_pnori_with_limit(self):
        """Test query limit parameter."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Insert multiple configurations
        for i in range(10):
            sentence = f"$PNORI,4,{1000 + i},4,20,0.20,1.00,0*00"
            config = PNORI.from_nmea(sentence)
            insert_pnori_configuration(conn, config.to_dict(), sentence)

        # Query with limit
        results = query_pnori_configurations(conn, limit=5)

        assert len(results) == 5

    def test_pnori_database_constraints(self):
        """Test that database enforces PNORI constraints."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        # Test invalid instrument type code (not in 0, 2, 4)
        import pytest

        with pytest.raises(Exception):  # DuckDB constraint violation
            conn.execute(
                """
                INSERT INTO pnori (
                    config_id, original_sentence,
                    instrument_type_name, instrument_type_code, head_id,
                    beam_count, cell_count, blanking_distance, cell_size,
                    coord_system_name, coord_system_code, checksum
                )
                VALUES (1, '$TEST', 'INVALID', 99, '123', 4, 20, 0.20, 1.00, 'ENU', 0, '00')
                """
            )

    def test_pnori_cross_field_validation(self):
        """Test cross-field constraint: Signature must have 4 beams."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        import pytest

        # Signature (type 4) with invalid beam count (3)
        with pytest.raises(Exception):  # DuckDB constraint violation
            conn.execute(
                """
                INSERT INTO pnori (
                    config_id, original_sentence,
                    instrument_type_name, instrument_type_code, head_id,
                    beam_count, cell_count, blanking_distance, cell_size,
                    coord_system_name, coord_system_code, checksum
                )
                VALUES (1, '$TEST', 'SIGNATURE', 4, '123', 3, 20, 0.20, 1.00, 'ENU', 0, '00')
                """
            )

    def test_pnori_coordinate_system_mapping(self):
        """Test that coordinate system mappings are enforced on pnori1."""
        db = DatabaseManager(":memory:")
        conn = db.get_connection()

        import pytest

        # Invalid mapping: ENU with code 1 (should be 0)
        with pytest.raises(Exception):  # DuckDB constraint violation
            conn.execute(
                """
                INSERT INTO pnori1 (
                    config_id, original_sentence,
                    instrument_type_name, instrument_type_code, head_id,
                    beam_count, cell_count, blanking_distance, cell_size,
                    coord_system_name, coord_system_code, checksum
                )
                VALUES (1, '$TEST', 'SIGNATURE', 4, '123', 4, 20, 0.20, 1.00, 'ENU', 1, '00')
                """
            )
