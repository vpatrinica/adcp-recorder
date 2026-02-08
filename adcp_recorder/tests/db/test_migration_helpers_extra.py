from unittest.mock import MagicMock

from adcp_recorder.db.migration import drop_all_indexes, drop_all_views


def test_drop_all_views_exception():
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = Exception("View error")
    # Should not raise, just log warning
    drop_all_views(mock_conn)


def test_drop_all_indexes_exception():
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = Exception("Index error")
    # Should not raise, just log warning
    drop_all_indexes(mock_conn, "some_table")
