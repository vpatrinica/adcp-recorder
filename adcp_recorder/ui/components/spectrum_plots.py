"""Spectrum visualization components for Fourier coefficients and wave energy.

Uses wave_measurement_full view and individual wave tables (pnore_data,
pnorf_data, pnorwd_data) for spectrum plots. Provides continuous time-slider
navigation instead of manual burst selection.
"""

import json
from datetime import datetime
from typing import Any

import numpy as np

try:
    import plotly.graph_objects as go
    import streamlit as st
except ImportError:
    go = None  # type: ignore
    st = None  # type: ignore

from adcp_recorder.ui.data_layer import DataLayer

# Color scheme for coefficient types
COEFFICIENT_COLORS = {
    "A1": "#FF6B6B",
    "B1": "#4ECDC4",
    "A2": "#45B7D1",
    "B2": "#96CEB4",
}


def render_fourier_spectrum(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "fourier",
) -> None:
    """Render Fourier coefficient spectrum plot (A1, B1, A2, B2).

    Uses continuous time slider instead of manual burst selection.

    Args:
        data_layer: DataLayer instance for data access
        config: Configuration dict with data_source, coefficient, time_range
        key_prefix: Unique key prefix for Streamlit session state

    """
    if st is None or go is None:
        raise ImportError("Streamlit and Plotly are required for this component.")
    config = config or {}

    # Configuration
    source_name = config.get("data_source", "pnorf_data")
    coefficient = config.get("coefficient", "A1")
    time_range = config.get("time_range", "24h")

    # Controls
    col1, col2, col3 = st.columns(3)

    with col1:
        coefficient = st.selectbox(
            "Coefficient Type",
            options=["A1", "B1", "A2", "B2"],
            index=["A1", "B1", "A2", "B2"].index(coefficient),
            key=f"{key_prefix}_coeff",
        )

    with col2:
        time_range = st.selectbox(
            "Time Range",
            options=["1h", "6h", "24h", "7d", "30d", "all"],
            index=["1h", "6h", "24h", "7d", "30d", "all"].index(time_range)
            if time_range in ["1h", "6h", "24h", "7d", "30d", "all"]
            else 2,
            key=f"{key_prefix}_time_range",
        )

    with col3:
        show_all = st.checkbox(
            "Show All Records (Layered)",
            value=False,
            key=f"{key_prefix}_show_all",
        )

    # Query spectrum data
    try:
        spectrum_data = data_layer.query_spectrum_data(
            source_name=source_name,
            coefficient=coefficient,
            time_range=time_range,
        )

        if not spectrum_data:
            st.info(f"No {coefficient} spectrum data available in the selected time range.")
            return

        # Continuous time slider for navigation
        num_spectra = len(spectrum_data)
        slider_idx = st.slider(
            "Spectrum Navigation",
            min_value=0,
            max_value=max(0, num_spectra - 1),
            value=0,
            format=f"Spectrum %d of {num_spectra}",
            key=f"{key_prefix}_time_slider",
            help="Slide to navigate through spectra over time.",
        )

        current_record = spectrum_data[slider_idx]
        date_str = current_record.get("measurement_date", "")
        time_str = current_record.get("measurement_time", "")
        st.caption(f"Current: {date_str} {time_str} ({slider_idx + 1}/{num_spectra})")

        fig = go.Figure()

        # Determine display range
        if show_all:
            display_data = spectrum_data
        else:
            display_data = spectrum_data[slider_idx : slider_idx + 1]

        for i, record in enumerate(display_data):
            start_freq = record.get("start_frequency", 0)
            step_freq = record.get("step_frequency", 0.01)
            num_freqs = record.get("num_frequencies", 0)
            coefficients_val = record.get("coefficients")

            # Parse coefficients if stored as JSON string
            if isinstance(coefficients_val, str):
                try:
                    coefficients_val = json.loads(coefficients_val)
                except json.JSONDecodeError:
                    continue

            if not coefficients_val or not isinstance(coefficients_val, list):
                continue

            # Generate frequency axis
            frequencies = [
                start_freq + (j * step_freq) for j in range(min(len(coefficients_val), num_freqs))
            ]

            # Timestamp label
            rec_date = record.get("measurement_date", "")
            rec_time = record.get("measurement_time", "")
            label = f"{rec_date} {rec_time}" if rec_date else f"Record {i + 1}"

            # Calculate opacity for layering
            is_current = (i == slider_idx) if show_all else (i == 0)
            opacity = 1.0 if is_current else max(0.2, 0.6 - (abs(i - slider_idx) * 0.1))

            fig.add_trace(
                go.Scatter(
                    x=frequencies,
                    y=coefficients_val[: len(frequencies)],
                    mode="lines",
                    name=label,
                    line=dict(
                        color=COEFFICIENT_COLORS.get(coefficient, "#888888"),
                        width=2 if is_current else 1,
                    ),
                    opacity=opacity,
                    hovertemplate=(
                        f"{coefficient}<br>Freq: %{{x:.3f}} Hz<br>"
                        f"Value: %{{y:.4f}}<extra>{label}</extra>"
                    ),
                ),
            )

        # Update layout
        fig.update_layout(
            height=400,
            margin=dict(l=50, r=20, t=30, b=50),
            xaxis=dict(
                title="Frequency (Hz)",
                showgrid=True,
                gridcolor="rgba(128,128,128,0.2)",
            ),
            yaxis=dict(
                title=f"{coefficient} Coefficient",
                showgrid=True,
                gridcolor="rgba(128,128,128,0.2)",
            ),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
            ),
            hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")

        st.caption(f"Showing {'all' if show_all else '1'} of {num_spectra} spectra in time range")

    except Exception as e:
        st.error(f"Error loading Fourier spectrum: {e}")


