"""Database operations for NMEA data storage.

Provides functions for inserting, updating, and querying NMEA sentence records.
"""

import json
from datetime import datetime
from typing import Any

import duckdb


def insert_raw_line(
    conn: duckdb.DuckDBPyConnection,
    sentence: str,
    parse_status: str = "PENDING",
    record_type: str | None = None,
    checksum_valid: bool | None = None,
    error_message: str | None = None,
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
        INSERT INTO raw_lines (
            line_id, raw_sentence, parse_status, record_type, checksum_valid, error_message
        )
        VALUES (nextval('raw_lines_seq'), ?, ?, ?, ?, ?)
        RETURNING line_id
        """,
        [sentence, parse_status, record_type, checksum_valid, error_message],
    ).fetchone()

    conn.commit()
    return result[0] if result else -1


def batch_insert_raw_lines(conn: duckdb.DuckDBPyConnection, records: list[dict[str, Any]]) -> int:
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

    # Pre-fetch IDs to avoid nextval() overhead in executemany loop
    count = len(records)

    ids_result = conn.execute(f"SELECT nextval('raw_lines_seq') FROM range({count})").fetchall()

    # Prepare data for executemany
    data = [
        (
            ids_result[i][0],
            r.get("sentence"),
            r.get("parse_status", "PENDING"),
            r.get("record_type"),
            r.get("checksum_valid"),
            r.get("error_message"),
        )
        for i, r in enumerate(records)
    ]

    conn.execute("BEGIN TRANSACTION")
    try:
        # Chunked insert for performance
        batch_size = 1000
        for i in range(0, len(data), batch_size):
            chunk = data[i : i + batch_size]
            placeholders = ", ".join(["(?, ?, ?, ?, ?, ?)"] * len(chunk))
            # Flatten list of tuples
            params = [val for row in chunk for val in row]
            conn.execute(
                f"""
                INSERT INTO raw_lines (
                    line_id, raw_sentence, parse_status, record_type, checksum_valid, error_message
                )
                VALUES {placeholders}
                """,
                params,
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return len(records)


def insert_parse_error(
    conn: duckdb.DuckDBPyConnection,
    sentence: str,
    error_type: str,
    error_message: str | None = None,
    attempted_prefix: str | None = None,
    checksum_expected: str | None = None,
    checksum_actual: str | None = None,
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
        INSERT INTO parse_errors (
            error_id, raw_sentence, error_type, error_message,
            attempted_prefix, checksum_expected, checksum_actual
        )
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
    error_message: str | None = None,
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
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    record_type: str | None = None,
    parse_status: str | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
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
    params: list[Any] = []

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
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    error_type: str | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
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
    params: list[Any] = []

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
    conn: duckdb.DuckDBPyConnection, pnori_dict: dict[str, Any], original_sentence: str
) -> int:
    """Insert PNORI/PNORI1/PNORI2 configuration into database - routes to correct table.

    Args:
        conn: DuckDB connection
        pnori_dict: Dictionary from PNORI.to_dict(), PNORI1.to_dict(), or PNORI2.to_dict()
        original_sentence: Original NMEA sentence

    Returns:
        The generated config_id for the inserted record
    """
    sentence_type = pnori_dict["sentence_type"]

    # Route to correct table based on sentence type
    if sentence_type == "PNORI":
        result = conn.execute(
            """
            INSERT INTO pnori (
                config_id, original_sentence,
                instrument_type_name, instrument_type_code, head_id,
                beam_count, cell_count, blanking_distance, cell_size,
                coord_system_name, coord_system_code, checksum
            )
            VALUES (
                nextval('pnori_seq'), ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?
            )
            RETURNING config_id
            """,
            [
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
    elif sentence_type in ("PNORI1", "PNORI2"):
        data_format = 101 if sentence_type == "PNORI1" else 102
        result = conn.execute(
            """
            INSERT INTO pnori12 (
                config_id, data_format, original_sentence,
                instrument_type_name, instrument_type_code, head_id,
                beam_count, cell_count, blanking_distance, cell_size,
                coord_system_name, coord_system_code, checksum
            )
            VALUES (
                nextval('pnori12_seq'), ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?
            )
            RETURNING config_id
            """,
            [
                data_format,
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
    else:
        raise ValueError(f"Unknown PNORI sentence type: {sentence_type}")

    conn.commit()
    return result[0] if result else -1


def query_pnori_configurations(
    conn: duckdb.DuckDBPyConnection,
    head_id: str | None = None,
    sentence_type: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Query PNORI configurations from all 3 tables (pnori, pnori1, pnori2).

    Args:
        conn: DuckDB connection
        head_id: Filter by head_id
        sentence_type: Filter by sentence type ('PNORI', 'PNORI1', or 'PNORI2')
        start_time: Filter records received after this time
        end_time: Filter records received before this time
        limit: Maximum number of records to return

    Returns:
        List of dictionaries containing configuration data

    """
    # Build query to UNION pnori (DF100) and pnori12 (DF101/102)
    query = """
        SELECT config_id, received_at, 'PNORI' as sentence_type, original_sentence,
               instrument_type_name, instrument_type_code, head_id,
               beam_count, cell_count, blanking_distance, cell_size,
               coord_system_name, coord_system_code, checksum
        FROM pnori
        UNION ALL
        SELECT config_id, received_at,
               CASE WHEN data_format = 101 THEN 'PNORI1' ELSE 'PNORI2' END as sentence_type,
               original_sentence,
               instrument_type_name, instrument_type_code, head_id,
               beam_count, cell_count, blanking_distance, cell_size,
               coord_system_name, coord_system_code, checksum
        FROM pnori12
    """

    conditions = []
    params: list[Any] = []

    if head_id:
        conditions.append("head_id = ?")
        params.append(head_id)

    if sentence_type:
        conditions.append("sentence_type = ?")
        params.append(sentence_type)

    if start_time:
        conditions.append("received_at >= ?")
        params.append(start_time)

    if end_time:
        conditions.append("received_at <= ?")
        params.append(end_time)

    if conditions:
        query = f"SELECT * FROM ({query}) WHERE {' AND '.join(conditions)}"

    query += " ORDER BY received_at DESC"

    if limit:
        query += f" LIMIT {limit}"

    result = conn.execute(query, params).fetchall()

    # Convert to list of dicts
    columns = [
        "config_id",
        "received_at",
        "sentence_type",
        "original_sentence",
        "instrument_type_name",
        "instrument_type_code",
        "head_id",
        "beam_count",
        "cell_count",
        "blanking_distance",
        "cell_size",
        "coord_system_name",
        "coord_system_code",
        "checksum",
    ]

    return [dict(zip(columns, row, strict=False)) for row in result]


def insert_sensor_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: dict) -> int:
    """Insert sensor data - routes to correct table based on sentence type."""
    sentence_type = data["sentence_type"]

    # Route to correct table based on data format
    if sentence_type == "PNORS":
        # DF100 - keep separate
        query = """
        INSERT INTO pnors_df100 (
            record_id, original_sentence, measurement_date, measurement_time,
            error_code, status_code, battery, sound_speed, heading, pitch, roll,
            pressure, temperature, analog1, analog2, checksum
        ) VALUES (
            nextval('pnors_df100_seq'), ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        ) RETURNING record_id;
        """
        params_df100 = (
            original_sentence,
            data["date"],
            data["time"],
            data.get("error_code"),
            data.get("status_code"),
            data.get("battery"),
            data.get("sound_speed"),
            data.get("heading"),
            data.get("pitch"),
            data.get("roll"),
            data.get("pressure"),
            data.get("temperature"),
            data.get("analog1"),
            data.get("analog2"),
            data.get("checksum"),
        )
        result = conn.execute(query, params_df100).fetchone()
    elif sentence_type in ("PNORS1", "PNORS2"):
        # DF101/102 consolidated into pnors12
        data_format = 101 if sentence_type == "PNORS1" else 102
        query = """
        INSERT INTO pnors12 (
            record_id, data_format, original_sentence, measurement_date, measurement_time,
            error_code, status_code, battery, sound_speed, heading_std_dev,
            heading, pitch, pitch_std_dev, roll, roll_std_dev,
            pressure, pressure_std_dev, temperature, checksum
        ) VALUES (
            nextval('pnors12_seq'), ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?
        ) RETURNING record_id;
        """
        params_df101 = (
            data_format,
            original_sentence,
            data["date"],
            data["time"],
            data.get("error_code"),
            data.get("status_code"),
            data.get("battery"),
            data.get("sound_speed"),
            data.get("heading_std_dev"),
            data.get("heading"),
            data.get("pitch"),
            data.get("pitch_std_dev"),
            data.get("roll"),
            data.get("roll_std_dev"),
            data.get("pressure"),
            data.get("pressure_std_dev"),
            data.get("temperature"),
            data.get("checksum"),
        )
        result = conn.execute(query, params_df101).fetchone()
    elif sentence_type in ("PNORS3", "PNORS4"):
        # DF103/104 consolidated into pnors34
        data_format = 103 if sentence_type == "PNORS3" else 104
        query = """
        INSERT INTO pnors34 (
            record_id, data_format, original_sentence, measurement_date, measurement_time,
            battery, sound_speed, heading, pitch, roll, pressure, temperature, checksum
        ) VALUES (
            nextval('pnors34_seq'), ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?
        ) RETURNING record_id;
        """
        params_df103 = (
            data_format,
            original_sentence,
            data["date"],
            data["time"],
            data.get("battery"),
            data.get("sound_speed"),
            data.get("heading"),
            data.get("pitch"),
            data.get("roll"),
            data.get("pressure"),
            data.get("temperature"),
            data.get("checksum"),
        )
        result = conn.execute(query, params_df103).fetchone()
    else:
        raise ValueError(f"Unknown sensor sentence type: {sentence_type}")

    conn.commit()
    return result[0] if result else -1


