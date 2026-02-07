from unittest.mock import MagicMock

import duckdb
import pytest

from adcp_recorder.db.migration import fix_pnorb_typos


def test_fix_pnorb_typos_migration():
    # 1. Setup a connection with the table in BROKEN state (using hmo)
    conn = duckdb.connect(":memory:")
    conn.execute("""
        CREATE TABLE pnorb_data (
            record_id BIGINT PRIMARY KEY,
            hmo DECIMAL(5,2),
            dirtp DECIMAL(5,2),
            sprtp DECIMAL(5,2)
        )
    """)
    conn.execute(
        "INSERT INTO pnorb_data (record_id, hmo, dirtp, sprtp) VALUES (1, 1.2, 180.0, 10.0)"
    )

    # 2. Run the fix
    result = fix_pnorb_typos(conn)
    assert result == 1

    # 3. Verify columns are renamed
    cols = [row[1] for row in conn.execute("PRAGMA table_info(pnorb_data)").fetchall()]
    assert "hm0" in cols
    assert "dir_tp" in cols
    assert "spr_tp" in cols
    assert "hmo" not in cols
    assert "dirtp" not in cols
    assert "sprtp" not in cols

    # 4. Verify data is preserved
    row = conn.execute("SELECT hm0, dir_tp, spr_tp FROM pnorb_data").fetchone()
    assert row is not None
    assert float(row[0]) == pytest.approx(1.2)
    assert float(row[1]) == pytest.approx(180.0)
    assert float(row[2]) == pytest.approx(10.0)

    # 5. Run again - should do nothing and return 0
    result = fix_pnorb_typos(conn)
    assert result == 0


def test_fix_pnorb_typos_no_table():
    conn = duckdb.connect(":memory:")
    result = fix_pnorb_typos(conn)
    assert result == 0


def test_fix_pnorb_typos_exception():
    mock_conn = MagicMock()

    def side_effect(sql, *args, **kwargs):
        if "information_schema.tables" in sql:
            res = MagicMock()
            res.fetchone.return_value = (1,)
            return res
        if "PRAGMA table_info" in sql:
            raise Exception("Pragma error")
        return MagicMock()

    mock_conn.execute.side_effect = side_effect

    result = fix_pnorb_typos(mock_conn)
    assert result == 0


def test_fix_pnorb_typos_rename_exception():
    mock_conn = MagicMock()

    def side_effect(sql, *args, **kwargs):
        if "information_schema.tables" in sql:
            res = MagicMock()
            res.fetchone.return_value = (1,)
            return res
        if "PRAGMA table_info" in sql:
            res = MagicMock()
            res.fetchall.return_value = [(0, "hmo", "DECIMAL", 0, None, 0)]
            return res
        if "ALTER TABLE" in sql:
            raise Exception("Rename error")
        return MagicMock()

    mock_conn.execute.side_effect = side_effect

    result = fix_pnorb_typos(mock_conn)
    assert result == 1
