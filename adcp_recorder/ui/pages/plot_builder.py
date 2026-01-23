"""Plot Builder page - Interactive plot creation and configuration."""

import streamlit as st

from adcp_recorder.ui.components.spectrum_plots import (
    render_directional_spectrum,
    render_energy_heatmap,
    render_fourier_spectrum,
)
from adcp_recorder.ui.components.time_series import render_time_series
from adcp_recorder.ui.components.velocity_profile import render_velocity_profile
from adcp_recorder.ui.config import PanelConfig, PanelPosition, PanelType
from adcp_recorder.ui.data_layer import DataLayer


def render_plot_builder(data_layer: DataLayer) -> None:
    """Render the Plot Builder page.

    Args:
        data_layer: DataLayer instance for data access

    """
    st.header("📈 Plot Builder")
    st.caption("Create custom visualizations from ADCP data")

    # Plot type selection
    plot_types = {
        "Time Series": PanelType.TIME_SERIES,
        "Velocity Profile": PanelType.VELOCITY_PROFILE,
        "Fourier Spectrum": PanelType.SPECTRUM,
        "Wave Energy Heatmap": PanelType.HEATMAP,
        "Directional Spectrum (Polar)": PanelType.POLAR,
    }

    col1, col2 = st.columns([2, 3])

    with col1:
        selected_type_name = st.selectbox(
            "Plot Type",
            options=list(plot_types.keys()),
            key="plot_type",
        )
        plot_type = plot_types[selected_type_name]

    with col2:
        st.info(_get_plot_description(plot_type))

    st.divider()

    # Render the selected plot type
    if plot_type == PanelType.TIME_SERIES:
        _render_time_series_builder(data_layer)
    elif plot_type == PanelType.VELOCITY_PROFILE:
        _render_velocity_profile_builder(data_layer)
    elif plot_type == PanelType.SPECTRUM:
        _render_spectrum_builder(data_layer)
    elif plot_type == PanelType.HEATMAP:
        _render_heatmap_builder(data_layer)
    elif plot_type == PanelType.POLAR:
        _render_polar_builder(data_layer)

    # Save to dashboard option
    st.divider()
    _render_save_panel_ui(plot_type)


def _get_plot_description(plot_type: PanelType) -> str:
    """Return description for each plot type."""
    descriptions = {
        PanelType.TIME_SERIES: "📊 Plot data series over time. Compare temperature, pressure, etc.",
        PanelType.VELOCITY_PROFILE: "🌊 Visualize current velocities at different depths.",
        PanelType.SPECTRUM: "📉 Display Fourier coefficient spectra (A1, B1, A2, B2).",
        PanelType.HEATMAP: "🔥 View wave energy density as a frequency-time heatmap.",
        PanelType.POLAR: "🧭 Visualize wave energy distribution by frequency and direction.",
    }
    return descriptions.get(plot_type, "Select a plot type")


def _render_time_series_builder(data_layer: DataLayer) -> None:
    """Render time series plot builder."""
    st.subheader("Time Series Plot")

    # Use the component's built-in series builder
    render_time_series(
        data_layer=data_layer,
        config=None,  # Let interactive builder take over
        key_prefix="pb_ts",
    )


def _render_velocity_profile_builder(data_layer: DataLayer) -> None:
    """Render velocity profile builder."""
    st.subheader("Velocity Profile")

    render_velocity_profile(
        data_layer=data_layer,
        config=None,
        key_prefix="pb_vp",
    )


def _render_spectrum_builder(data_layer: DataLayer) -> None:
    """Render Fourier spectrum builder."""
    st.subheader("Fourier Coefficient Spectrum")

    render_fourier_spectrum(
        data_layer=data_layer,
        config=None,
        key_prefix="pb_fourier",
    )


def _render_heatmap_builder(data_layer: DataLayer) -> None:
    """Render wave energy heatmap builder."""
    st.subheader("Wave Energy Density Heatmap")

    render_energy_heatmap(
        data_layer=data_layer,
        config=None,
        key_prefix="pb_heatmap",
    )