def insert_velocity_data(
    conn: duckdb.DuckDBPyConnection, original_sentence: str, data: dict
) -> int:
    """Insert velocity data - routes to correct table based on sentence type."""
    sentence_type = data["sentence_type"]

    # Route to correct table based on data format
    if sentence_type == "PNORC":
        # DF100 - keep separate
        query = """
        INSERT INTO pnorc_df100 (
            record_id, original_sentence, measurement_date, measurement_time,
            cell_index, vel1, vel2, vel3, vel4, speed, direction, amp_unit,
            amp1, amp2, amp3, amp4, corr1, corr2, corr3, corr4, checksum
        ) VALUES (
            nextval('pnorc_df100_seq'), ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?
        ) RETURNING record_id;
        """
        params_df100 = (
            original_sentence,
            data["date"],
            data["time"],
            data["cell_index"],
            data["vel1"],
            data["vel2"],
            data["vel3"],
            data["vel4"],
            data["speed"],
            data["direction"],
            data["amp_unit"],
            data["amp1"],
            data["amp2"],
            data["amp3"],
            data["amp4"],
            data["corr1"],
            data["corr2"],
            data["corr3"],
            data["corr4"],
            data.get("checksum"),
        )
        result = conn.execute(query, params_df100).fetchone()
    elif sentence_type in ("PNORC1", "PNORC2"):
        # DF101/102 consolidated into pnorc12
        data_format = 101 if sentence_type == "PNORC1" else 102
        query = """
        INSERT INTO pnorc12 (
            record_id, data_format, original_sentence, measurement_date, measurement_time,
            cell_index, cell_distance, vel1, vel2, vel3, vel4,
            amp1, amp2, amp3, amp4, corr1, corr2, corr3, corr4, checksum
        ) VALUES (
            nextval('pnorc12_seq'), ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?
        ) RETURNING record_id;
        """
        params_df101 = (
            data_format,
            original_sentence,
            data["date"],
            data["time"],
            data["cell_index"],
            data.get("distance"),
            data["vel1"],
            data["vel2"],
            data["vel3"],
            data["vel4"],
            data["amp1"],
            data["amp2"],
            data["amp3"],
            data["amp4"],
            data["corr1"],
            data["corr2"],
            data["corr3"],
            data["corr4"],
            data.get("checksum"),
        )
        result = conn.execute(query, params_df101).fetchone()
    elif sentence_type in ("PNORC3", "PNORC4"):
        # DF103/104 consolidated into pnorc34
        data_format = 103 if sentence_type == "PNORC3" else 104
        query = """
        INSERT INTO pnorc34 (
            record_id, data_format, original_sentence, measurement_date, measurement_time,
            cell_index, cell_distance, speed, direction, checksum
        ) VALUES (
            nextval('pnorc34_seq'), ?, ?, ?, ?,
            ?, ?, ?, ?, ?
        ) RETURNING record_id;
        """
        params_df103 = (
            data_format,
            original_sentence,
            data["date"],
            data["time"],
            data.get("cell_index", 1),
            data.get("distance"),
            data["speed"],
            data["direction"],
            data.get("checksum"),
        )
        result = conn.execute(query, params_df103).fetchone()
    else:
        raise ValueError(f"Unknown velocity sentence type: {sentence_type}")

    conn.commit()
    return result[0] if result else -1


