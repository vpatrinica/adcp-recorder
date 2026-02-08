import duckdb

from adcp_recorder.db.migration import create_new_schema


def test_create_new_schema_default():
    conn = duckdb.connect(":memory:")
    # Call with default (schema_sql=None) to cover lines 512-514
    create_new_schema(conn)
    # Verify a table from ALL_SCHEMA_SQL exists
    res = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'raw_lines'"
    ).fetchone()
    assert res is not None
    assert res[0] > 0
    conn.close()