def render_energy_heatmap(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "heatmap",
) -> None:
    """Render wave energy density spectrum as a heatmap.

    Args:
        data_layer: DataLayer instance for data access
        config: Configuration dict with data_source, colorscale, time_range
        key_prefix: Unique key prefix for Streamlit session state

    """
    if st is None or go is None:
        raise ImportError("Streamlit and Plotly are required for this component.")
    config = config or {}

    # Configuration
    source_name = config.get("data_source", "pnore_data")
    colorscale = config.get("colorscale", "Viridis")
    time_range = config.get("time_range", "24h")

    # Controls
    col1, col2 = st.columns(2)

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
            index=0,
            key=f"{key_prefix}_colorscale",
        )

    # Query wave energy data
    try:
        energy_data = data_layer.query_wave_energy(
            source_name=source_name,
            time_range=time_range,
        )

        if not energy_data:
            st.info("No wave energy data available in the selected time range.")
            return

        # Build heatmap data
        timestamps = []
        all_frequencies = set()
        energy_matrix = []

        for record in energy_data:
            received_at = record.get("received_at")
            start_freq = record.get("start_frequency", 0)
            step_freq = record.get("step_frequency", 0.01)
            energies = record.get("energy_densities")

            # Parse energies if stored as JSON string
            if isinstance(energies, str):
                try:
                    energies = json.loads(energies)
                except json.JSONDecodeError:
                    continue

            if not energies or not isinstance(energies, list):
                continue

            timestamps.append(received_at)

            # Generate frequency bins
            frequencies = [start_freq + (j * step_freq) for j in range(len(energies))]
            all_frequencies.update(frequencies)
            energy_matrix.append(energies)

        if not energy_matrix:
            st.info("No valid wave energy records found.")
            return

        # Convert to numpy array for heatmap
        # Pad shorter rows to match longest
        max_len = max(len(row) for row in energy_matrix)
        padded_matrix = []
        for row in energy_matrix:
            padded = row + [0] * (max_len - len(row))
            padded_matrix.append(padded)

        z_data = np.array(padded_matrix)

        # Generate frequency axis
        sorted_freqs = sorted(all_frequencies)
        freq_axis = sorted_freqs if sorted_freqs else list(range(max_len))

        fig = go.Figure(
            data=go.Heatmap(
                z=z_data,
                x=freq_axis[:max_len],
                y=list(range(len(timestamps))),
                colorscale=colorscale,
                colorbar=dict(title="Energy (m\u00b2/Hz)"),
                hovertemplate=(
                    "Freq: %{x:.3f} Hz<br>Record: %{y}<br>Energy: %{z:.4f}<extra></extra>"
                ),
            ),
        )

        # Update layout
        fig.update_layout(
            height=400,
            margin=dict(l=50, r=80, t=30, b=50),
            xaxis=dict(
                title="Frequency (Hz)",
                showgrid=False,
            ),
            yaxis=dict(
                title="Time",
                showgrid=False,
                autorange="reversed",
                tickmode="array",
                tickvals=list(range(len(timestamps))),
                ticktext=[
                    ts.strftime("%H:%M:%S") if isinstance(ts, datetime) else str(ts)
                    for ts in timestamps
                ],
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")

        st.caption(f"Showing {len(energy_matrix)} energy spectra over {time_range}")

    except Exception as e:
        st.error(f"Error loading wave energy heatmap: {e}")


def render_directional_spectrum(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "polar",
) -> None:
    """Render wave directional spectrum as a polar plot.

    Uses continuous time slider instead of manual burst selection.

    Args:
        data_layer: DataLayer instance
        config: Configuration dict with time_range
        key_prefix: Unique key prefix for Streamlit session state

    """
    if st is None or go is None:
        raise ImportError("Streamlit and Plotly are required for this component.")
    config = config or {}

    # Configuration
    time_range = config.get("time_range", "24h")

    # Controls
    col1, col2 = st.columns([1, 1])

    with col1:
        time_range = st.selectbox(
            "Observation Window",
            options=["1h", "6h", "24h", "7d", "30d", "all"],
            index=["1h", "6h", "24h", "7d", "30d", "all"].index(time_range)
            if time_range in ["1h", "6h", "24h", "7d", "30d", "all"]
            else 2,
            key=f"{key_prefix}_time_range",
        )

    with col2:
        plot_style = st.radio(
            "Visualization Style",
            options=["Bubble Plot", "Heatmap (Reconstructed)"],
            index=0,
            key=f"{key_prefix}_style",
            horizontal=True,
        )

    # Get available bursts for time slider
    bursts = data_layer.get_available_bursts(
        time_range=time_range,
    )

    if not bursts:
        st.info("No wave bursts found in this window.")
        st.caption("Try increasing the Observation Window (e.g. to 7d) if data is older.")
        return

    # Continuous time slider
    num_bursts = len(bursts)
    slider_idx = st.slider(
        "Burst Navigation",
        min_value=0,
        max_value=max(0, num_bursts - 1),
        value=0,
        format=f"Burst %d of {num_bursts}",
        key=f"{key_prefix}_time_slider",
        help="Slide to navigate through wave bursts over time.",
    )

    selected_burst = bursts[slider_idx]
    st.caption(f"Burst: {selected_burst['label']} ({slider_idx + 1}/{num_bursts})")

    try:
        data = data_layer.query_directional_spectrum(
            time_range=time_range, timestamp=selected_burst["received_at"]
        )
        if not data:
            st.info("No merged directional spectrum data found.")
            st.caption(
                "This requires both Wave Energy (PNORE) and Directional Spread (PNORWD) "
                "records with matching date/time."
            )
            return

        if data.get("frequencies"):
            min_f = min(data["frequencies"])
            max_f = max(data["frequencies"])
            st.caption(
                f"Frequency Range: {min_f:.2f} - {max_f:.2f} Hz"
                if min_f is not None and max_f is not None
                else "Frequency Range: N/A"
            )

        # Prepare Polar Data
        fig = go.Figure()

        # Find peak for normalization and metrics
        energies = data.get("energy", [])
        if energies:
            # Handle possible None values in data
            clean_energies = [e if e is not None else 0.0 for e in energies]
            peak_idx = int(np.argmax(clean_energies))

            peak_f = data["frequencies"][peak_idx] if peak_idx < len(data["frequencies"]) else None
            peak_e = clean_energies[peak_idx]

            directions = data.get("directions", [])
            peak_d = directions[peak_idx] if peak_idx < len(directions) else None

            # Safe formatting for metrics
            f_label = f"{peak_f:.3f} Hz" if peak_f is not None else "N/A"
            e_label = f"{peak_e:.4f} m\u00b2/Hz" if peak_e is not None else "N/A"
            d_label = f"{peak_d:.1f}\u00b0" if peak_d is not None else "N/A"

            st.sidebar.metric("Peak Frequency", f_label)
            st.sidebar.metric("Peak Energy", e_label)
            st.sidebar.metric("Peak Direction", d_label)

        if plot_style == "Bubble Plot":
            # Bubble plot: Energy vs Frequency/Direction
            fig.add_trace(
                go.Scatterpolar(
                    r=data["frequencies"],
                    theta=data["directions"],
                    mode="markers",
                    marker=dict(
                        size=[max(5, np.sqrt(e if e is not None else 0.0) * 40) for e in energies],
                        color=energies,
                        colorscale="Viridis",
                        showscale=True,
                        colorbar=dict(title="Energy", orientation="h", y=-0.2),
                        line=dict(width=1, color="white"),
                    ),
                    text=[
                        (f"Freq: {f:.3f} Hz<br>" if f is not None else "Freq: N/A<br>")
                        + (f"Dir: {d:.1f}\u00b0<br>" if d is not None else "Dir: N/A<br>")
                        + (f"Energy: {e:.4f}<br>" if e is not None else "Energy: N/A<br>")
                        + (f"Spread: {s:.1f}\u00b0" if s is not None else "Spread: N/A")
                        for f, d, e, s in zip(
                            data.get("frequencies", []),
                            data.get("directions", []),
                            data.get("energy", []),
                            data.get("spreads", []),
                            strict=False,
                        )
                    ],
                    hoverinfo="text",
                    name="Directional Energy",
                )
            )
        else:
            # Heatmap Reconstructed
            # Define directional bins (e.g., 5 degree resolution)
            theta_bins = np.linspace(0, 360, 73)[:-1]  # 72 bins
            d_theta = 360 / 72

            # For each frequency bin, calculate the distribution
            freqs = np.array(data["frequencies"])
            dr: float = 0.01
            if len(freqs) > 1:
                dr = float(np.mean(np.diff(freqs)))

            # Build a 2D intensity grid
            intensity_grid = []

            for i, _f in enumerate(freqs):
                e_total = data["energy"][i] if data["energy"][i] is not None else 0.0
                theta_m = data["directions"][i] if data["directions"][i] is not None else 0.0
                sigma = data["spreads"][i] if data["spreads"][i] is not None else 20.0

                # Ensure sigma is positive to avoid div by zero
                sigma = max(1.0, sigma)

                # Gaussian spreading function
                diff = (theta_bins - theta_m + 180) % 360 - 180
                dist = np.exp(-0.5 * (diff / sigma) ** 2)

                # Normalize
                dist_sum = np.sum(dist)
                if dist_sum > 0:
                    dist = (dist / dist_sum) * (e_total / d_theta)

                intensity_grid.append(dist)

            intensity_arr = np.array(intensity_grid)

            # Render as go.Barpolar segments
            for i, f in enumerate(freqs):
                fig.add_trace(
                    go.Barpolar(
                        r=[dr] * len(theta_bins),
                        theta=theta_bins,
                        base=[f - dr / 2] * len(theta_bins),
                        marker=dict(
                            color=intensity_arr[i],
                            colorscale="Viridis",
                            showscale=(i == 0),
                            colorbar=dict(title="Energy Density", orientation="h", y=-0.2)
                            if i == 0
                            else None,
                            line=dict(width=0),
                        ),
                        width=[d_theta] * len(theta_bins),
                        hoverinfo="skip",
                        name=f"{f:.3f} Hz",
                    )
                )

        # Update Polar Layout
        fig.update_layout(
            height=600,
            template="plotly_dark",
            polar=dict(
                radialaxis=dict(
                    title="Frequency (Hz)",
                    gridcolor="rgba(255,255,255,0.2)",
                    showline=False,
                    ticks="",
                ),
                angularaxis=dict(
                    direction="clockwise",
                    period=360,
                    rotation=90,  # North at top
                    gridcolor="rgba(255,255,255,0.2)",
                ),
                bgcolor="rgba(0,0,0,0)",
            ),
            margin=dict(l=40, r=40, t=20, b=40),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")

    except Exception as e:
        st.error(f"Error rendering directional spectrum: {e}")


def render_amplitude_heatmap(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "amplitude_heatmap",
) -> None:
    """Render a heatmap of signal strength (amplitude) over time and depth.

    Args:
        data_layer: DataLayer instance for data access
        config: Configuration dict with data_source, time_range
        key_prefix: Unique key prefix for Streamlit session state
    """
    if st is None or go is None:
        raise ImportError("Streamlit and Plotly are required for this component.")
    config = config or {}

    # Auto-detect best current profile source for amplitude data
    source_name = data_layer.detect_current_profile_view()
    if source_name is None:
        st.info("No current profile data available for amplitude heatmap.")
        return

    default_time_range = config.get("time_range", "24h")

    # Local time range selector
    time_range = st.selectbox(
        "Observation Window",
        options=["1h", "6h", "24h", "7d", "30d", "all"],
        index=["1h", "6h", "24h", "7d", "30d", "all"].index(default_time_range)
        if default_time_range in ["1h", "6h", "24h", "7d", "30d", "all"]
        else 2,
        key=f"{key_prefix}_time_range",
    )

    data = data_layer.query_amplitude_heatmap(source_name, time_range)

    if not data:
        st.info("No amplitude data found for the selected time range.")
        return

    # Extract timestamps and amplitude grid
    timestamps = [d["received_at"] for d in data]

    # We need to ensure all rows have the same length for the heatmap
    max_cells = max(len(d["amplitudes"]) for d in data)

    # Fill intensity grid: Rows are cells (distance), Columns are time
    intensity_grid = []
    for cell_idx in range(max_cells):
        row = []
        for d in data:
            if cell_idx < len(d["amplitudes"]):
                row.append(d["amplitudes"][cell_idx])
            else:
                row.append(None)
        intensity_grid.append(row)

    # Use cell index for Y-axis
    y_axis = list(range(max_cells))

    fig = go.Figure(
        data=go.Heatmap(
            z=intensity_grid,
            x=timestamps,
            y=y_axis,
            colorscale="Jet",
            colorbar=dict(title="Counts"),
            hovertemplate="Time: %{x}<br>Cell: %{y}<br>Amplitude: %{z:.1f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Average Signal Strength (counts)",
        xaxis_title="Time",
        yaxis_title="Cell Index",
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")