def insert_header_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: dict) -> int:
    """Insert header data - routes to consolidated pnorh table."""
    sentence_type = data["sentence_type"]

    if sentence_type in ("PNORH3", "PNORH4"):
        data_format = 103 if sentence_type == "PNORH3" else 104
        query = """
        INSERT INTO pnorh (
            record_id, data_format, original_sentence,
            measurement_date, measurement_time,
            error_code, status_code, checksum
        ) VALUES (
            nextval('pnorh_seq'), ?, ?, ?, ?, ?, ?, ?
        ) RETURNING record_id;
        """
        params = (
            data_format,
            original_sentence,
            data["date"],
            data["time"],
            data["error_code"],
            data["status_code"],
            data.get("checksum"),
        )
    else:
        raise ValueError(f"Unknown header sentence type: {sentence_type}")

    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0] if result else -1


def insert_pnore_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: dict) -> int:
    """Insert wave energy density spectrum into pnore_data table.

    Args:
        conn: DuckDB connection
        original_sentence: Original NMEA sentence
        data: Dictionary from PNORE.to_dict() containing spectrum_basis,
              frequencies, and energy_densities array

    Returns:
        The generated record_id

    """
    query = """
    INSERT INTO pnore_data (
        record_id, original_sentence, sentence_type,
        measurement_date, measurement_time,
        spectrum_basis, start_frequency, step_frequency, num_frequencies,
        energy_densities, checksum
    ) VALUES (
        nextval('pnore_data_seq'), ?, ?,
        ?, ?,
        ?, ?, ?, ?,
        ?, ?
    ) RETURNING record_id;
    """

    # Serialize energy_densities list to JSON string
    energy_json = json.dumps(data["energy_densities"])

    params = (
        original_sentence,
        data["sentence_type"],
        data["date"],
        data["time"],
        data["spectrum_basis"],
        data["start_frequency"],
        data["step_frequency"],
        data["num_frequencies"],
        energy_json,
        data.get("checksum"),
    )

    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0] if result else -1


