"""Data Explorer page - Table-centric data exploration with filtering."""

import streamlit as st

from adcp_recorder.ui.components.table_view import render_table_view
from adcp_recorder.ui.data_layer import DataLayer


def render_data_explorer(data_layer: DataLayer) -> None:
    """Render the Data Explorer page.

    Args:
        data_layer: DataLayer instance for data access

    """
    st.header("📊 Data Explorer")
    st.caption("Browse and filter ADCP data from all available sources")

    # Get available sources grouped by category
    sources = data_layer.get_available_sources(include_views=True)

    if not sources:
        st.warning("No data sources available. Make sure the ADCP Recorder has captured some data.")
        return

    # Group sources by category
    categories: dict[str, list] = {}
    for source in sources:
        cat = source.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(source)

    # Source selection with category grouping
    col1, col2 = st.columns([2, 3])

    with col1:
        # Category filter
        category_options = ["All"] + sorted(categories.keys())
        selected_category = st.selectbox(
            "Category",
            options=category_options,
            key="explorer_category",
        )

    with col2:
        # Filter sources by category
        if selected_category == "All":
            filtered_sources = sources
        else:
            filtered_sources = categories.get(selected_category, [])

        source_options = {s.display_name: s.name for s in filtered_sources}

        if not source_options:
            st.warning("No sources in selected category.")
            return

        selected_display = st.selectbox(
            "Data Source",
            options=list(source_options.keys()),
            key="explorer_source",
        )
        selected_source = source_options.get(selected_display, "")

    if not selected_source:
        return

    # Source info
    source_meta = data_layer.get_source_metadata(selected_source)
    if source_meta:
        info_cols = st.columns(4)
        with info_cols[0]:
            st.metric("Total Records", f"{source_meta.record_count:,}")
        with info_cols[1]:
            st.metric("Columns", len(source_meta.columns))
        with info_cols[2]:
            st.metric("Category", source_meta.category)
        with info_cols[3]:
            st.metric("Has Timestamp", "✓" if source_meta.has_timestamp else "✗")

    st.divider()

    # Render the table view
    render_table_view(
        data_layer=data_layer,
        source_name=selected_source,
        key_prefix=f"explorer_{selected_source}",
    )

    # Quick stats for numeric columns
    if source_meta:
        numeric_cols = source_meta.get_numeric_columns()
        if numeric_cols:
            with st.expander("📈 Column Statistics", expanded=False):
                stat_cols = st.columns(min(4, len(numeric_cols)))
                for i, col_name in enumerate(numeric_cols[:8]):
                    try:
                        stats = data_layer.get_column_stats(selected_source, col_name)
                        if stats:
                            with stat_cols[i % 4]:
                                col_meta = source_meta.get_column(col_name)
                                unit = col_meta.unit if col_meta else ""
                                st.markdown(f"**{col_name}**")
                                st.text(f"Min: {stats.get('min', 'N/A'):.2f} {unit}")
                                st.text(f"Max: {stats.get('max', 'N/A'):.2f} {unit}")
                                st.text(f"Avg: {stats.get('avg', 'N/A'):.2f} {unit}")
                    except Exception:  # noqa: BLE001
                        # If stats fail for one column, just skip it quietly
                        pass
