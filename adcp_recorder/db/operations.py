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


# PNORI Configuration Operations


def insert_pnori_configuration(
    conn: duckdb.DuckDBPyConnection, pnori_dict: Dict[str, Any], original_sentence: str
) -> int:
    """Insert PNORI/PNORI1/PNORI2 configuration into database.

    Args:
        conn: DuckDB connection
        pnori_dict: Dictionary from PNORI.to_dict(), PNORI1.to_dict(), or PNORI2.to_dict()
        original_sentence: Original NMEA sentence

    Returns:
        The generated config_id for the inserted record

    Example:
        >>> from adcp_recorder.parsers import PNORI
        >>> config = PNORI.from_nmea("$PNORI,4,Test,4,20,0.20,1.00,0*2E")
        >>> config_id = insert_pnori_configuration(conn, config.to_dict(), "$PNORI...")
    """
    result = conn.execute(
        """
        INSERT INTO pnori_configurations (
            config_id, sentence_type, original_sentence,
            instrument_type_name, instrument_type_code, head_id,
            beam_count, cell_count, blanking_distance, cell_size,
            coord_system_name, coord_system_code, checksum
        )
        VALUES (
            nextval('pnori_configurations_seq'), ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?
        )
        RETURNING config_id
        """,
        [
            pnori_dict["sentence_type"],
            original_sentence,
            pnori_dict["instrument_type_name"],
            pnori_dict["instrument_type_code"],
            pnori_dict["head_id"],
            pnori_dict["beam_count"],
            pnori_dict["cell_count"],
            pnori_dict["blanking_distance"],
            pnori_dict["cell_size"],
            pnori_dict["coord_system_name"],
            pnori_dict["coord_system_code"],
            pnori_dict["checksum"],
        ],
    ).fetchone()

    conn.commit()
    return result[0] if result else -1


def query_pnori_configurations(
    conn: duckdb.DuckDBPyConnection,
    head_id: Optional[str] = None,
    sentence_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """Query PNORI configurations with optional filters.

    Args:
        conn: DuckDB connection
        head_id: Filter by instrument head ID
        sentence_type: Filter by sentence type ('PNORI', 'PNORI1', 'PNORI2')
        start_time: Filter records after this timestamp
        end_time: Filter records before this timestamp
        limit: Maximum number of records to return

    Returns:
        List of dictionaries containing configuration data

    Example:
        >>> configs = query_pnori_configurations(conn, head_id='Signature1000900001', limit=10)
    """
    where_clauses = []
    params = []

    if head_id is not None:
        where_clauses.append("head_id = ?")
        params.append(head_id)

    if sentence_type is not None:
        where_clauses.append("sentence_type = ?")
        params.append(sentence_type)

    if start_time is not None:
        where_clauses.append("received_at >= ?")
        params.append(start_time)

    if end_time is not None:
        where_clauses.append("received_at <= ?")
        params.append(end_time)

    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

    sql = f"""
        SELECT config_id, received_at, sentence_type, original_sentence,
               instrument_type_name, instrument_type_code, head_id,
               beam_count, cell_count, blanking_distance, cell_size,
               coord_system_name, coord_system_code, checksum
        FROM pnori_configurations
        WHERE {where_clause}
        ORDER BY received_at DESC
        LIMIT ?
    """

    params.append(limit)

    results = conn.execute(sql, params).fetchall()

    # Convert to list of dictionaries
    return [
        {
            "config_id": row[0],
            "received_at": row[1],
            "sentence_type": row[2],
            "original_sentence": row[3],
            "instrument_type_name": row[4],
            "instrument_type_code": row[5],
            "head_id": row[6],
            "beam_count": row[7],
            "cell_count": row[8],
            "blanking_distance": row[9],
            "cell_size": row[10],
            "coord_system_name": row[11],
            "coord_system_code": row[12],
            "checksum": row[13],
        }
        for row in results
    ]


def insert_sensor_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: Dict) -> int:
    """Insert sensor data into sensor_data table."""
    query = """
    INSERT INTO sensor_data (
        record_id, original_sentence, sentence_type,
        measurement_date, measurement_time,
        error_code, status_code, battery, sound_speed,
        heading, pitch, roll, pressure, temperature,
        analog1, analog2, salinity, checksum
    ) VALUES (
        nextval('sensor_data_seq'), ?, ?,
        ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?
    ) RETURNING record_id;
    """
    
    params = (
        original_sentence, data["sentence_type"],
        data["date"], data["time"],
        data.get("error_code"), data.get("status_code"), data.get("battery"), data.get("sound_speed"),
        data.get("heading"), data.get("pitch"), data.get("roll"), data.get("pressure"), data.get("temperature"),
        data.get("analog1"), data.get("analog2"), data.get("salinity"), data.get("checksum")
    )
    
    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0]


