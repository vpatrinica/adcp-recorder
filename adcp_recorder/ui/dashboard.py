"""Advanced Streamlit dashboard for ADCP data visualization and analysis.

This is a multi-page application providing:
- Data Explorer: Browse and filter data from all sources
- Plot Builder: Create custom visualizations
- Dashboard Editor: Configure and save custom dashboards
- Custom Dashboards: View saved dashboard configurations
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

import streamlit as st

from adcp_recorder.config import RecorderConfig
from adcp_recorder.db import DatabaseManager
from adcp_recorder.ui.components import (
    render_amplitude_heatmap,
    render_directional_spectrum,
    render_energy_heatmap,
    render_fourier_spectrum,
    render_table_view,
    render_time_series,
    render_velocity_profile,
)
from adcp_recorder.ui.components.file_browser import render_file_browser
from adcp_recorder.ui.config import DashboardConfig, PanelType
from adcp_recorder.ui.data_layer import DataLayer
from adcp_recorder.ui.pages import (
    render_dashboard_editor,
    render_data_explorer,
    render_plot_builder,
)
from adcp_recorder.ui.parquet_data_layer import ParquetDataLayer


class DataLayerProtocol(Protocol):
    """Protocol for data layer compatibility."""

    def query(
        self,
        view_name: str,
        columns: list[str] | None = None,
        limit: int = 100,
        order_by: str | None = None,
        order_desc: bool = True,
    ) -> list[dict[str, Any]]: ...

    def get_column_info(self, view_name: str) -> list[tuple[str, str]]: ...

    def execute_sql(self, sql: str) -> list[dict[str, Any]]: ...


# Page configuration
st.set_page_config(
    page_title="ADCP Analysis Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS to hide the Deploy button and other elements
st.markdown(
    """
    <style>
    .stDeployButton {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_db() -> DatabaseManager:
    """Initialize database connection (cached)."""
    config = RecorderConfig.load()
    print(config)
    db_dir = Path(config.output_dir) / "db"
    db_path = config.db_path or (db_dir / "adcp.duckdb")
    return DatabaseManager(str(db_path))


@st.cache_resource
def get_data_layer(_db: DatabaseManager) -> DataLayer:
    """Initialize data layer (cached)."""
    return DataLayer(_db.get_connection())


def get_parquet_layer(config: RecorderConfig | None = None) -> ParquetDataLayer:
    """Get or create the ParquetDataLayer from session state."""
    if "parquet_layer" not in st.session_state:
        st.session_state.parquet_layer = ParquetDataLayer()
    layer = st.session_state.parquet_layer

    # Set default path from config if not already set
    if config and "parquet_default_set" not in st.session_state:
        default_dir = config.output_dir
        if default_dir:
            st.session_state.parquet_data_dir = default_dir
            st.session_state.parquet_default_set = True

    return layer


def main() -> None:
    """Run the main dashboard entry point."""
    # Sidebar navigation
    st.sidebar.title("🌊 ADCP Dashboard")
    st.sidebar.caption("Advanced Data Visualization")

    # Data Source Selector
    st.sidebar.divider()
    st.sidebar.subheader("📁 Data Source")

    data_source = st.sidebar.radio(
        "Select data source:",
        options=["Parquet Files", "DuckDB (configured)"],
        index=0,  # Default to Parquet Files
        key="data_source_selector",
        label_visibility="collapsed",
    )

    # Determine which data layer to use
    data_layer: DataLayer

    if data_source == "Parquet Files":
        try:
            config = RecorderConfig.load()
            parquet_layer = get_parquet_layer(config)

            # Auto-load data on first visit to parquet mode
            if "parquet_auto_loaded" not in st.session_state:
                st.session_state.parquet_auto_loaded = False

            # Show file browser - collapsed by default
            with st.sidebar.expander("📂 Parquet File Browser", expanded=False):
                render_file_browser(parquet_layer, key="sidebar_browser")

                # Show loaded views info
                if parquet_layer.get_loaded_views():
                    st.success(f"✓ Loaded: {', '.join(parquet_layer.get_loaded_views())}")

                # Show any writer faults
                faults = parquet_layer.get_writer_faults()
                if faults:
                    st.warning(f"⚠️ {len(faults)} file(s) stuck in writing state")

            # Auto-load data if not already done and directory is set
            if (
                not st.session_state.parquet_auto_loaded
                and "parquet_data_dir" in st.session_state
                and st.session_state.parquet_data_dir
            ):
                try:
                    parquet_layer.set_data_directory(st.session_state.parquet_data_dir)
                    structure = parquet_layer.get_file_structure()
                    if structure and structure.record_types:
                        parquet_layer.load_data()  # Load all available data
                        st.session_state.parquet_auto_loaded = True
                except Exception as load_err:
                    st.sidebar.warning(f"⚠️ Could not auto-load data: {load_err}")

            # Use parquet layer for data access
            data_layer = parquet_layer
        except Exception as e:
            st.sidebar.error("❌ Parquet Data Error")
            st.error(
                f"""
                ### 📁 Parquet Data Access Error

                Could not access the Parquet data files. This usually happens when:

                1. **File is locked** - Another application may be writing to the files
                2. **Directory not found** - Check that the data directory exists
                3. **Permission denied** - Check file permissions

                **Error details:** `{e}`

                **Suggestion:** Check that no other processes are writing to the files,
                or try switching to a different data directory.
                """
            )
            # Fallback to empty parquet layer
            parquet_layer = ParquetDataLayer()
            data_layer = parquet_layer
    else:
        # Only initialize DuckDB connection when DuckDB mode is selected
        try:
            db = get_db()
            duckdb_layer = get_data_layer(db)
            data_layer = duckdb_layer
            st.sidebar.caption(f"📁 DB: {db.db_path}")
        except Exception as e:
            st.sidebar.error("❌ DuckDB Connection Failed")
            st.error(
                f"""
                ### 🔒 Database Connection Error

                Could not connect to the DuckDB database. This usually happens when:

                1. **Another process is using the database** - Check for running scripts
                2. **Database file is locked** - Try restarting or killing stale processes
                3. **Database doesn't exist** - Make sure the recorder has created data

                **Error details:** `{e}`

                **Suggestion:** Switch to **Parquet Files** mode in the sidebar,
                which doesn't require database locking.
                """
            )
            st.stop()

    # Navigation menu
    st.sidebar.divider()
    pages = {
        "📊 Data Explorer": "explorer",
        "📈 Plot Builder": "plot_builder",
        "⚙️ Dashboard Editor": "editor",
    }

    # Add saved dashboards to navigation
    saved_dashboards = DashboardConfig.list_dashboards()
    if saved_dashboards:
        st.sidebar.subheader("📋 My Dashboards")
        for dash_name in saved_dashboards:
            pages[f"  📊 {dash_name}"] = f"dashboard:{dash_name}"

    selected = st.sidebar.radio(
        "Navigation",
        options=list(pages.keys()),
        label_visibility="collapsed",
    )

    page_key = pages.get(selected, "explorer")
    with st.sidebar.expander("⚡ Quick Actions", expanded=True):
        if st.button("🔄 Refresh Data", width=250):
            # use numerical width or "use_container_width=True" in newer streamlit,
            # but stick to compatible args if unsure, or just True
            st.cache_resource.clear()
            st.rerun()

        col_q1, col_q2 = st.columns(2)
        with col_q1:
            if st.button("📊 Raw Lines"):
                st.session_state["quick_view"] = "raw_lines"
                st.rerun()
        with col_q2:
            if st.button("⚠️ Errors"):
                st.session_state["quick_view"] = "parse_errors"
                st.rerun()

    # Footer
    st.sidebar.divider()
    st.sidebar.caption(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")

    # Handle quick view requests (Overlay)
    if st.session_state.get("quick_view"):
        source = st.session_state["quick_view"]
        st.divider()

        # Header with Close button
        col_h1, col_h2 = st.columns([6, 1])
        with col_h1:
            st.subheader(f"Quick View: {source}")
        with col_h2:
            if st.button("❌ Close", key="close_quick_view"):
                del st.session_state["quick_view"]
                st.rerun()

        render_table_view(data_layer, source, key_prefix=f"quick_{source}")
        st.divider()

    # Main content area
    if page_key == "explorer":
        render_data_explorer(data_layer)

    elif page_key == "plot_builder":
        render_plot_builder(data_layer)

    elif page_key == "editor":
        render_dashboard_editor(data_layer)

    elif page_key.startswith("dashboard:"):
        dashboard_name = page_key.split(":", 1)[1]
        render_saved_dashboard(data_layer, dashboard_name)


def render_saved_dashboard(data_layer: DataLayer, dashboard_name: str) -> None:
    """Render a saved dashboard configuration.

    Args:
        data_layer: DataLayer instance
        dashboard_name: Name of the saved dashboard

    """
    try:
        dashboard = DashboardConfig.load(dashboard_name)
    except FileNotFoundError:
        st.error(f"Dashboard '{dashboard_name}' not found.")
        return
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        return

    # Dashboard header
    st.title(f"📊 {dashboard.name}")
    if dashboard.description:
        st.caption(dashboard.description)

    # Time range selector (global for dashboard)
    col1, col2 = st.columns([1, 4])
    with col1:
        time_range = st.selectbox(
            "Time Range",
            options=["1h", "6h", "24h", "7d", "30d"],
            index=["1h", "6h", "24h", "7d", "30d"].index(dashboard.default_time_range)
            if dashboard.default_time_range in ["1h", "6h", "24h", "7d", "30d"]
            else 2,
            key=f"dash_{dashboard_name}_time",
        )

    st.divider()

    if not dashboard.panels:
        st.info("This dashboard has no panels configured. Go to Dashboard Editor to add panels.")
        return

    # Render panels in grid layout
    # Group panels by row
    rows: dict[int, list] = {}
    for panel in dashboard.panels:
        row = panel.position.row
        if row not in rows:
            rows[row] = []
        rows[row].append(panel)

    # Render each row
    for row_idx in sorted(rows.keys()):
        row_panels = sorted(rows[row_idx], key=lambda p: p.position.col)

        # Calculate column widths based on panel widths
        total_width = sum(p.position.width for p in row_panels)
        col_ratios = [p.position.width / total_width for p in row_panels]

        cols = st.columns(col_ratios)

        for col_container, panel in zip(cols, row_panels, strict=False):
            with col_container:
                if panel.title:
                    st.subheader(panel.title)

                # Merge panel config with global time range
                panel_config = dict(panel.config)
                panel_config["time_range"] = time_range

                # Render based on panel type
                try:
                    render_panel(data_layer, panel, panel_config)
                except Exception as e:
                    st.error(f"Error rendering {panel.id}: {e}")


def render_panel(
    data_layer: DataLayer,
    panel: Any,
    config: dict[str, Any],
) -> None:
    """Render a single dashboard panel.

    Args:
        data_layer: DataLayer instance
        panel: PanelConfig object
        config: Merged configuration dict

    """
    key_prefix = f"panel_{panel.id}"

    if panel.type == PanelType.TABLE:
        source = config.get("data_source", "pnors_df100")
        render_table_view(data_layer, source, config, key_prefix)

    elif panel.type == PanelType.TIME_SERIES:
        render_time_series(data_layer, config, key_prefix)

    elif panel.type == PanelType.VELOCITY_PROFILE:
        render_velocity_profile(data_layer, config, key_prefix)

    elif panel.type == PanelType.SPECTRUM:
        render_fourier_spectrum(data_layer, config, key_prefix)

    elif panel.type == PanelType.HEATMAP:
        render_energy_heatmap(data_layer, config, key_prefix)

    elif panel.type == PanelType.AMPLITUDE_HEATMAP:
        render_amplitude_heatmap(data_layer, config, key_prefix)

    elif panel.type == PanelType.POLAR:
        render_directional_spectrum(data_layer, config, key_prefix)

    else:
        st.warning(f"Unknown panel type: {panel.type}")


if __name__ == "__main__":
    main()
