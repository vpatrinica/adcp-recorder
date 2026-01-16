"""Spectrum visualization components for Fourier coefficients and wave energy."""

import json
from typing import Any

import numpy as np
import plotly.graph_objects as go
import streamlit as st

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

    Args:
        data_layer: DataLayer instance for data access
        config: Configuration dict with data_source, coefficient, time_range
        key_prefix: Unique key prefix for Streamlit session state

    """
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
            options=["1h", "6h", "24h", "7d"],
            index=["1h", "6h", "24h", "7d"].index(time_range)
            if time_range in ["1h", "6h", "24h", "7d"]
            else 2,
            key=f"{key_prefix}_time_range",
        )

    with col3:
        show_all = st.checkbox(
            "Show All Timestamps",
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

        fig = go.Figure()

        # Limit number of spectra shown
        max_spectra = len(spectrum_data) if show_all else min(5, len(spectrum_data))

        for i, record in enumerate(spectrum_data[:max_spectra]):
            start_freq = record.get("start_frequency", 0)
            step_freq = record.get("step_frequency", 0.01)
            num_freqs = record.get("num_frequencies", 0)
            coefficients = record.get("coefficients")

            # Parse coefficients if stored as JSON string
            if isinstance(coefficients, str):
                try:
                    coefficients = json.loads(coefficients)
                except json.JSONDecodeError:
                    continue

            if not coefficients or not isinstance(coefficients, list):
                continue

            # Generate frequency axis
            frequencies = [
                start_freq + (j * step_freq) for j in range(min(len(coefficients), num_freqs))
            ]

            # Timestamp label
            date_str = record.get("measurement_date", "")
            time_str = record.get("measurement_time", "")
            label = f"{date_str} {time_str}" if date_str else f"Record {i + 1}"

            # Calculate opacity for layering
            opacity = 1.0 if i == 0 else 0.6 - (i * 0.1)
            opacity = max(0.2, opacity)

            fig.add_trace(
                go.Scatter(
                    x=frequencies,
                    y=coefficients[: len(frequencies)],
                    mode="lines",
                    name=label,
                    line=dict(
                        color=COEFFICIENT_COLORS.get(coefficient, "#888888"),
                        width=2 if i == 0 else 1,
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

        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_chart")

        st.caption(f"Showing {max_spectra} of {len(spectrum_data)} spectra in time range")

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
    config = config or {}

    # Configuration
    source_name = config.get("data_source", "echo_data")
    colorscale = config.get("colorscale", "Viridis")
    time_range = config.get("time_range", "24h")

    # Controls
    col1, col2 = st.columns(2)

    with col1:
        time_range = st.selectbox(
            "Time Range",
            options=["1h", "6h", "24h", "7d"],
            index=["1h", "6h", "24h", "7d"].index(time_range)
            if time_range in ["1h", "6h", "24h", "7d"]
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
                colorbar=dict(title="Energy (m²/Hz)"),
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
                title="Time (record index)",
                showgrid=False,
                autorange="reversed",
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_chart")

        st.caption(f"Showing {len(energy_matrix)} energy spectra over {time_range}")

    except Exception as e:
        st.error(f"Error loading wave energy heatmap: {e}")


def render_directional_spectrum(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "polar",
) -> None:
    """Render wave directional spectrum as a polar plot.

    Args:
        data_layer: DataLayer instance
        config: Configuration dict with time_range
        key_prefix: Unique key prefix for Streamlit session state

    """
    config = config or {}

    # Configuration
    time_range = config.get("time_range", "24h")

    # Controls
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        time_range = st.selectbox(
            "Observation Window",
            options=["1h", "6h", "24h", "7d"],
            index=["1h", "6h", "24h", "7d"].index(time_range)
            if time_range in ["1h", "6h", "24h", "7d"]
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

    # Note: Currently query_directional_spectrum fetches the latest available burst
    # in the database that has both energy and directional components.
    try:
        data = data_layer.query_directional_spectrum(time_range=time_range)

        if not data:
            st.info("No directional spectrum data (PNORE + PNORWD) found.")
            st.caption("Ensure both Wave Energy (PNORE) and Directional (PNORWD) records exist.")
            return

        with col3:
            st.write(f"**Latest Burst:** {data['measurement_date']} {data['measurement_time']}")
            st.write(
                f"**Frequency Range:** {min(data['frequencies']):.2f} - "
                f"{max(data['frequencies']):.2f} Hz"
            )

        # Prepare Polar Data
        fig = go.Figure()

        # Find peak for normalization and metrics
        energies = data["energy"]
        if energies:
            peak_idx = int(np.argmax(energies))
            peak_f = data["frequencies"][peak_idx]
            peak_e = energies[peak_idx]
            peak_d = data["directions"][peak_idx]

            st.sidebar.metric("Peak Frequency", f"{peak_f:.3f} Hz")
            st.sidebar.metric("Peak Energy", f"{peak_e:.4f} m²/Hz")
            st.sidebar.metric("Peak Direction", f"{peak_d:.1f}°")

        if plot_style == "Bubble Plot":
            # Bubble plot: Energy vs Frequency/Direction
            fig.add_trace(
                go.Scatterpolar(
                    r=data["frequencies"],
                    theta=data["directions"],
                    mode="markers",
                    marker=dict(
                        size=[max(5, np.sqrt(e) * 40) for e in energies],
                        color=energies,
                        colorscale="Viridis",
                        showscale=True,
                        colorbar=dict(title="Energy", orientation="h", y=-0.2),
                        line=dict(width=1, color="white"),
                    ),
                    text=[
                        f"Freq: {f:.3f} Hz<br>Dir: {d:.1f}°<br>Energy: {e:.4f}<br>Spread: {s:.1f}°"
                        for f, d, e, s in zip(
                            data["frequencies"],
                            data["directions"],
                            data["energy"],
                            data["spreads"],
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
            # Calculate dr for bar heights (frequency steps)
            if len(freqs) > 1:
                dr = np.mean(np.diff(freqs))
            else:
                dr = 0.01

            # Build a 2D intensity grid
            # Shape: (len(freqs), len(theta_bins))
            intensity_grid = []

            for i, f in enumerate(freqs):
                e_total = data["energy"][i]
                theta_m = data["directions"][i]
                sigma = data["spreads"][i]

                # Ensure sigma is positive to avoid div by zero
                sigma = max(1.0, sigma)

                # Gaussian spreading function: D(theta) = exp(-0.5 * ((theta-theta_m)/sigma)^2)
                # Shortest angular distance
                diff = (theta_bins - theta_m + 180) % 360 - 180
                dist = np.exp(-0.5 * (diff / sigma) ** 2)

                # Normalize so sum(dist * d_theta) = 1 (approx) or just preserve e_total
                dist_sum = np.sum(dist)
                if dist_sum > 0:
                    dist = (dist / dist_sum) * (e_total / d_theta)

                intensity_grid.append(dist)

            intensity_grid = np.array(intensity_grid)

            # Render as go.Barpolar segments to create a heatmap appearance
            # To be efficient, we merge segments or use Heatmap if possible.
            # However, Barpolar with a common radius works well for rings.
            for i, f in enumerate(freqs):
                fig.add_trace(
                    go.Barpolar(
                        r=[dr] * len(theta_bins),
                        theta=theta_bins,
                        base=[f - dr / 2] * len(theta_bins),
                        marker=dict(
                            color=intensity_grid[i],
                            colorscale="Viridis",
                            # showscale only for the first trace
                            showscale=(i == 0),
                            colorbar=dict(title="Energy Density", orientation="h", y=-0.2)
                            if i == 0
                            else None,
                            line=dict(width=0),
                        ),
                        width=[d_theta] * len(theta_bins),
                        hoverinfo="skip",  # Hover on heatmap is tricky per pixel
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

        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_chart")

    except Exception as e:
        st.error(f"Error rendering directional spectrum: {e}")