def insert_pnorw_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: dict) -> int:
    """Insert into pnorw_data table."""
    query = """
    INSERT INTO pnorw_data (
        record_id, original_sentence, sentence_type,
        measurement_date, measurement_time,
        spectrum_basis, processing_method,
        hm0, h3, h10, hmax,
        tm02, tp, tz,
        dir_tp, spr_tp, main_dir,
        uni_index, mean_pressure,
        num_no_detects, num_bad_detects,
        near_surface_speed, near_surface_dir,
        wave_error_code, checksum
    ) VALUES (
        nextval('pnorw_data_seq'), ?, ?,
        ?, ?,
        ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?,
        ?, ?, ?,
        ?, ?,
        ?, ?,
        ?, ?,
        ?, ?
    ) RETURNING record_id;
    """
    params = (
        original_sentence,
        data["sentence_type"],
        data["date"],
        data["time"],
        data.get("spectrum_basis"),
        data.get("processing_method"),
        data.get("hm0"),
        data.get("h3"),
        data.get("h10"),
        data.get("hmax"),
        data.get("tm02"),
        data.get("tp"),
        data.get("tz"),
        data.get("dir_tp"),
        data.get("spr_tp"),
        data.get("main_dir"),
        data.get("uni_index"),
        data.get("mean_pressure"),
        data.get("num_no_detects"),
        data.get("num_bad_detects"),
        data.get("near_surface_speed"),
        data.get("near_surface_dir"),
        data.get("wave_error_code"),
        data.get("checksum"),
    )
    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0] if result else -1