def insert_velocity_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: Dict) -> int:
    """Insert current velocity data into velocity_data table."""
    query = """
    INSERT INTO velocity_data (
        record_id, original_sentence, sentence_type,
        measurement_date, measurement_time, cell_index,
        vel1, vel2, vel3,
        corr1, corr2, corr3,
        amp1, amp2, amp3, amp4,
        checksum
    ) VALUES (
        nextval('velocity_data_seq'), ?, ?,
        ?, ?, ?,
        ?, ?, ?,
        ?, ?, ?,
        ?, ?, ?, ?,
        ?
    ) RETURNING record_id;
    """
    
    params = (
        original_sentence, data["sentence_type"],
        data["date"], data["time"], data["cell_index"],
        data["vel1"], data["vel2"], data["vel3"],
        data.get("corr1"), data.get("corr2"), data.get("corr3"),
        data.get("amp1"), data.get("amp2"), data.get("amp3"), data.get("amp4"),
        data.get("checksum")
    )
    
    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0]


def insert_header_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: Dict) -> int:
    """Insert header data into header_data table."""
    query = """
    INSERT INTO header_data (
        record_id, original_sentence, sentence_type,
        measurement_date, measurement_time,
        num_cells, first_cell, ping_count,
        coord_system, profile_interval, checksum
    ) VALUES (
        nextval('header_data_seq'), ?, ?,
        ?, ?,
        ?, ?, ?,
        ?, ?, ?
    ) RETURNING record_id;
    """
    
    params = (
        original_sentence, data["sentence_type"],
        data["date"], data["time"],
        data["num_cells"], data["first_cell"], data["ping_count"],
        data.get("coordinate_system"), data.get("profile_interval"), data.get("checksum")
    )
    
    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0]


def insert_echo_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: Dict) -> int:
    """Insert echo intensity data into echo_data table."""
    query = """
    INSERT INTO echo_data (
        record_id, original_sentence, sentence_type,
        measurement_date, measurement_time, cell_index,
        echo1, echo2, echo3, echo4,
        checksum
    ) VALUES (
        nextval('echo_data_seq'), ?, ?,
        ?, ?, ?,
        ?, ?, ?, ?,
        ?
    ) RETURNING record_id;
    """
    
    params = (
        original_sentence, data["sentence_type"],
        data["date"], data["time"], data["cell_index"],
        data["echo1"], data["echo2"], data["echo3"], data["echo4"],
        data.get("checksum")
    )
    
    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0]


def insert_pnorw_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: Dict) -> int:
    """Insert into pnorw_data table."""
    query = """
    INSERT INTO pnorw_data (
        record_id, original_sentence, sentence_type,
        measurement_date, measurement_time,
        sig_wave_height, max_wave_height, peak_period, mean_direction,
        checksum
    ) VALUES (
        nextval('pnorw_data_seq'), ?, ?,
        ?, ?,
        ?, ?, ?, ?,
        ?
    ) RETURNING record_id;
    """
    params = (
        original_sentence, data["sentence_type"],
        data["date"], data["time"],
        data["sig_wave_height"], data["max_wave_height"], data["peak_period"], data["mean_direction"],
        data.get("checksum")
    )
    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0]


def insert_pnorb_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: Dict) -> int:
    """Insert into pnorb_data table."""
    query = """
    INSERT INTO pnorb_data (
        record_id, original_sentence, sentence_type,
        measurement_date, measurement_time,
        vel_east, vel_north, vel_up, bottom_dist, quality,
        checksum
    ) VALUES (
        nextval('pnorb_data_seq'), ?, ?,
        ?, ?,
        ?, ?, ?, ?, ?,
        ?
    ) RETURNING record_id;
    """
    params = (
        original_sentence, data["sentence_type"],
        data["date"], data["time"],
        data["vel_east"], data["vel_north"], data["vel_up"], data["bottom_dist"], data["quality"],
        data.get("checksum")
    )
    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0]


