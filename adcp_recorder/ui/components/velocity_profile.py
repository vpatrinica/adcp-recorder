"""Velocity profile depth plot component.

Uses current_profile_* views (joining sensor + current data) as the primary
data source. Provides continuous time-slider navigation instead of manual burst
selection.
"""

from datetime import datetime
from typing import Any

try:
    import plotly.graph_objects as go
    import streamlit as st
except ImportError:
    go = None  # type: ignore
    st = None  # type: ignore

from adcp_recorder.ui.data_layer import DataLayer

# Color scheme for velocity beams
BEAM_COLORS = {
    "vel1": "#FF6B6B",  # Red - East/Beam1
    "vel2": "#4ECDC4",  # Teal - North/Beam2
    "vel3": "#45B7D1",  # Blue - Up/Beam3
    "vel4": "#96CEB4",  # Green - Beam4
}

BEAM_LABELS = {
    "vel1": "East (Vel1)",
    "vel2": "North (Vel2)",
    "vel3": "Up (Vel3)",
    "vel4": "Beam4 (Vel4)",
}

# Preferred data sources: views first, then raw tables
_PREFERRED_SOURCES = [
    "current_profile_1",
    "current_profile_12",
    "current_profile_df100",
    "current_profile_34",
    "pnorc1",
    "pnorc12",
    "pnorc_df100",
    "pnorc34",
]


