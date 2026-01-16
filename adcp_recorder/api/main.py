"""API layer for ADCP Recorder data access."""

import logging
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from adcp_recorder.config import RecorderConfig
from adcp_recorder.db import DatabaseManager, query_parse_errors, query_raw_lines

logger = logging.getLogger(__name__)

app = FastAPI(title="ADCP Recorder API", version="0.1.0")

# Global DB manager - will be initialized on startup or via dependency
_db_manager: DatabaseManager | None = None


def get_db():
    global _db_manager
    if _db_manager is None:
        config = RecorderConfig.load()
        db_dir = Path(config.output_dir) / "db"
        db_path = config.db_path or (db_dir / "adcp.duckdb")
        _db_manager = DatabaseManager(str(db_path))
    return _db_manager


class RecordResponse(BaseModel):
    line_id: int
    received_at: datetime
    raw_sentence: str
    parse_status: str
    record_type: str | None
    checksum_valid: bool | None
    error_message: str | None


class ErrorResponse(BaseModel):
    error_id: int
    received_at: datetime
    raw_sentence: str
    error_type: str
    error_message: str | None
    attempted_prefix: str | None


@app.get("/")
async def root():
    return {"message": "ADCP Recorder API is running", "version": "0.1.0"}


@app.get("/records", response_model=list[RecordResponse])
async def get_records(
    record_type: str | None = None,
    status: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
):
    db = get_db()
    conn = db.get_connection()
    try:
        records = query_raw_lines(conn, record_type=record_type, parse_status=status, limit=limit)
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/errors", response_model=list[ErrorResponse])
async def get_errors(error_type: str | None = None, limit: int = Query(100, ge=1, le=1000)):
    db = get_db()
    conn = db.get_connection()
    try:
        errors = query_parse_errors(conn, error_type=error_type, limit=limit)
        return errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ducklake/{prefix}")
async def get_ducklake_data(prefix: str, limit: int = 100):
    """Query data directly from Parquet views."""
    db = get_db()
    conn = db.get_connection()
    view_name = f"view_{prefix.lower()}"
    try:
        # Check if view exists
        res = conn.execute(f"SELECT * FROM {view_name} LIMIT {limit}").fetchall()
        # Convert results to list of dicts (need to fetch column names)
        cols = [d[0] for d in conn.description]
        return [dict(zip(cols, row)) for row in res]
    except Exception as e:
        if "does not exist" in str(e):
            raise HTTPException(status_code=404, detail=f"No DuckLake data for {prefix}")
        raise HTTPException(status_code=500, detail=str(e))
