"""Dashboard Editor page - Create and manage dashboard configurations."""

import streamlit as st

from adcp_recorder.ui.config import (
    DASHBOARD_TEMPLATES,
    DashboardConfig,
    LayoutConfig,
    PanelConfig,
    PanelPosition,
    PanelType,
    get_template,
)
from adcp_recorder.ui.data_layer import DataLayer


def render_dashboard_editor(data_layer: DataLayer) -> None:  # noqa: ARG001
    """Render the Dashboard Editor page.

    Args:
        data_layer: DataLayer instance for data access

    """
    st.header("⚙️ Dashboard Editor")
    st.caption("Create, configure, and manage custom dashboards")

    # Tabs for different editor sections
    tab1, tab2, tab3 = st.tabs(["📋 My Dashboards", "➕ Create New", "📦 Templates"])

    with tab1:
        _render_dashboard_list()

    with tab2:
        _render_create_dashboard()

    with tab3:
        _render_templates()


def _render_dashboard_list() -> None:
    """Render list of existing dashboards."""
    st.subheader("Saved Dashboards")

    dashboards = DashboardConfig.list_dashboards()

    if not dashboards:
        st.info("No dashboards saved yet. Create a new dashboard or use a template to get started.")
        return

    for dash_name in dashboards:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            try:
                dashboard = DashboardConfig.load(dash_name)

                with col1:
                    st.markdown(f"**{dashboard.name}**")
                    st.caption(dashboard.description or "No description")

                with col2:
                    st.metric("Panels", len(dashboard.panels))

                with col3:
                    if st.button("✏️ Edit", key=f"edit_{dash_name}"):
                        st.session_state["editing_dashboard"] = dash_name
                        st.rerun()

                with col4:
                    if st.button("🗑️ Delete", key=f"delete_{dash_name}"):
                        if st.session_state.get(f"confirm_delete_{dash_name}"):
                            dashboard.delete()
                            st.success(f"Deleted {dash_name}")
                            st.rerun()
                        else:
                            st.session_state[f"confirm_delete_{dash_name}"] = True
                            st.warning("Click again to confirm deletion")

            except Exception as e:
                with col1:
                    st.error(f"Error loading {dash_name}: {e}")

            st.divider()

    # Edit mode
    if "editing_dashboard" in st.session_state:
        st.subheader(f"Editing: {st.session_state['editing_dashboard']}")
        _render_dashboard_editor_form(st.session_state["editing_dashboard"])

        if st.button("✅ Done Editing"):
            del st.session_state["editing_dashboard"]
            st.rerun()


def _render_create_dashboard() -> None:
    """Render form to create a new dashboard."""
    st.subheader("Create New Dashboard")

    with st.form("create_dashboard_form"):
        name = st.text_input("Dashboard Name", placeholder="My Analysis Dashboard")
        description = st.text_area(
            "Description",
            placeholder="Description of what this dashboard shows...",
        )

        col1, col2 = st.columns(2)
        with col1:
            columns = st.number_input("Grid Columns", min_value=1, max_value=6, value=2)
        with col2:
            rows = st.number_input("Grid Rows", min_value=1, max_value=10, value=2)

        refresh_interval = st.number_input(
            "Auto-refresh (seconds, 0=disabled)",
            min_value=0,
            max_value=3600,
            value=0,
        )

        time_range = st.selectbox(
            "Default Time Range",
            options=["1h", "6h", "24h", "7d", "30d"],
            index=2,
        )

        submitted = st.form_submit_button("Create Dashboard")

        if submitted:
            if not name:
                st.error("Dashboard name is required")
            else:
                try:
                    dashboard = DashboardConfig(
                        name=name,
                        description=description,
                        refresh_interval=refresh_interval,
                        default_time_range=time_range,
                        layout=LayoutConfig(columns=int(columns), rows=int(rows)),
                        panels=[],
                    )
                    path = dashboard.save()
                    st.success(f"Dashboard created! Saved to {path}")
                except Exception as e:
                    st.error(f"Failed to create dashboard: {e}")


def _render_templates() -> None:
    """Render available dashboard templates."""
    st.subheader("Dashboard Templates")
    st.caption("Quick-start templates for common use cases")

    for template_name, template in DASHBOARD_TEMPLATES.items():
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**{template.name}**")
                st.caption(template.description)

            with col2:
                st.metric("Panels", len(template.panels))

            with col3:
                if st.button("Use Template", key=f"use_{template_name}"):
                    try:
                        # Create copy of template with unique name
                        new_dashboard = get_template(template_name)
                        new_dashboard.name = f"{template.name} (Copy)"
                        path = new_dashboard.save()
                        st.success(f"Created from template! Saved to {path}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create from template: {e}")

            # Preview panels
            with st.expander("Preview Panels"):
                for panel in template.panels:
                    st.markdown(f"- **{panel.title or panel.id}** ({panel.type.value})")

            st.divider()


