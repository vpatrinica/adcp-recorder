"""Additional tests for ParquetDataLayer.resolve_source_name behavior.

These focus on preserving numeric suffixes and mapping common DuckDB-style
names to the corresponding `pq_` view when present.
"""

from adcp_recorder.ui.parquet_data_layer import ParquetDataLayer


def test_resolve_preserves_numeric_suffixes():
    layer = ParquetDataLayer()

    # Simulate loaded views that include suffix-preserving names
    layer._loaded_views.update({"pq_pnors1", "pq_pnorc12", "pq_pnors"})

    # Exact pq_ names return themselves
    assert layer.resolve_source_name("pq_pnors1") == "pq_pnors1"
    assert layer.resolve_source_name("pq_pnorc12") == "pq_pnorc12"

    # DuckDB-style and short names should prefer suffix-preserving views
    assert layer.resolve_source_name("pnors1") == "pq_pnors1"
    assert layer.resolve_source_name("pnorc12") == "pq_pnorc12"


def test_resolve_duckdb_and_df100_mapping():
    layer = ParquetDataLayer()
    layer._loaded_views.update({"pq_pnors", "pq_pnorc", "pq_test"})

    # DuckDB-style *_data names map to pq_ prefix
    assert layer.resolve_source_name("pnors_data") == "pq_pnors"
    assert layer.resolve_source_name("pnorc_data") == "pq_pnorc"

    # Legacy style with df100 suffix should map to base pq_pnors when present
    assert layer.resolve_source_name("pnors_df100") == "pq_pnors"

    # Non-existing names return None
    assert layer.resolve_source_name("unknown_source") is None
