"""File browser component for Parquet file selection in Streamlit dashboard.

Provides a hierarchical file browser with directory selection and
multi-select capability for Parquet files.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any

try:
    import streamlit as st

    HAS_STREAMLIT = True
except ImportError:  # pragma: no cover
    HAS_STREAMLIT = False
    st = None  # type: ignore

from adcp_recorder.ui.parquet_data_layer import ParquetDataLayer, ParquetDirectory


@dataclass
class FileSelection:
    """Represents the current file selection state."""

    data_directory: str
    selected_record_types: list[str]
    start_date: date | None
    end_date: date | None


def render_directory_selector(
    key: str = "data_dir",
    default_path: str = "",
) -> str:
    """Render a directory path input.

    Args:
        key: Streamlit widget key
        default_path: Default directory path

    Returns:
        The entered directory path

    """
    if not HAS_STREAMLIT or st is None:
        return default_path

    st.subheader("📂 Data Directory")

    col1, col2 = st.columns([4, 1])

    with col1:
        path = st.text_input(
            "Parquet data directory",
            value=default_path,
            key=f"{key}_input",
            help="Path to directory containing Parquet files",
        )

    with col2:
        if st.button("🔄", key=f"{key}_refresh", help="Refresh file list"):
            # Clear cache to force rescan
            if "parquet_data_layer" in st.session_state:
                st.session_state.parquet_data_layer.refresh()

    return path


def render_record_type_selector(
    available_types: list[str],
    key: str = "record_types",
) -> list[str]:
    """Render record type multi-select.

    Args:
        available_types: List of available record types
        key: Streamlit widget key

    Returns:
        List of selected record types

    """
    if not HAS_STREAMLIT or st is None:
        return available_types

    if not available_types:
        st.info("No record types available. Check the data directory.")
        return []

    st.subheader("📊 Record Types")

    # Checkbox for select all
    select_all = st.checkbox("Select all", value=True, key=f"{key}_all")

    if select_all:
        return available_types

    selected = st.multiselect(
        "Select record types",
        options=available_types,
        default=available_types[: min(3, len(available_types))],
        key=f"{key}_select",
    )

    return selected


def render_date_range_selector(
    available_dates: list[date],
    key: str = "date_range",
) -> tuple[date | None, date | None]:
    """Render date range selector.

    Args:
        available_dates: List of available dates (sorted descending)
        key: Streamlit widget key

    Returns:
        Tuple of (start_date, end_date)

    """
    if not HAS_STREAMLIT or st is None:
        if available_dates:
            return (available_dates[-1], available_dates[0])
        return (None, None)

    if not available_dates:
        st.info("No dates available.")
        return (None, None)

    st.subheader("📅 Date Range")

    # Show available range
    min_date = min(available_dates)
    max_date = max(available_dates)

    col1, col2 = st.columns(2)

    with col1:
        start = st.date_input(
            "Start date",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key=f"{key}_start",
        )

    with col2:
        end = st.date_input(
            "End date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key=f"{key}_end",
        )

    # Convert to date objects (streamlit returns date)
    start_date = start if isinstance(start, date) else None
    end_date = end if isinstance(end, date) else None

    return (start_date, end_date)


def render_file_tree(
    structure: ParquetDirectory,
    key: str = "file_tree",
) -> dict[str, list[date]]:
    """Render a hierarchical file tree view.

    Args:
        structure: ParquetDirectory with file structure
        key: Streamlit widget key

    Returns:
        Dict mapping record type to list of selected dates

    """
    if not HAS_STREAMLIT or st is None:
        return {}

    if not structure.record_types:
        st.info("No Parquet files found in the selected directory.")
        return {}

    st.subheader("📁 File Structure")

    selection: dict[str, list[date]] = {}

    for rec_type in sorted(structure.record_types.keys()):
        dates_dict = structure.record_types[rec_type]
        file_count = sum(len(files) for files in dates_dict.values())

        with st.expander(f"**{rec_type}** ({file_count} files)", expanded=False):
            dates_sorted = sorted(dates_dict.keys(), reverse=True)

            selected_dates = st.multiselect(
                f"Select dates for {rec_type}",
                options=dates_sorted,
                default=dates_sorted[: min(7, len(dates_sorted))],
                format_func=lambda d: f"{d.isoformat()} ({len(dates_dict.get(d, []))} files)",
                key=f"{key}_{rec_type}_dates",
            )

            if selected_dates:
                selection[rec_type] = selected_dates

    return selection


def render_file_browser(
    data_layer: ParquetDataLayer,
    key: str = "browser",
) -> FileSelection | None:
    """Render the complete file browser component.

    Args:
        data_layer: ParquetDataLayer instance
        key: Base key for Streamlit widgets

    Returns:
        FileSelection with user's choices, or None if no valid selection

    """
    if not HAS_STREAMLIT or st is None:
        return None

    # Directory selection
    default_dir = ""
    if "parquet_data_dir" in st.session_state:
        default_dir = st.session_state.parquet_data_dir

    data_dir = render_directory_selector(
        key=f"{key}_dir",
        default_path=default_dir,
    )

    if not data_dir:
        st.warning("Please enter a data directory path.")
        return None

    # Store in session state
    st.session_state.parquet_data_dir = data_dir

    # Only update data layer if directory actually changed
    # This prevents clearing loaded views on every render
    current_dir_key = f"{key}_current_data_dir"
    if current_dir_key not in st.session_state or st.session_state[current_dir_key] != data_dir:
        data_layer.set_data_directory(data_dir)
        st.session_state[current_dir_key] = data_dir

    # Get file structure
    structure = data_layer.get_file_structure()

    if not structure or not structure.record_types:
        st.error(f"No Parquet files found in: {data_dir}")
        return None

    # Show stats
    total_files = sum(
        len(files) for dates in structure.record_types.values() for files in dates.values()
    )
    st.caption(
        f"Found {len(structure.record_types)} record types, "
        f"{len(structure.get_all_dates())} dates, {total_files} files"
    )

    # Record type selection
    available_types = sorted(structure.record_types.keys())
    selected_types = render_record_type_selector(
        available_types,
        key=f"{key}_types",
    )

    # Date range selection
    available_dates = structure.get_all_dates()
    start_date, end_date = render_date_range_selector(
        available_dates,
        key=f"{key}_dates",
    )

    # Load data button
    if st.button("📥 Load Selected Data", key=f"{key}_load", type="primary"):
        with st.spinner("Loading Parquet files..."):
            try:
                result = data_layer.load_data(
                    record_types=selected_types,
                    start_date=start_date,
                    end_date=end_date,
                )

                if result:
                    st.success(
                        f"Loaded {len(result)} views: "
                        + ", ".join(f"{k} ({v} rows)" for k, v in result.items())
                    )
                else:
                    st.warning("No data loaded. Check your selection.")
            except Exception as e:
                error_msg = str(e).lower()
                if "lock" in error_msg or "busy" in error_msg:
                    st.error(
                        "🔒 **File is locked** - Another process may be writing data. "
                        "Wait a moment and try again."
                    )
                elif "permission" in error_msg or "access" in error_msg:
                    st.error(
                        "🚫 **Permission denied** - Cannot access some files. "
                        "Check file permissions."
                    )
                else:
                    st.error(f"❌ **Load failed:** {e}")

    return FileSelection(
        data_directory=data_dir,
        selected_record_types=selected_types,
        start_date=start_date,
        end_date=end_date,
    )


def get_selection_summary(selection: FileSelection) -> dict[str, Any]:
    """Get a summary dict of the current selection.

    Args:
        selection: FileSelection object

    Returns:
        Dict with selection summary

    """
    return {
        "data_directory": selection.data_directory,
        "record_types": selection.selected_record_types,
        "start_date": selection.start_date.isoformat() if selection.start_date else None,
        "end_date": selection.end_date.isoformat() if selection.end_date else None,
    }
