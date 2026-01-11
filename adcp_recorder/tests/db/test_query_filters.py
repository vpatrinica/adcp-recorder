"""Targeted tests for query filters in adcp_recorder.db.operations.
"""

import pytest
from datetime import datetime, timedelta
from adcp_recorder.db.db import DatabaseManager
from adcp_recorder.db.operations import (
    insert_raw_line,
    query_raw_lines,
    insert_parse_error,
    query_parse_errors,
    insert_pnori_configuration,
    query_pnori_configurations
)

@pytest.fixture
def db(tmp_path):
    db_file = tmp_path / "test_queries.db"
    return DatabaseManager(str(db_file))

def test_query_raw_lines_filters(db):
    conn = db.get_connection()
    
    # Insert records with different properties
    now = datetime.now()
    past = now - timedelta(hours=1)
    future = now + timedelta(hours=1)
    
    insert_raw_line(conn, "$PNORI,1*00", parse_status="OK", record_type="PNORI")
    insert_raw_line(conn, "$PNORS,2*00", parse_status="FAIL", record_type="PNORS")
    
    # Test record_type filter
    results = query_raw_lines(conn, record_type="PNORI")
    assert len(results) == 1
    assert results[0]["record_type"] == "PNORI"
    
    # Test parse_status filter
    results = query_raw_lines(conn, parse_status="FAIL")
    assert len(results) == 1
    assert results[0]["record_type"] == "PNORS"
    
    # Test time filters (Note: received_at is set by DuckDB, so we can't easily set it to past)
    # But we can test that start_time=now matches and future doesn't.
    results = query_raw_lines(conn, start_time=now - timedelta(seconds=10))
    assert len(results) == 2
    
    results = query_raw_lines(conn, end_time=now - timedelta(seconds=10))
    assert len(results) == 0

def test_query_parse_errors_filters(db):
    conn = db.get_connection()
    now = datetime.now()
    
    insert_parse_error(conn, "bad data 1", "TYPE_A", "Error A")
    insert_parse_error(conn, "bad data 2", "TYPE_B", "Error B")
    
    results = query_parse_errors(conn, error_type="TYPE_A")
    assert len(results) == 1
    assert results[0]["error_type"] == "TYPE_A"
    
    results = query_parse_errors(conn, start_time=now - timedelta(seconds=10))
    assert len(results) >= 2
    
    results = query_parse_errors(conn, end_time=now - timedelta(seconds=10))
    assert len(results) == 0

def test_query_pnori_configurations_filters(db):
    conn = db.get_connection()
    now = datetime.now()
    
    config1 = {
        "sentence_type": "PNORI",
        "instrument_type_name": "Signature",
        "instrument_type_code": "4",
        "head_id": "H1",
        "beam_count": 4,
        "cell_count": 20,
        "blanking_distance": 0.2,
        "cell_size": 1.0,
        "coord_system_name": "ENU",
        "coord_system_code": "0",
        "checksum": "00"
    }
    config2 = config1.copy()
    config2["head_id"] = "H2"
    config2["sentence_type"] = "PNORI1"
    
    insert_pnori_configuration(conn, config1, "$PNORI...")
    insert_pnori_configuration(conn, config2, "$PNORI1...")
    
    results = query_pnori_configurations(conn, head_id="H1")
    assert len(results) == 1
    assert results[0]["head_id"] == "H1"
    
    results = query_pnori_configurations(conn, sentence_type="PNORI1")
    assert len(results) == 1
    assert results[0]["sentence_type"] == "PNORI1"
    
    results = query_pnori_configurations(conn, start_time=now - timedelta(seconds=10))
    assert len(results) == 2
    
    results = query_pnori_configurations(conn, end_time=now - timedelta(seconds=10))
    assert len(results) == 0
