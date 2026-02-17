"""Current profile visualization components.

Provides:
- Current speed heatmap: time x depth grid with color=speed, optional direction arrows
- Current direction polar: polar scatter of speed/direction across depth cells

Uses current_profile_* views (joining PNORS + PNORC + PNORI/PNORH) as primary
data sources.
"""

from datetime import datetime
from typing import Any

try:
    import plotly.graph_objects as go
    import streamlit as st
except ImportError:  # pragma: no cover
    go = None  # type: ignore
    st = None  # type: ignore

from adcp_recorder.ui.data_layer import DataLayer


def render_current_speed_heatmap(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "speed_heatmap",
) -> None:
    """Render current speed as a time x depth heatmap.

    X-axis is time, Y-axis is cell number/depth, color intensity is speed (m/s).
    Optionally overlays direction arrows.

    Args:
        data_layer: DataLayer instance for data access
        config: Configuration dict with data_source, colorscale, show_direction_arrows, time_range
        key_prefix: Unique key prefix for Streamlit session state

    """
    if st is None or go is None:
        raise ImportError(
            "Streamlit and Plotly are required for this component."
        )  # pragma: no cover
    config = config or {}

    # Auto-detect best current profile view
    source_name = data_layer.detect_current_profile_view()
    if source_name is None:
        st.info("No current profile data available. Waiting for PNORC data.")
        return

    colorscale = config.get("colorscale", "Viridis")
    show_arrows = config.get("show_direction_arrows", False)
    time_range = config.get("time_range", "24h")

    # Controls
    col1, col2, col3 = st.columns(3)

    with col1:
        time_range = st.selectbox(
            "Time Range",
            options=["1h", "6h", "24h", "7d", "30d", "all"],
            index=["1h", "6h", "24h", "7d", "30d", "all"].index(time_range)
            if time_range in ["1h", "6h", "24h", "7d", "30d", "all"]
            else 2,
            key=f"{key_prefix}_time_range",
        )

    with col2:
        colorscale = st.selectbox(
            "Color Scale",
            options=["Viridis", "Plasma", "Inferno", "Turbo", "Blues", "Reds"],
            index=["Viridis", "Plasma", "Inferno", "Turbo", "Blues", "Reds"].index(colorscale)
            if colorscale in ["Viridis", "Plasma", "Inferno", "Turbo", "Blues", "Reds"]
            else 0,
            key=f"{key_prefix}_colorscale",
        )

    with col3:
        show_arrows = st.checkbox(
            "Show Direction Arrows",
            value=show_arrows,
            key=f"{key_prefix}_arrows",
        )

    try:
        heatmap_data = data_layer.query_current_speed_heatmap(
            source_name=source_name,
            time_range=time_range,
        )

        if not heatmap_data:
            st.info("No current profile data available in the selected time range.")
            return

        timestamps = heatmap_data.get("timestamps", [])
        cell_indices = heatmap_data.get("cell_indices", [])
        speeds = heatmap_data.get("speeds", [])
        directions = heatmap_data.get("directions")
        cell_distances = heatmap_data.get("cell_distances")

        if not timestamps or not cell_indices or not speeds:
            st.info("Insufficient data for heatmap rendering.")
            return

        # Use actual values for axes to allow numerical overlays
        x_axis = timestamps
        if cell_distances and any(d is not None for d in cell_distances):
            y_axis = cell_distances
            y_title = "Depth (m)"
        else:
            y_axis = cell_indices
            y_title = "Cell Index"

        fig = go.Figure()

        fig.add_trace(
            go.Heatmap(
                z=speeds,
                x=x_axis,
                y=y_axis,
                colorscale=colorscale,
                colorbar=dict(title="Speed (m/s)"),
                hovertemplate=("Time: %{x}<br>Depth: %{y}<br>Speed: %{z:.3f} m/s<extra></extra>"),
            ),
        )

        # Overlay direction arrows if requested and data available
        if show_arrows and directions:
            _add_direction_arrows(fig, x_axis, y_axis, speeds, directions)

        fig.update_layout(
            height=500,
            margin=dict(l=60, r=80, t=30, b=60),
            xaxis=dict(
                title="Time",
                showgrid=False,
                tickangle=-45,
            ),
            yaxis=dict(
                title=y_title,
                showgrid=False,
                autorange="reversed",  # Depth increases downward
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")

        st.caption(
            f"Source: {source_name} | {len(timestamps)} time steps x "
            f"{len(cell_indices)} cells | Range: {time_range}"
        )

    except Exception as e:
        st.error(f"Error rendering current speed heatmap: {e}")


def _add_direction_arrows(
    fig: Any,
    x_values: list[Any],
    y_values: list[Any],
    speeds: list[list[float | None]],
    directions: list[list[float | None]],
) -> None:
    """Add direction arrows as a scatter trace overlay on the heatmap.

    Subsamples to avoid overcrowding. Arrow points in the flow direction.

    Args:
        fig: Plotly Figure to add arrows to
        x_values: X-axis values (timestamps)
        y_values: Y-axis values (depths or cell indices)
        speeds: 2D speed array [cell][time]
        directions: 2D direction array [cell][time]

    """
    num_cells = len(y_values)
    num_times = len(x_values)

    # Subsample: max ~20 arrows per axis
    cell_step = max(1, num_cells // 15)
    time_step = max(1, num_times // 20)

    arrow_x = []
    arrow_y = []
    arrow_angles = []

    for ci in range(0, num_cells, cell_step):
        for ti in range(0, num_times, time_step):
            direction = (
                directions[ci][ti] if ci < len(directions) and ti < len(directions[ci]) else None
            )
            speed = speeds[ci][ti] if ci < len(speeds) and ti < len(speeds[ci]) else None

            if direction is None or speed is None or speed < 0.01:
                continue

            arrow_x.append(x_values[ti])
            arrow_y.append(y_values[ci])
            # Plotly angle: 0 is up, clockwise. ADCP direction: 0 is North (up), clockwise.
            arrow_angles.append(direction)

    if arrow_x:
        fig.add_trace(
            go.Scatter(
                x=arrow_x,
                y=arrow_y,
                mode="markers",
                marker=dict(
                    symbol="arrow-wide",
                    angle=arrow_angles,
                    size=12,
                    color="white",
                    line=dict(width=1, color="rgba(0,0,0,0.5)"),
                ),
                name="Direction",
                hoverinfo="skip",
                showlegend=False,
            )
        )


def render_current_direction_polar(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "current_polar",
) -> None:
    """Render current speed/direction as a polar scatter plot across depth cells.

    Each point represents a measurement: theta=direction, r=speed,
    color=cell index (depth).

    Args:
        data_layer: DataLayer instance for data access
        config: Configuration dict with data_source, time_range
        key_prefix: Unique key prefix for Streamlit session state

    """
    if st is None or go is None:
        raise ImportError(
            "Streamlit and Plotly are required for this component."
        )  # pragma: no cover
    config = config or {}

    # Auto-detect best current profile view
    source_name = data_layer.detect_current_profile_view()
    if source_name is None:
        st.info("No current profile data available. Waiting for PNORC data.")
        return

    time_range = config.get("time_range", "24h")

    # Controls
    time_range = st.selectbox(
        "Time Range",
        options=["1h", "6h", "24h", "7d", "30d", "all"],
        index=["1h", "6h", "24h", "7d", "30d", "all"].index(time_range)
        if time_range in ["1h", "6h", "24h", "7d", "30d", "all"]
        else 2,
        key=f"{key_prefix}_time_range",
    )

    try:
        heatmap_data = data_layer.query_current_speed_heatmap(
            source_name=source_name,
            time_range=time_range,
        )

        if not heatmap_data:
            st.info("No current profile data available in the selected time range.")
            return

        timestamps = heatmap_data.get("timestamps", [])
        cell_indices = heatmap_data.get("cell_indices", [])
        speeds = heatmap_data.get("speeds", [])
        directions = heatmap_data.get("directions")

        if not timestamps or not cell_indices or not speeds or not directions:
            st.info("Direction data is required for polar plots but is not available.")
            return

        # Flatten: each cell x time becomes a data point
        r_values: list[float] = []
        theta_values: list[float] = []
        cell_colors: list[int] = []
        hover_texts: list[str] = []

        for ci_idx, ci in enumerate(cell_indices):
            for ti_idx, ts in enumerate(timestamps):
                spd = (
                    speeds[ci_idx][ti_idx]
                    if ci_idx < len(speeds) and ti_idx < len(speeds[ci_idx])
                    else None
                )
                dirn = (
                    directions[ci_idx][ti_idx]
                    if ci_idx < len(directions) and ti_idx < len(directions[ci_idx])
                    else None
                )

                if spd is not None and dirn is not None:
                    r_values.append(spd)
                    theta_values.append(dirn)
                    cell_colors.append(ci)
                    ts_str = ts.strftime("%m-%d %H:%M") if isinstance(ts, datetime) else str(ts)
                    hover_texts.append(
                        f"Cell {ci}<br>Speed: {spd:.3f} m/s<br>"
                        f"Dir: {dirn:.1f}\u00b0<br>Time: {ts_str}"
                    )

        if not r_values:
            st.info("No valid speed/direction pairs found in the data.")
            return

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=r_values,
                theta=theta_values,
                mode="markers",
                marker=dict(
                    size=5,
                    color=cell_colors,
                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(title="Cell Index"),
                    line=dict(width=0.3, color="white"),
                    opacity=0.6,
                ),
                text=hover_texts,
                hoverinfo="text",
                name="Current Direction",
            ),
        )

        fig.update_layout(
            height=550,
            polar=dict(
                radialaxis=dict(
                    title="Speed (m/s)",
                    showgrid=True,
                    gridcolor="rgba(128,128,128,0.3)",
                ),
                angularaxis=dict(
                    direction="clockwise",
                    rotation=90,  # North at top
                    showgrid=True,
                    gridcolor="rgba(128,128,128,0.3)",
                ),
            ),
            margin=dict(l=40, r=40, t=30, b=40),
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")

        # Summary
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Data Points", len(r_values))
        with col_m2:
            avg_speed = sum(r_values) / len(r_values)
            st.metric("Avg Speed", f"{avg_speed:.3f} m/s")
        with col_m3:
            max_speed = max(r_values)
            st.metric("Max Speed", f"{max_speed:.3f} m/s")

        st.caption(
            f"Source: {source_name} | {len(timestamps)} time steps x "
            f"{len(cell_indices)} cells | Range: {time_range}"
        )

    except Exception as e:
        st.error(f"Error rendering current direction polar: {e}")
