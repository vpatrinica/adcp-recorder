"""Interactive table view component with column selection and filtering."""

from typing import Any

try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore

from adcp_recorder.ui.data_layer import DataLayer, DataSource


def render_table_view(
    data_layer: DataLayer,
    source_name: str,
    config: dict[str, Any] | None = None,
    key_prefix: str = "table",
) -> None:
    """Render an interactive data table with column selection and filtering.

    Args:
        data_layer: DataLayer instance for data access
        source_name: Name of the data source (table/view)
        config: Optional configuration dict with columns, limit, sortable, filterable
        key_prefix: Unique key prefix for Streamlit session state

    """
    if st is None:
        raise ImportError("Streamlit is required for this component.")
    config = config or {}

    # Get source metadata
    source = data_layer.get_source_metadata(source_name)
    if not source:
        st.error(f"Data source not found: {source_name}")
        return

    # Settings expander
    with st.expander("⚙️ Table Settings", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            limit = st.number_input(
                "Row limit",
                min_value=10,
                max_value=10000,
                value=config.get("limit", 100),
                step=50,
                key=f"{key_prefix}_limit",
            )

        with col2:
            available_columns = [c.name for c in source.columns]
            default_columns = config.get("columns") or available_columns[:10]

            selected_columns = st.multiselect(
                "Columns to display",
                options=available_columns,
                default=[c for c in default_columns if c in available_columns],
                key=f"{key_prefix}_columns",
            )

    # Ensure mandatory columns for filtering are always included
    for mandatory in ["record_type", "raw_sentence"]:
        if mandatory in available_columns and mandatory not in selected_columns:
            selected_columns.append(mandatory)

    if not selected_columns:
        selected_columns = available_columns[:5]

    # Filtering section
    filters_key = f"{key_prefix}_filters"
    if filters_key not in st.session_state:
        st.session_state[filters_key] = {}

    if config.get("filterable", True):
        with st.expander("🔍 Filters", expanded=False):
            filter_cols = st.columns(3)

            for i, col_name in enumerate(selected_columns):  # Show filter for all selected columns
                col_meta = source.get_column(col_name)
                if not col_meta:
                    continue

                with filter_cols[i % 3]:
                    if col_meta.column_type.value == "text":
                        # Use a separate key prefix for the widget vs the stored state logic
                        # to avoid Streamlit overwriting our tuple state with a string
                        widget_key = f"{key_prefix}_filter_widget_{col_name}"
                        filter_val = st.text_input(
                            f"Filter {col_name}",
                            key=widget_key,
                        )
                        state_key = f"{key_prefix}_filter_state_{col_name}"
                        if filter_val:
                            st.session_state[state_key] = ("contains", filter_val)
                        elif state_key in st.session_state:
                            del st.session_state[state_key]

    # Time range filter for timestamped sources
    time_range = "24h"
    start_time = None
    end_time = None

    if source.has_timestamp:
        time_range = st.selectbox(
            "Time range",
            options=["1h", "6h", "24h", "7d", "30d", "all", "Custom"],
            index=2,
            key=f"{key_prefix}_time_range",
        )

        if time_range == "Custom":
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                start_date = st.date_input("Start Date", key=f"{key_prefix}_start_date")
            with c2:
                start_time_val = st.time_input("Start Time", key=f"{key_prefix}_start_time")
            with c3:
                end_date = st.date_input("End Date", key=f"{key_prefix}_end_date")
            with c4:
                end_time_val = st.time_input("End Time", key=f"{key_prefix}_end_time")

            if start_date and end_date:
                from datetime import datetime

                start_time = datetime.combine(start_date, start_time_val)
                end_time = datetime.combine(end_date, end_time_val)
        elif time_range != "all":
            start_time = data_layer._parse_time_range(time_range)

    # Query data
    try:
        data = data_layer.query_data(
            source_name=source_name,
            columns=selected_columns,
            start_time=start_time,
            end_time=end_time,
            limit=int(limit),
        )
        # Apply client‑side filters stored in session_state
        if data:
            filtered = []
            for row in data:
                keep = True
                for col in selected_columns:
                    state_key = f"{key_prefix}_filter_state_{col}"
                    if state_key in st.session_state:
                        state = st.session_state[state_key]
                        if (
                            isinstance(state, (tuple, list))
                            and len(state) == 2
                            and state[0] == "contains"
                        ):
                            # op, val = state
                            val = state[1]
                            if val.lower() not in str(row.get(col, "")).lower():
                                keep = False
                                break
                if keep:
                    filtered.append(row)
            data = filtered

        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows Loaded", len(data))
        with col2:
            st.metric("Total Records", f"{source.record_count:,}")
        with col3:
            st.metric("Columns", len(selected_columns))

        # Display table
        if data:
            st.dataframe(
                data,
                width="stretch",
                hide_index=True,
            )

            # Export options
            export_col1, export_col2 = st.columns([1, 4])
            with export_col1:
                if st.button("📥 Export CSV", key=f"{key_prefix}_export"):
                    import csv
                    import io

                    output = io.StringIO()
                    if data:
                        writer = csv.DictWriter(output, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)

                    st.download_button(
                        label="Download CSV",
                        data=output.getvalue(),
                        file_name=f"{source_name}_export.csv",
                        mime="text/csv",
                        key=f"{key_prefix}_download",
                    )
        else:
            st.info("No data available for the selected filters.")

    except Exception as e:
        st.error(f"Error loading data: {e}")


def render_column_selector(
    source: DataSource,
    default_columns: list[str] | None = None,
    key: str = "col_select",
) -> list[str]:
    """Standalone column selector widget.

    Args:
        source: DataSource metadata
        default_columns: Initially selected columns
        key: Streamlit widget key

    Returns:
        List of selected column names

    """
    if st is None:
        raise ImportError("Streamlit is required for this component.")
    available = [c.name for c in source.columns]
    defaults = default_columns or available[:5]

    return st.multiselect(
        "Select columns",
        options=available,
        default=[c for c in defaults if c in available],
        key=key,
    )