def _render_polar_builder(data_layer: DataLayer) -> None:
    """Render directional spectrum polar builder."""
    st.subheader("Directional Spectrum (Polar)")

    render_directional_spectrum(
        data_layer=data_layer,
        config=None,
        key_prefix="pb_polar",
    )


def _render_save_panel_ui(plot_type: PanelType) -> None:
    """Render UI to save current plot configuration to a dashboard."""
    with st.expander("💾 Save to Dashboard", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            panel_id = st.text_input(
                "Panel ID",
                value=f"custom_{plot_type.value}",
                key="save_panel_id",
            )

        with col2:
            panel_title = st.text_input(
                "Panel Title",
                value=f"Custom {plot_type.value.replace('_', ' ').title()}",
                key="save_panel_title",
            )

        # Dashboard selection
        from adcp_recorder.ui.config import DashboardConfig

        available_dashboards = DashboardConfig.list_dashboards()
        if available_dashboards:
            target_dashboard = st.selectbox(
                "Target Dashboard",
                options=available_dashboards,
                key="save_target_dashboard",
            )
        else:
            st.info("No dashboards available. Create one in Dashboard Editor first.")
            target_dashboard = None

        # Save button
        if st.button("💾 Save Panel", key="save_panel_btn", disabled=not target_dashboard):
            if target_dashboard and panel_id:
                try:
                    # Load dashboard and add panel
                    dashboard = DashboardConfig.load(target_dashboard)

                    # Reconstruct configuration from session state
                    saved_config: dict = {}

                    if plot_type == PanelType.TIME_SERIES:
                        # Reconstruct series config
                        prefix = "pb_ts"
                        num_series = st.session_state.get(f"{prefix}_num_series", 1)
                        series_list = []

                        for i in range(num_series):
                            s_source = st.session_state.get(f"{prefix}_source_{i}")
                            s_y = st.session_state.get(f"{prefix}_y_{i}")
                            s_label = st.session_state.get(f"{prefix}_label_{i}")
                            s_color = st.session_state.get(f"{prefix}_color_{i}")

                            if s_source and s_y:
                                series_list.append(
                                    {
                                        "source": s_source,
                                        "x": "received_at",
                                        "y": s_y,
                                        "label": s_label or s_y,
                                        "color": s_color,
                                    }
                                )

                        saved_config["series"] = series_list
                        saved_config["time_range"] = st.session_state.get(
                            f"{prefix}_time_range", "24h"
                        )

                    elif plot_type == PanelType.VELOCITY_PROFILE:
                        prefix = "pb_vp"
                        saved_config["data_source"] = st.session_state.get(
                            f"{prefix}_source", "pnorc12"
                        )
                        saved_config["time_range"] = st.session_state.get(
                            f"{prefix}_time_range", "24h"
                        )

                    elif plot_type == PanelType.SPECTRUM:
                        prefix = "pb_fourier"
                        saved_config["coefficient"] = st.session_state.get(f"{prefix}_coeff", "A1")
                        saved_config["time_range"] = st.session_state.get(
                            f"{prefix}_time_range", "24h"
                        )

                    elif plot_type == PanelType.HEATMAP:
                        prefix = "pb_heatmap"
                        saved_config["time_range"] = st.session_state.get(
                            f"{prefix}_time_range", "24h"
                        )

                    elif plot_type == PanelType.POLAR:
                        prefix = "pb_polar"
                        saved_config["time_range"] = st.session_state.get(
                            f"{prefix}_time_range", "24h"
                        )

                    # Create panel config
                    panel = PanelConfig(
                        id=panel_id,
                        type=plot_type,
                        title=panel_title,
                        position=PanelPosition(row=0, col=0),
                        config=saved_config,
                    )

                    dashboard.add_panel(panel)
                    dashboard.save()

                    st.success(f"✅ Panel '{panel_title}' added to {target_dashboard}!")
                except ValueError as e:
                    st.error(f"Panel ID already exists: {e}")
                except Exception as e:
                    st.error(f"Failed to save panel: {e}")
            else:
                st.warning("Please select a dashboard and provide a panel ID.")