def insert_pnorb_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: dict) -> int:
    """Insert PNORB wave band parameters into pnorb_data table.

    Args:
        conn: DuckDB connection
        original_sentence: Original NMEA sentence
        data: Dictionary from PNORB.to_dict() containing wave band parameters

    Returns:
        The generated record_id

    """
    query = """
    INSERT INTO pnorb_data (
        record_id, original_sentence, sentence_type,
        measurement_date, measurement_time,
        spectrum_basis, processing_method,
        freq_low, freq_high,
        hmo, tm02, tp,
        dirtp, sprtp, main_dir,
        wave_error_code, checksum
    ) VALUES (
        nextval('pnorb_data_seq'), ?, ?,
        ?, ?,
        ?, ?,
        ?, ?,
        ?, ?, ?,
        ?, ?, ?,
        ?, ?
    ) RETURNING record_id;
    """

    params = (
        original_sentence,
        data["sentence_type"],
        data["date"],
        data["time"],
        data["spectrum_basis"],
        data["processing_method"],
        data["freq_low"],
        data["freq_high"],
        data["hm0"],
        data["tm02"],
        data["tp"],
        data["dir_tp"],
        data["spr_tp"],
        data["main_dir"],
        data["wave_error_code"],
        data.get("checksum"),
    )

    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0] if result else -1


def insert_pnorf_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: dict) -> int:
    """Insert Fourier coefficient spectra into pnorf_data table.

    Args:
        conn: DuckDB connection
        original_sentence: Original NMEA sentence
        data: Dictionary from PNORF.to_dict() containing coefficient_flag,
              spectrum_basis, frequencies, and coefficients array

    Returns:
        The generated record_id

    """
    import json

    query = """
    INSERT INTO pnorf_data (
        record_id, original_sentence, sentence_type,
        coefficient_flag, measurement_date, measurement_time,
        spectrum_basis, start_frequency, step_frequency, num_frequencies,
        coefficients, checksum
    ) VALUES (
        nextval('pnorf_data_seq'), ?, ?,
        ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?
    ) RETURNING record_id;
    """

    # Serialize coefficients list to JSON string
    coefficients_json = json.dumps(data["coefficients"])

    params = (
        original_sentence,
        data["sentence_type"],
        data["coefficient_flag"],
        data["date"],
        data["time"],
        data["spectrum_basis"],
        data["start_frequency"],
        data["step_frequency"],
        data["num_frequencies"],
        coefficients_json,
        data.get("checksum"),
    )
    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0] if result else -1


def insert_pnorwd_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: dict) -> int:
    """Insert wave directional spectra into pnorwd_data table.

    Args:
        conn: DuckDB connection
        original_sentence: Original NMEA sentence
        data: Dictionary from PNORWD.to_dict() containing direction_type,
              spectrum_basis, frequencies, and values array

    Returns:
        The generated record_id

    """
    import json

    query = """
    INSERT INTO pnorwd_data (
        record_id, original_sentence, sentence_type,
        direction_type, measurement_date, measurement_time,
        spectrum_basis, start_frequency, step_frequency, num_frequencies,
        values, checksum
    ) VALUES (
        nextval('pnorwd_data_seq'), ?, ?,
        ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?
    ) RETURNING record_id;
    """

    # Serialize values list to JSON string
    values_json = json.dumps(data["values"])

    params = (
        original_sentence,
        data["sentence_type"],
        data["direction_type"],
        data["date"],
        data["time"],
        data["spectrum_basis"],
        data["start_frequency"],
        data["step_frequency"],
        data["num_frequencies"],
        values_json,
        data.get("checksum"),
    )
    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0] if result else -1


