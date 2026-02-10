
import duckdb
from datetime import datetime, timedelta, timezone
import os

def check_timezone():
    print(f"Local now: {datetime.now()}")
    print(f"UTC now: {datetime.utcnow()}")
    
    # Check astimezone behavior
    local_now = datetime.now()
    aware_local = local_now.astimezone()
    print(f"Aware local: {aware_local}")
    print(f"Timezone name: {aware_local.tzinfo}")
    
    # Convert to UTC
    if aware_local.tzinfo:
        utc_converted = aware_local.astimezone(timezone.utc)
        print(f"Converted to UTC: {utc_converted}")
    else:
        print("No timezone info available on local time")
    
    # Check DuckDB behavior
    conn = duckdb.connect()
    # Create test table
    # DuckDB TIMESTAMP is microseconds, naive
    conn.execute("CREATE TABLE test (ts TIMESTAMP)")
    
    # Insert UTC time (naive)
    utc_now_naive = datetime.utcnow()
    conn.execute("INSERT INTO test VALUES (?)", [utc_now_naive])
    
    print(f"Inserted UTC naive: {utc_now_naive}")
    
    # Query with naive local (future relative to UTC)
    local_now_naive = datetime.now()
    # If local is ahead of UTC (e.g. Berlin +1), local_now > utc_now
    # Query: ts >= local_now_naive
    # Should be False if we want "recent" data but filter is in future
    res = conn.execute("SELECT * FROM test WHERE ts >= ?", [local_now_naive]).fetchall()
    print(f"Query with naive local ({local_now_naive}): {res}")
    
    # Query with naive UTC
    # Query: ts >= utc_now_naive - 1s
    res = conn.execute("SELECT * FROM test WHERE ts >= ?", [utc_now_naive - timedelta(seconds=1)]).fetchall()
    print(f"Query with naive UTC ({utc_now_naive - timedelta(seconds=1)}): {res}")
    
    # Query with aware UTC
    utc_aware = datetime.now(timezone.utc)
    try:
        res = conn.execute("SELECT * FROM test WHERE ts >= ?", [utc_aware - timedelta(seconds=1)]).fetchall()
        print(f"Query with aware UTC ({utc_aware - timedelta(seconds=1)}): {res}")
    except Exception as e:
        print(f"Query with aware UTC failed: {e}")

if __name__ == "__main__":
    check_timezone()