def _render_dashboard_editor_form(dashboard_name: str) -> None:
    """Render detailed editor for a specific dashboard."""
    try:
        dashboard = DashboardConfig.load(dashboard_name)
    except Exception as e:
        st.error(f"Could not load dashboard: {e}")
        return

    # Basic settings
    with st.expander("📝 Dashboard Settings", expanded=True):
        new_name = st.text_input("Name", value=dashboard.name, key="edit_name")
        new_desc = st.text_area("Description", value=dashboard.description, key="edit_desc")

        col1, col2, col3 = st.columns(3)
        with col1:
            new_cols = st.number_input(
                "Columns",
                min_value=1,
                max_value=6,
                value=dashboard.layout.columns,
                key="edit_cols",
            )
        with col2:
            new_rows = st.number_input(
                "Rows",
                min_value=1,
                max_value=10,
                value=dashboard.layout.rows,
                key="edit_rows",
            )
        with col3:
            new_refresh = st.number_input(
                "Refresh (s)",
                min_value=0,
                max_value=3600,
                value=dashboard.refresh_interval,
                key="edit_refresh",
            )

        if st.button("Save Settings", key="save_settings"):
            dashboard.name = new_name
            dashboard.description = new_desc
            dashboard.layout.columns = int(new_cols)
            dashboard.layout.rows = int(new_rows)
            dashboard.refresh_interval = int(new_refresh)
            dashboard.save(dashboard_name)
            st.success("Settings saved!")

    # Panel management
    st.subheader("Panels")

    if not dashboard.panels:
        st.info("No panels configured. Add panels below.")
    else:
        for _i, panel in enumerate(dashboard.panels):
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

                with col1:
                    st.markdown(f"**{panel.title or panel.id}**")
                    st.caption(f"Type: {panel.type.value}")

                with col2:
                    st.caption(f"Position: Row {panel.position.row}, Col {panel.position.col}")
                    st.caption(f"Size: {panel.position.width}x{panel.position.height}")

                with col3, st.popover("📍"):
                    # Edit panel position
                    new_row = st.number_input(
                        "Row",
                        min_value=0,
                        value=panel.position.row,
                        key=f"pos_row_{panel.id}",
                    )
                    new_col = st.number_input(
                        "Col",
                        min_value=0,
                        value=panel.position.col,
                        key=f"pos_col_{panel.id}",
                    )
                    if st.button("Update", key=f"update_pos_{panel.id}"):
                        panel.position.row = int(new_row)
                        panel.position.col = int(new_col)
                        dashboard.save(dashboard_name)
                        st.rerun()

                with col4:
                    if st.button("🗑️", key=f"remove_panel_{panel.id}"):
                        dashboard.remove_panel(panel.id)
                        dashboard.save(dashboard_name)
                        st.rerun()

                st.divider()

    # Add new panel
    with st.expander("➕ Add New Panel"):
        _render_add_panel_form(dashboard, dashboard_name)


def _render_add_panel_form(dashboard: DashboardConfig, dashboard_name: str) -> None:
    """Render form to add a new panel to dashboard."""
    col1, col2 = st.columns(2)

    with col1:
        panel_id = st.text_input("Panel ID", key="new_panel_id")
        panel_title = st.text_input("Panel Title", key="new_panel_title")

    with col2:
        panel_type = st.selectbox(
            "Panel Type",
            options=[pt.value for pt in PanelType],
            key="new_panel_type",
        )

        position_row = st.number_input("Row", min_value=0, value=0, key="new_pos_row")
        position_col = st.number_input("Column", min_value=0, value=0, key="new_pos_col")

    # Type-specific configuration
    config = {}
    panel_type_enum = PanelType(panel_type)

    if panel_type_enum == PanelType.TABLE:
        config["data_source"] = st.text_input("Data Source", value="pnors_df100")
        config["limit"] = st.number_input("Row Limit", min_value=10, value=100)

    elif panel_type_enum == PanelType.TIME_SERIES:
        st.info("Configure series after adding panel via Plot Builder")

    elif panel_type_enum == PanelType.SPECTRUM:
        config["coefficient"] = st.selectbox("Coefficient", options=["A1", "B1", "A2", "B2"])

    elif panel_type_enum == PanelType.VELOCITY_PROFILE:
        config["data_source"] = st.text_input("Data Source", value="pnorc_df101")

    if st.button("Add Panel"):
        if not panel_id:
            st.error("Panel ID is required")
        else:
            try:
                panel = PanelConfig(
                    id=panel_id,
                    type=panel_type_enum,
                    title=panel_title or panel_id,
                    position=PanelPosition(
                        row=int(position_row),
                        col=int(position_col),
                    ),
                    config=config,
                )
                dashboard.add_panel(panel)
                dashboard.save(dashboard_name)
                st.success(f"Panel '{panel_id}' added!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add panel: {e}")