def insert_pnora_data(conn: duckdb.DuckDBPyConnection, original_sentence: str, data: dict) -> int:
    """Insert into pnora_data table."""
    query = """
    INSERT INTO pnora_data (
        record_id, original_sentence, sentence_type,
        measurement_date, measurement_time,
        pressure, altimeter_distance, quality, status,
        pitch, roll,
        checksum
    ) VALUES (
        nextval('pnora_data_seq'), ?, ?,
        ?, ?,
        ?, ?, ?, ?,
        ?, ?,
        ?
    ) RETURNING record_id;
    """
    params = (
        original_sentence,
        data["sentence_type"],
        data["date"],
        data["time"],
        data["pressure"],
        data["distance"],
        data["quality"],
        data["status"],
        data["pitch"],
        data["roll"],
        data.get("checksum"),
    )
    result = conn.execute(query, params).fetchone()
    conn.commit()
    return result[0] if result else -1


def query_sensor_data(conn: duckdb.DuckDBPyConnection, limit: int = 100) -> list[dict[str, Any]]:
    """Query recent sensor data records (UNION from DF100, DF101/102, DF103/104)."""
    query = """
        SELECT record_id, received_at, 'DF100' as format, heading, pitch, roll,
               pressure, temperature FROM pnors_df100
        UNION ALL
        SELECT record_id, received_at,
               CASE WHEN data_format = 101 THEN 'DF101' ELSE 'DF102' END as format,
               heading, pitch, roll, pressure, temperature FROM pnors12
        UNION ALL
        SELECT record_id, received_at,
               CASE WHEN data_format = 103 THEN 'DF103' ELSE 'DF104' END as format,
               heading, pitch, roll, pressure, temperature FROM pnors34
        ORDER BY received_at DESC
        LIMIT ?
    """
    results = conn.execute(query, [limit]).fetchall()
    columns = [
        "record_id",
        "received_at",
        "format",
        "heading",
        "pitch",
        "roll",
        "pressure",
        "temperature",
    ]
    return [dict(zip(columns, row, strict=False)) for row in results]


def query_velocity_data(conn: duckdb.DuckDBPyConnection, limit: int = 100) -> list[dict[str, Any]]:
    """Query recent velocity data records (from DF100 and DF101/102)."""
    # Note: DF103/104 are averaged current, not velocity profiles, so excluded here
    query = """
        SELECT record_id, received_at, 'DF100' as format, cell_index, vel1, vel2,
               vel3, vel4 FROM pnorc_df100
        UNION ALL
        SELECT record_id, received_at,
               CASE WHEN data_format = 101 THEN 'DF101' ELSE 'DF102' END as format,
               cell_index, vel1, vel2, vel3, vel4 FROM pnorc12
        ORDER BY received_at DESC
        LIMIT ?
    """
    results = conn.execute(query, [limit]).fetchall()
    columns = ["record_id", "received_at", "format", "cell_index", "vel1", "vel2", "vel3", "vel4"]
    return [dict(zip(columns, row, strict=False)) for row in results]


def query_header_data(conn: duckdb.DuckDBPyConnection, limit: int = 100) -> list[dict[str, Any]]:
    """Query recent header data records (DF103/104) from consolidated pnorh table."""
    query = """
        SELECT record_id, received_at,
               CASE WHEN data_format = 103 THEN 'DF103' ELSE 'DF104' END as format,
               error_code, status_code
        FROM pnorh
        ORDER BY received_at DESC
        LIMIT ?
    """
    results = conn.execute(query, [limit]).fetchall()
    columns = ["record_id", "received_at", "format", "error_code", "status_code"]
    return [dict(zip(columns, row, strict=False)) for row in results]