def render_velocity_profile(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "vp",
) -> None:
    """Render a velocity profile depth plot showing velocity vs depth.

    Uses current_profile_* views by default, with a continuous time slider
    for navigating through measurements.

    Args:
        data_layer: DataLayer instance for data access
        config: Configuration dict with data_source, velocity_columns, cell_size, blanking_distance
        key_prefix: Unique key prefix for Streamlit session state

    """
    if st is None or go is None:
        raise ImportError("Streamlit and Plotly are required for this component.")
    config = config or {}

    # Auto-detect best current profile view
    source_name = data_layer.detect_current_profile_view()
    if source_name is None:
        st.info("No current profile data available. Waiting for PNORC data.")
        return

    velocity_columns = config.get("velocity_columns", ["vel1", "vel2", "vel3", "vel4"])
    cell_size = config.get("cell_size", 1.0)
    blanking_distance = config.get("blanking_distance", 0.5)
    time_range = config.get("time_range", "24h")

    # Settings expander
    with st.expander("Profile Settings", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            cell_size = st.number_input(
                "Cell Size (m)",
                min_value=0.1,
                max_value=10.0,
                value=cell_size,
                step=0.1,
                key=f"{key_prefix}_cell_size",
            )

        with col2:
            blanking_distance = st.number_input(
                "Blanking Distance (m)",
                min_value=0.0,
                max_value=10.0,
                value=blanking_distance,
                step=0.1,
                key=f"{key_prefix}_blanking",
            )

        # Velocity column selection
        available_vel_cols = ["vel1", "vel2", "vel3", "vel4"]
        source_meta = data_layer.get_source_metadata(source_name)
        if source_meta:
            available_vel_cols = [c.name for c in source_meta.columns if c.name.startswith("vel")]

        selected_velocities = st.multiselect(
            "Velocity Components",
            options=available_vel_cols,
            default=[v for v in velocity_columns if v in available_vel_cols],
            key=f"{key_prefix}_velocities",
        )

    # Continuous time navigation — use a slider over available bursts
    available_bursts = data_layer.get_available_bursts(
        source_name=source_name, time_range=time_range
    )

    if not available_bursts:
        st.info("No velocity profile data available in the selected time range.")
        return

    # Time slider for continuous navigation
    burst_labels = [b["label"] for b in available_bursts]
    num_bursts = len(burst_labels)

    slider_idx = st.slider(
        "Time Navigation",
        min_value=0,
        max_value=max(0, num_bursts - 1),
        value=0,
        format=f"Measurement %d of {num_bursts}",
        key=f"{key_prefix}_time_slider",
        help="Slide to navigate through measurements over time.",
    )

    selected_burst = available_bursts[slider_idx]
    st.caption(f"Measurement: {selected_burst['label']} ({slider_idx + 1}/{num_bursts})")

    # Query velocity profile data
    try:
        profile = data_layer.query_velocity_profile(
            source_name=source_name,
            velocity_columns=selected_velocities,
            cell_size=cell_size,
            blanking_distance=blanking_distance,
            timestamp=selected_burst["received_at"],
        )

        depths = profile.get("depths", [])
        velocities = profile.get("velocities", {})

        if not depths:
            st.info("No velocity profile data for this measurement.")
            return

        # Build the profile plot
        fig = go.Figure()

        for vel_col in selected_velocities:
            vel_values = velocities.get(vel_col, [])
            if not vel_values:
                continue

            color = BEAM_COLORS.get(vel_col, "#888888")
            label = BEAM_LABELS.get(vel_col, vel_col)

            fig.add_trace(
                go.Scatter(
                    x=vel_values,
                    y=depths,
                    mode="lines+markers",
                    name=label,
                    line=dict(color=color, width=2),
                    marker=dict(size=6, color=color),
                    hovertemplate=(
                        f"{label}<br>Velocity: %{{x:.3f}} m/s<br>Depth: %{{y:.2f}} m<extra></extra>"
                    ),
                ),
            )

        # Update layout for depth profile (inverted Y-axis, depth increases downward)
        fig.update_layout(
            height=500,
            margin=dict(l=60, r=20, t=30, b=50),
            xaxis=dict(
                title="Velocity (m/s)",
                showgrid=True,
                gridcolor="rgba(128,128,128,0.2)",
                zeroline=True,
                zerolinecolor="rgba(128,128,128,0.5)",
            ),
            yaxis=dict(
                title="Depth (m)",
                showgrid=True,
                gridcolor="rgba(128,128,128,0.2)",
                autorange="reversed",  # Depth increases downward
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            hovermode="closest",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        # Display
        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")

        # Metrics
        if selected_velocities:
            cols = st.columns(len(selected_velocities))
            for i, vel_col in enumerate(selected_velocities):
                vel_values = velocities.get(vel_col, [])
                if vel_values:
                    with cols[i]:
                        valid_values = [v for v in vel_values if v is not None]
                        if valid_values:
                            avg_vel = sum(valid_values) / len(valid_values)
                            st.metric(
                                BEAM_LABELS.get(vel_col, vel_col),
                                f"{avg_vel:.3f} m/s",
                                help=f"Average {vel_col} across all cells",
                            )

    except Exception as e:
        st.error(f"Error loading velocity profile: {e}")

    st.caption(f"Source: {source_name} (auto-detected)")


def render_velocity_comparison(
    data_layer: DataLayer,
    timestamps: list[datetime],
    config: dict[str, Any] | None = None,
    key_prefix: str = "vc",
) -> None:
    """Render multiple velocity profiles for comparison over time.

    Args:
        data_layer: DataLayer instance
        timestamps: List of timestamps to compare
        config: Configuration dict
        key_prefix: Unique key prefix

    """
    if st is None or go is None:
        raise ImportError("Streamlit and Plotly are required for this component.")
    config = config or {}
    source_name = data_layer.detect_current_profile_view()
    if source_name is None:
        st.info("No current profile data available.")
        return

    fig = go.Figure()

    for i, ts in enumerate(timestamps[:5]):  # Limit to 5 profiles
        try:
            profile_data = data_layer.query_velocity_profile(
                source_name=source_name,
                velocity_columns=["vel1"],
                timestamp=ts,
            )

            depths = profile_data.get("depths", [])
            vel1 = profile_data.get("velocities", {}).get("vel1", [])

            if depths and vel1:
                fig.add_trace(
                    go.Scatter(
                        x=vel1,
                        y=depths,
                        mode="lines",
                        name=str(ts),
                        opacity=0.7 + (i * 0.06),
                    ),
                )
        except Exception:  # noqa: BLE001
            continue

    fig.update_layout(
        height=400,
        yaxis=dict(autorange="reversed"),
        xaxis=dict(title="Velocity (m/s)"),
        yaxis_title="Depth (m)",
    )

    st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_comparison")
