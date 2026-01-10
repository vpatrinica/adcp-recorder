"""Database operations for NMEA data storage.

Provides functions for inserting, updating, and querying NMEA sentence records.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import duckdb


def insert_raw_line(
    conn: duckdb.DuckDBPyConnection,
    sentence: str,
    parse_status: str = "PENDING",
    record_type: Optional[str] = None,
    checksum_valid: Optional[bool] = None,
    error_message: Optional[str] = None,
) -> int:
    """Insert a single raw NMEA sentence into the database.

    Args:
        conn: DuckDB connection
        sentence: Raw NMEA sentence string
        parse_status: Parse status ('OK', 'FAIL', 'PENDING')
        record_type: NMEA message type (e.g., 'PNORI', 'PNORS')
        checksum_valid: Whether checksum validation passed
        error_message: Error message if parsing failed

    Returns:
        The generated line_id for the inserted record

    Example:
        >>> line_id = insert_raw_line(conn, "$PNORI,4,Test*2E", "OK", "PNORI", True)
    """
    result = conn.execute(
        """
        INSERT INTO raw_lines (line_id, raw_sentence, parse_status, record_type, checksum_valid, error_message)
        VALUES (nextval('raw_lines_seq'), ?, ?, ?, ?, ?)
        RETURNING line_id
        """,
        [sentence, parse_status, record_type, checksum_valid, error_message],
    ).fetchone()

    conn.commit()
    return result[0] if result else -1


def batch_insert_raw_lines(
    conn: duckdb.DuckDBPyConnection, records: List[Dict[str, Any]]
) -> int:
    """Batch insert multiple raw NMEA sentences.

    Args:
        conn: DuckDB connection
        records: List of dictionaries with keys: sentence, parse_status, record_type,
                checksum_valid, error_message

    Returns:
        Number of records inserted

    Example:
        >>> records = [
        ...     {'sentence': '$PNORI,4,Test*2E', 'parse_status': 'OK',
        ...      'record_type': 'PNORI', 'checksum_valid': True, 'error_message': None},
        ... ]
        >>> count = batch_insert_raw_lines(conn, records)
    """
    if not records:
        return 0

    # Prepare data for executemany
    data = [
        (
            r.get("sentence"),
            r.get("parse_status", "PENDING"),
            r.get("record_type"),
            r.get("checksum_valid"),
            r.get("error_message"),
        )
        for r in records
    ]

    conn.executemany(
        """
        INSERT INTO raw_lines (line_id, raw_sentence, parse_status, record_type, checksum_valid, error_message)
        VALUES (nextval('raw_lines_seq'), ?, ?, ?, ?, ?)
        """,
        data,
    )

    conn.commit()
    return len(records)


def insert_parse_error(
    conn: duckdb.DuckDBPyConnection,
    sentence: str,
    error_type: str,
    error_message: Optional[str] = None,
    attempted_prefix: Optional[str] = None,
    checksum_expected: Optional[str] = None,
    checksum_actual: Optional[str] = None,
) -> int:
    """Insert a parsing error record.

    Args:
        conn: DuckDB connection
        sentence: Raw NMEA sentence that failed to parse
        error_type: Type of error (e.g., 'CHECKSUM_FAILED', 'INVALID_FORMAT')
        error_message: Detailed error message
        attempted_prefix: NMEA prefix that was attempted to parse
        checksum_expected: Expected checksum value
        checksum_actual: Actual checksum value

    Returns:
        The generated error_id for the inserted record

    Example:
        >>> error_id = insert_parse_error(conn, "$PNORI,4*FF", "CHECKSUM_FAILED",
        ...                               attempted_prefix="PNORI", checksum_expected="2E",
        ...                               checksum_actual="FF")
    """
    result = conn.execute(
        """
        INSERT INTO parse_errors (error_id, raw_sentence, error_type, error_message,
                                 attempted_prefix, checksum_expected, checksum_actual)
        VALUES (nextval('parse_errors_seq'), ?, ?, ?, ?, ?, ?)
        RETURNING error_id
        """,
        [
            sentence,
            error_type,
            error_message,
            attempted_prefix,
            checksum_expected,
            checksum_actual,
        ],
    ).fetchone()

    conn.commit()
    return result[0] if result else -1


def update_raw_line_status(
    conn: duckdb.DuckDBPyConnection,
    line_id: int,
    parse_status: str,
    error_message: Optional[str] = None,
) -> bool:
    """Update the parse status of a raw line record.

    Args:
        conn: DuckDB connection
        line_id: ID of the record to update
        parse_status: New parse status ('OK', 'FAIL')
        error_message: Error message if status is 'FAIL'

    Returns:
        True if update was successful, False otherwise

    Example:
        >>> success = update_raw_line_status(conn, 123, "OK")
    """
    result = conn.execute(
        """
        UPDATE raw_lines
        SET parse_status = ?, error_message = ?
        WHERE line_id = ?
        """,
        [parse_status, error_message, line_id],
    )

    conn.commit()
    return result.fetchone() is not None


def query_raw_lines(
    conn: duckdb.DuckDBPyConnection,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    record_type: Optional[str] = None,
    parse_status: Optional[str] = None,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """Query raw lines with optional filters.

    Args:
        conn: DuckDB connection
        start_time: Filter records after this timestamp
        end_time: Filter records before this timestamp
        record_type: Filter by NMEA message type
        parse_status: Filter by parse status
        limit: Maximum number of records to return

    Returns:
        List of dictionaries containing record data

    Example:
        >>> records = query_raw_lines(conn, record_type='PNORI', parse_status='OK', limit=100)
    """
    where_clauses = []
    params = []

    if start_time is not None:
        where_clauses.append("received_at >= ?")
        params.append(start_time)

    if end_time is not None:
        where_clauses.append("received_at <= ?")
        params.append(end_time)

    if record_type is not None:
        where_clauses.append("record_type = ?")
        params.append(record_type)

    if parse_status is not None:
        where_clauses.append("parse_status = ?")
        params.append(parse_status)

    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

    sql = f"""
        SELECT line_id, received_at, raw_sentence, parse_status, record_type, 
               checksum_valid, error_message
        FROM raw_lines
        WHERE {where_clause}
        ORDER BY received_at DESC
        LIMIT ?
    """

    params.append(limit)

    results = conn.execute(sql, params).fetchall()

    # Convert to list of dictionaries
    return [
        {
            "line_id": row[0],
            "received_at": row[1],
            "raw_sentence": row[2],
            "parse_status": row[3],
            "record_type": row[4],
            "checksum_valid": row[5],
            "error_message": row[6],
        }
        for row in results
    ]


def query_parse_errors(
    conn: duckdb.DuckDBPyConnection,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    error_type: Optional[str] = None,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """Query parse errors with optional filters.

    Args:
        conn: DuckDB connection
        start_time: Filter records after this timestamp
        end_time: Filter records before this timestamp
        error_type: Filter by error type
        limit: Maximum number of records to return

    Returns:
        List of dictionaries containing error data

    Example:
        >>> errors = query_parse_errors(conn, error_type='CHECKSUM_FAILED', limit=50)
    """
    where_clauses = []
    params = []

    if start_time is not None:
        where_clauses.append("received_at >= ?")
        params.append(start_time)

    if end_time is not None:
        where_clauses.append("received_at <= ?")
        params.append(end_time)

    if error_type is not None:
        where_clauses.append("error_type = ?")
        params.append(error_type)

    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

    sql = f"""
        SELECT error_id, received_at, raw_sentence, error_type, error_message,
               attempted_prefix, checksum_expected, checksum_actual
        FROM parse_errors
        WHERE {where_clause}
        ORDER BY received_at DESC
        LIMIT ?
    """

    params.append(limit)

    results = conn.execute(sql, params).fetchall()

    # Convert to list of dictionaries
    return [
        {
            "error_id": row[0],
            "received_at": row[1],
            "raw_sentence": row[2],
            "error_type": row[3],
            "error_message": row[4],
            "attempted_prefix": row[5],
            "checksum_expected": row[6],
            "checksum_actual": row[7],
        }
        for row in results
    ]