def query_pnore_data(conn: duckdb.DuckDBPyConnection, limit: int = 100) -> list[dict[str, Any]]:
    """Query recent PNORE wave energy density records."""
    cols = conn.execute("DESCRIBE pnore_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM pnore_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row, strict=False)) for row in results]


# Backwards compatibility aliases
insert_echo_data = insert_pnore_data
query_echo_data = query_pnore_data


def query_pnorw_data(conn: duckdb.DuckDBPyConnection, limit: int = 100) -> list[dict[str, Any]]:
    """Query recent wave height/period records."""
    cols = conn.execute("DESCRIBE pnorw_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM pnorw_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row, strict=False)) for row in results]


def query_pnorb_data(conn: duckdb.DuckDBPyConnection, limit: int = 100) -> list[dict[str, Any]]:
    """Query recent bottom track records."""
    cols = conn.execute("DESCRIBE pnorb_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM pnorb_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row, strict=False)) for row in results]


def query_pnorf_data(conn: duckdb.DuckDBPyConnection, limit: int = 100) -> list[dict[str, Any]]:
    """Query recent frequency records."""
    cols = conn.execute("DESCRIBE pnorf_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM pnorf_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row, strict=False)) for row in results]


def query_pnorwd_data(conn: duckdb.DuckDBPyConnection, limit: int = 100) -> list[dict[str, Any]]:
    """Query recent wave directional records."""
    cols = conn.execute("DESCRIBE pnorwd_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM pnorwd_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row, strict=False)) for row in results]


def query_pnora_data(conn: duckdb.DuckDBPyConnection, limit: int = 100) -> list[dict[str, Any]]:
    """Query recent altitude records."""
    cols = conn.execute("DESCRIBE pnora_data").fetchall()
    col_names = [c[0] for c in cols]
    results = conn.execute(f"SELECT * FROM pnora_data LIMIT {limit}").fetchall()
    return [dict(zip(col_names, row, strict=False)) for row in results]


def expand_energy_densities(
    conn: duckdb.DuckDBPyConnection, limit: int = 100
) -> list[dict[str, Any]]:
    """Expand PNORE energy densities into long format with frequency axis.

    Uses DuckDB's unnest to efficiently expand JSON arrays into individual rows.
    """
    query = """
        SELECT
            record_id,
            received_at,
            measurement_date,
            measurement_time,
            UNNEST(energy_densities::DOUBLE[]) as energy,
            start_frequency + (generate_subscripts(energy_densities::DOUBLE[], 1) - 1)
                * step_frequency as frequency
        FROM pnore_data
        ORDER BY received_at DESC, frequency ASC
        LIMIT ?
    """
    results = conn.execute(query, [limit]).fetchall()
    columns = [
        "record_id",
        "received_at",
        "measurement_date",
        "measurement_time",
        "energy",
        "frequency",
    ]
    return [dict(zip(columns, row, strict=False)) for row in results]


def expand_coefficients(conn: duckdb.DuckDBPyConnection, limit: int = 100) -> list[dict[str, Any]]:
    """Expand PNORF Fourier coefficients into long format."""
    query = """
        SELECT
            record_id,
            received_at,
            coefficient_flag,
            measurement_date,
            measurement_time,
            UNNEST(coefficients::DOUBLE[]) as coefficient_value,
            start_frequency + (generate_subscripts(coefficients::DOUBLE[], 1) - 1)
                * step_frequency as frequency
        FROM pnorf_data
        ORDER BY received_at DESC, coefficient_flag, frequency ASC
        LIMIT ?
    """
    results = conn.execute(query, [limit]).fetchall()
    columns = [
        "record_id",
        "received_at",
        "coefficient_flag",
        "measurement_date",
        "measurement_time",
        "coefficient_value",
        "frequency",
    ]
    return [dict(zip(columns, row, strict=False)) for row in results]


def expand_pnorwd_values(conn: duckdb.DuckDBPyConnection, limit: int = 100) -> list[dict[str, Any]]:
    """Expand PNORWD directional spectrum values into long format."""
    query = """
        SELECT
            record_id,
            received_at,
            direction_type,
            measurement_date,
            measurement_time,
            UNNEST(values::DOUBLE[]) as direction_value,
            start_frequency + (generate_subscripts(values::DOUBLE[], 1) - 1)
                * step_frequency as frequency
        FROM pnorwd_data
        ORDER BY received_at DESC, direction_type, frequency ASC
        LIMIT ?
    """
    results = conn.execute(query, [limit]).fetchall()
    columns = [
        "record_id",
        "received_at",
        "direction_type",
        "measurement_date",
        "measurement_time",
        "direction_value",
        "frequency",
    ]
    return [dict(zip(columns, row, strict=False)) for row in results]
