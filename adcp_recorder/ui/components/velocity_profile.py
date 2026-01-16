"""Velocity profile depth plot component."""

from datetime import datetime
from typing import Any

import plotly.graph_objects as go
import streamlit as st

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


def render_velocity_profile(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "vp",
) -> None:
    """Render a velocity profile depth plot showing velocity vs depth.

    Args:
        data_layer: DataLayer instance for data access
        config: Configuration dict with data_source, velocity_columns, cell_size, blanking_distance
        key_prefix: Unique key prefix for Streamlit session state

    """
    config = config or {}

    # Configuration
    source_name = config.get("data_source", "pnorc_df101")
    velocity_columns = config.get("velocity_columns", ["vel1", "vel2", "vel3", "vel4"])
    cell_size = config.get("cell_size", 1.0)
    blanking_distance = config.get("blanking_distance", 0.5)

    # Settings expander
    with st.expander("⚙️ Profile Settings", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            # Get available velocity sources
            sources = data_layer.get_available_sources()
            velocity_sources = [
                s.name
                for s in sources
                if "pnorc" in s.name.lower() or "velocity" in s.category.lower()
            ]
            if not velocity_sources:
                velocity_sources = [source_name]

            source_name = st.selectbox(
                "Data Source",
                options=velocity_sources,
                index=velocity_sources.index(source_name) if source_name in velocity_sources else 0,
                key=f"{key_prefix}_source",
            )

        with col2:
            cell_size = st.number_input(
                "Cell Size (m)",
                min_value=0.1,
                max_value=10.0,
                value=cell_size,
                step=0.1,
                key=f"{key_prefix}_cell_size",
            )

        with col3:
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

    if not selected_velocities:
        selected_velocities = available_vel_cols[:3]

    # Query velocity profile data
    try:
        profile_data = data_layer.query_velocity_profile(
            source_name=source_name,
            velocity_columns=selected_velocities,
            cell_size=cell_size,
            blanking_distance=blanking_distance,
        )

        depths = profile_data.get("depths", [])
        velocities = profile_data.get("velocities", {})

        if not depths:
            st.info("No velocity profile data available.")
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
        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_chart")

        # Metrics
        cols = st.columns(len(selected_velocities))
        for i, vel_col in enumerate(selected_velocities):
            vel_values = velocities.get(vel_col, [])
            if vel_values:
                with cols[i]:
                    # Filter out None values for stats
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
    config = config or {}
    source_name = config.get("data_source", "pnorc_df101")

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

    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_comparison")