def insert_pnorf_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: Dict) -> int:
    """Insert into pnorf_data table."""
    query = """
    INSERT INTO pnorf_data (
        record_id, original_sentence, sentence_type,
        measurement_date, measurement_time,
        frequency, bandwidth, transmit_power,
        checksum
    ) VALUES (
        nextval('pnorf_data_seq'), ?, ?,
        ?, ?,
        ?, ?, ?,
        ?
    ) RETURNING record_id;
    """
    params = (
        original_sentence, data["sentence_type"],
        data["date"], data["time"],
        data["frequency"], data["bandwidth"], data["transmit_power"],
        data.get("checksum")
    )
    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0]


def insert_pnorwd_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: Dict) -> int:
    """Insert into pnorwd_data table."""
    query = """
    INSERT INTO pnorwd_data (
        record_id, original_sentence, sentence_type,
        measurement_date, measurement_time,
        freq_bin, direction, spread_angle, energy,
        checksum
    ) VALUES (
        nextval('pnorwd_data_seq'), ?, ?,
        ?, ?,
        ?, ?, ?, ?,
        ?
    ) RETURNING record_id;
    """
    params = (
        original_sentence, data["sentence_type"],
        data["date"], data["time"],
        data["freq_bin"], data["direction"], data["spread_angle"], data["energy"],
        data.get("checksum")
    )
    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0]


def insert_pnora_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: Dict) -> int:
    """Insert into pnora_data table."""
    query = """
    INSERT INTO pnora_data (
        record_id, original_sentence, sentence_type,
        measurement_date, measurement_time,
        method, distance, quality,
        checksum
    ) VALUES (
        nextval('pnora_data_seq'), ?, ?,
        ?, ?,
        ?, ?, ?,
        ?
    ) RETURNING record_id;
    """
    params = (
        original_sentence, data["sentence_type"],
        data["date"], data["time"],
        data["method"], data["distance"], data["quality"],
        data.get("checksum")
    )
    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0]


def query_sensor_data(
    conn: duckdb.DuckDBPyConnection, limit: int = 100
) -> List[Dict[str, Any]]:
    """Query recent sensor data records."""
    cols = conn.execute("DESCRIBE sensor_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM sensor_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row)) for row in results]


def query_velocity_data(
    conn: duckdb.DuckDBPyConnection, limit: int = 100
) -> List[Dict[str, Any]]:
    """Query recent velocity data records."""
    cols = conn.execute("DESCRIBE velocity_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM velocity_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row)) for row in results]


def query_header_data(
    conn: duckdb.DuckDBPyConnection, limit: int = 100
) -> List[Dict[str, Any]]:
    """Query recent header data records."""
    cols = conn.execute("DESCRIBE header_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM header_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row)) for row in results]


def query_echo_data(
    conn: duckdb.DuckDBPyConnection, limit: int = 100
) -> List[Dict[str, Any]]:
    """Query recent echo data records."""
    cols = conn.execute("DESCRIBE echo_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM echo_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row)) for row in results]


def query_pnorw_data(
    conn: duckdb.DuckDBPyConnection, limit: int = 100
) -> List[Dict[str, Any]]:
    """Query recent wave height/period records."""
    cols = conn.execute("DESCRIBE pnorw_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM pnorw_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row)) for row in results]


def query_pnorb_data(
    conn: duckdb.DuckDBPyConnection, limit: int = 100
) -> List[Dict[str, Any]]:
    """Query recent bottom track records."""
    cols = conn.execute("DESCRIBE pnorb_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM pnorb_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row)) for row in results]


def query_pnorf_data(
    conn: duckdb.DuckDBPyConnection, limit: int = 100
) -> List[Dict[str, Any]]:
    """Query recent frequency records."""
    cols = conn.execute("DESCRIBE pnorf_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM pnorf_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row)) for row in results]


def query_pnorwd_data(
    conn: duckdb.DuckDBPyConnection, limit: int = 100
) -> List[Dict[str, Any]]:
    """Query recent wave directional records."""
    cols = conn.execute("DESCRIBE pnorwd_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM pnorwd_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row)) for row in results]


def query_pnora_data(
    conn: duckdb.DuckDBPyConnection, limit: int = 100
) -> List[Dict[str, Any]]:
    """Query recent altitude records."""
    cols = conn.execute("DESCRIBE pnora_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM pnora_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row)) for row in results]
