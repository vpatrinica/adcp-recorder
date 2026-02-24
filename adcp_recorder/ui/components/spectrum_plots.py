"""Spectrum visualization components for Fourier coefficients and wave energy.

Uses wave_measurement_full view and individual wave tables (pnore_data,
pnorf_data, pnorwd_data) for spectrum plots. Provides continuous time-slider
navigation instead of manual burst selection.
"""

import json
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

        z_data = np.array(padded_matrix, dtype=float)

        # Compute explicit zmax from actual values so the colorscale
        # spans the real data range and small values are clearly visible.
        z_max = float(np.max(z_data)) if z_data.size > 0 else 1.0

        # Generate frequency axis
        sorted_freqs = sorted(all_frequencies)
        freq_axis = sorted_freqs if sorted_freqs else list(range(max_len))

        fig = go.Figure(
            data=go.Heatmap(
                z=z_data,
                x=freq_axis[:max_len],
                y=timestamps,
                colorscale=colorscale,
                zmin=0,
                zmax=z_max,
                colorbar=dict(title="Energy (m²/Hz)"),
                hovertemplate=(
                    "Freq: %{x:.3f} Hz<br>Time: %{y}<br>Energy: %{z:.4f}<extra></extra>"
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

        # Validate the returned data has non-empty arrays
        frequencies = data.get("frequencies", [])
        energies = data.get("energy", [])
        directions = data.get("directions", [])
        spreads = data.get("spreads", [])

        if not frequencies or not energies:
            st.warning("Directional spectrum data is incomplete.")
            st.caption(
                f"Retrieved: {len(frequencies)} frequencies, {len(energies)} energy values, "
                f"{len(directions)} directions, {len(spreads)} spreads. "
                f"Keys in data: {list(data.keys())}"
            )
            return

        # Ensure all arrays have the same length
        n = len(frequencies)
        if len(energies) < n:
            energies = energies + [0.0] * (n - len(energies))
        if len(directions) < n:
            directions = directions + [0.0] * (n - len(directions))
        if len(spreads) < n:
            spreads = spreads + [20.0] * (n - len(spreads))

        # Clean None values
        clean_energies = [float(e) if e is not None else 0.0 for e in energies[:n]]
        clean_directions = [float(d) if d is not None else 0.0 for d in directions[:n]]
        clean_spreads = [float(s) if s is not None else 20.0 for s in spreads[:n]]

        min_f = min(frequencies)
        max_f = max(frequencies)
        max_energy = max(clean_energies) if clean_energies else 0.0
        st.caption(
            f"Frequency: {min_f:.3f}–{max_f:.3f} Hz  |  "
            f"{n} bins  |  Peak energy: {max_energy:.4f} m²/Hz"
        )

        # Prepare Polar Data
        fig = go.Figure()

        # Find peak for metrics
        if max_energy > 0:
            peak_idx = int(np.argmax(clean_energies))
            peak_f = frequencies[peak_idx]
            peak_e = clean_energies[peak_idx]
            peak_d = clean_directions[peak_idx]

            st.sidebar.metric("Peak Frequency", f"{peak_f:.3f} Hz")
            st.sidebar.metric("Peak Energy", f"{peak_e:.4f} m²/Hz")
            st.sidebar.metric("Peak Direction", f"{peak_d:.1f}°")

        if plot_style == "Bubble Plot":
            # Scale marker sizes: use log-scaled sizes so small values are visible.
            # Map energy to a visible range [8, 40] using log normalization.
            if max_energy > 0:
                marker_sizes = []
                for e in clean_energies:
                    if e > 0:
                        # Log-normalize: log(e) relative to range
                        log_e = np.log10(e)
                        log_max = np.log10(max_energy)
                        log_min = np.log10(max(min(ce for ce in clean_energies if ce > 0), 1e-10))
                        log_range = max(log_max - log_min, 1.0)
                        normalized = (log_e - log_min) / log_range
                        marker_sizes.append(8 + normalized * 32)
                    else:
                        marker_sizes.append(6)
            else:
                marker_sizes = [8] * n

            fig.add_trace(
                go.Scatterpolar(
                    r=frequencies,
                    theta=clean_directions,
                    mode="markers",
                    marker=dict(
                        size=marker_sizes,
                        color=clean_energies,
                        colorscale="Turbo",
                        showscale=True,
                        cmin=0,
                        cmax=max_energy if max_energy > 0 else 1.0,
                        colorbar=dict(
                            title="Energy (m²/Hz)",
                            orientation="h",
                            y=-0.15,
                            thickness=15,
                        ),
                        line=dict(width=1, color="white"),
                        opacity=0.85,
                    ),
                    text=[
                        f"Freq: {f:.3f} Hz<br>"
                        f"Dir: {d:.1f}°<br>"
                        f"Energy: {e:.5f} m²/Hz<br>"
                        f"Spread: {s:.1f}°"
                        for f, d, e, s in zip(
                            frequencies,
                            clean_directions,
                            clean_energies,
                            clean_spreads,
                            strict=False,
                        )
                    ],
                    hoverinfo="text",
                    name="Directional Energy",
                )
            )
        else:
            # Heatmap Reconstructed
            theta_bins = np.linspace(0, 360, 73)[:-1]  # 72 bins × 5° each
            d_theta = 360 / 72

            freqs = np.array(frequencies)
            dr: float = 0.01
            if len(freqs) > 1:
                dr = float(np.mean(np.diff(freqs)))

            # Build a 2D intensity grid
            intensity_grid = []
            for i, _f in enumerate(freqs):
                e_total = clean_energies[i]
                theta_m = clean_directions[i]
                sigma = max(1.0, clean_spreads[i])

                # Gaussian spreading function
                diff = (theta_bins - theta_m + 180) % 360 - 180
                dist = np.exp(-0.5 * (diff / sigma) ** 2)

                dist_sum = np.sum(dist)
                if dist_sum > 0:
                    dist = (dist / dist_sum) * (e_total / d_theta)

                intensity_grid.append(dist)

            intensity_arr = np.array(intensity_grid)

            # Render as go.Barpolar segments
            r_all: list[float] = []
            theta_all: list[float] = []
            base_all: list[float] = []
            colors_all: list[float] = []

            for i, f in enumerate(freqs):
                r_all.extend([dr] * len(theta_bins))
                theta_all.extend(theta_bins)
                base_all.extend([f - dr / 2] * len(theta_bins))
                colors_all.extend(intensity_arr[i])

            fig.add_trace(
                go.Barpolar(
                    r=r_all,
                    theta=theta_all,
                    base=base_all,
                    marker=dict(
                        color=colors_all,
                        colorscale="Turbo",
                        showscale=True,
                        colorbar=dict(
                            title="Energy (m²/Hz)",
                            orientation="h",
                            y=-0.15,
                            thickness=15,
                        ),
                        line=dict(width=0),
                    ),
                    width=[d_theta] * len(theta_all),
                    hoverinfo="skip",
                    name="Directional Energy",
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

    # Auto-detect best current profile source for amplitude data (prefer *_1 views)
    source_name = data_layer.detect_current_profile_view()
    st.write(f"Selected source: {source_name}")
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
        yaxis=dict(autorange="reversed"),
    )

    st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")


def render_fourier_surface_3d(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "fourier_3d",
) -> None:
    """Render Fourier coefficients as a 3D surface (Time × Frequency × Value).

    Shows all bursts simultaneously so the user does not need to navigate
    one-by-one with a slider.

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
    time_range = config.get("time_range", "7d")
    colorscale = config.get("colorscale", "Viridis")

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
            else 3,
            key=f"{key_prefix}_time_range",
        )

    with col3:
        colorscale = st.selectbox(
            "Color Scale",
            options=["Viridis", "Plasma", "Inferno", "Turbo", "Blues"],
            index=0,
            key=f"{key_prefix}_colorscale",
        )

    try:
        spectrum_data = data_layer.query_spectrum_data(
            source_name=source_name,
            coefficient=coefficient,
            time_range=time_range,
        )

        if not spectrum_data:
            st.info(
                f"No {coefficient} spectrum data available for 3D surface "
                f"in the selected time range."
            )
            return

        # Build the 2D matrix: rows = bursts (time), cols = frequency bins
        timestamps: list[str] = []
        z_rows: list[list[float]] = []

        for record in spectrum_data:
            coefficients_val = record.get("coefficients")
            if isinstance(coefficients_val, str):
                try:
                    coefficients_val = json.loads(coefficients_val)
                except json.JSONDecodeError:
                    continue
            if not coefficients_val or not isinstance(coefficients_val, list):
                continue

            ts = record.get("received_at")
            timestamps.append(str(ts) if ts else "")
            z_rows.append([float(v) if v is not None else 0.0 for v in coefficients_val])

        if not z_rows:
            st.info("No valid Fourier records for 3D surface.")
            return

        # Pad rows to uniform length
        max_len = max(len(row) for row in z_rows)
        for row in z_rows:
            row.extend([0.0] * (max_len - len(row)))

        z_data = np.array(z_rows, dtype=float)

        # Frequency axis from first valid record
        first = spectrum_data[0]
        start_f = first.get("start_frequency", 0.0)
        step_f = first.get("step_frequency", 0.01)
        freq_axis = [start_f + i * step_f for i in range(max_len)]

        fig = go.Figure(
            data=go.Surface(
                z=z_data,
                x=freq_axis,
                y=timestamps,
                colorscale=colorscale,
                colorbar=dict(title=f"{coefficient}"),
                hovertemplate=(
                    f"{coefficient}<br>"
                    "Freq: %{x:.3f} Hz<br>"
                    "Time: %{y}<br>"
                    "Value: %{z:.4f}<extra></extra>"
                ),
            ),
        )

        fig.update_layout(
            height=600,
            margin=dict(l=20, r=20, t=30, b=20),
            scene=dict(
                xaxis=dict(title="Frequency (Hz)"),
                yaxis=dict(
                    title="Time",
                    ticklen=25,
                    tickcolor="rgba(0,0,0,0)",
                ),
                zaxis=dict(title=f"{coefficient} Coefficient"),
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")
        st.caption(
            f"3D surface: {len(z_rows)} bursts × {max_len} frequency bins "
            f"({coefficient}, {time_range})"
        )

    except Exception as e:
        st.error(f"Error rendering Fourier 3D surface: {e}")


def render_energy_surface_3d(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "energy_3d",
) -> None:
    """Render wave energy density as a 3D surface (Time × Frequency × Energy).

    Shows all energy spectra simultaneously so the user does not need to
    navigate one-by-one with a slider.

    Args:
        data_layer: DataLayer instance for data access
        config: Configuration dict with data_source, time_range, colorscale
        key_prefix: Unique key prefix for Streamlit session state

    """
    if st is None or go is None:
        raise ImportError("Streamlit and Plotly are required for this component.")
    config = config or {}

    # Configuration
    source_name = config.get("data_source", "pnore_data")
    time_range = config.get("time_range", "7d")
    colorscale = config.get("colorscale", "Plasma")

    # Controls
    col1, col2 = st.columns(2)

    with col1:
        time_range = st.selectbox(
            "Time Range",
            options=["1h", "6h", "24h", "7d", "30d", "all"],
            index=["1h", "6h", "24h", "7d", "30d", "all"].index(time_range)
            if time_range in ["1h", "6h", "24h", "7d", "30d", "all"]
            else 3,
            key=f"{key_prefix}_time_range",
        )

    with col2:
        colorscale = st.selectbox(
            "Color Scale",
            options=["Plasma", "Viridis", "Inferno", "Turbo", "Hot"],
            index=0,
            key=f"{key_prefix}_colorscale",
        )

    try:
        energy_data = data_layer.query_wave_energy(
            source_name=source_name,
            time_range=time_range,
        )

        if not energy_data:
            st.info("No wave energy data available for 3D surface in the selected time range.")
            return

        # Build the 2D matrix: rows = bursts (time), cols = frequency bins
        timestamps: list[str] = []
        z_rows: list[list[float]] = []

        for record in energy_data:
            energies = record.get("energy_densities")
            if isinstance(energies, str):
                try:
                    energies = json.loads(energies)
                except json.JSONDecodeError:
                    continue
            if not energies or not isinstance(energies, list):
                continue

            ts = record.get("received_at", "")
            timestamps.append(str(ts))
            z_rows.append([float(v) if v is not None else 0.0 for v in energies])

        if not z_rows:
            st.info("No valid energy records for 3D surface.")
            return

        # Pad rows to uniform length
        max_len = max(len(row) for row in z_rows)
        for row in z_rows:
            row.extend([0.0] * (max_len - len(row)))

        z_data = np.array(z_rows, dtype=float)

        # Frequency axis from first valid record
        first = energy_data[0]
        start_f = first.get("start_frequency", 0.0)
        step_f = first.get("step_frequency", 0.01)
        freq_axis = [start_f + i * step_f for i in range(max_len)]

        fig = go.Figure(
            data=go.Surface(
                z=z_data,
                x=freq_axis,
                y=timestamps,
                colorscale=colorscale,
                colorbar=dict(title="Energy (m²/Hz)"),
                hovertemplate=(
                    "Freq: %{x:.3f} Hz<br>Time: %{y}<br>Energy: %{z:.4f} m²/Hz<extra></extra>"
                ),
            ),
        )

        fig.update_layout(
            height=600,
            margin=dict(l=20, r=20, t=30, b=20),
            scene=dict(
                xaxis=dict(title="Frequency (Hz)"),
                yaxis=dict(
                    title="Time",
                    ticklen=25,
                    tickcolor="rgba(0,0,0,0)",
                ),
                zaxis=dict(title="Energy (m²/Hz)"),
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")
        st.caption(f"3D surface: {len(z_rows)} bursts × {max_len} frequency bins ({time_range})")

    except Exception as e:
        st.error(f"Error rendering energy 3D surface: {e}")


def _query_directional_field_surface(
    data_layer: DataLayer,
    field: str,
    time_range: str,
) -> tuple[list[list[float]], list[str], list[float]]:
    """Shared helper: collect one field across all bursts.

    Args:
        data_layer: DataLayer instance
        field: Key to extract from query result ('directions' or 'spreads')
        time_range: Time range string

    Returns:
        (z_rows, labels, freq_axis) – may be empty if no data found.

    """
    bursts = data_layer.get_available_bursts(time_range=time_range)
    if not bursts:
        return [], [], []

    z_rows: list[list[float]] = []
    labels: list[str] = []
    freq_axis: list[float] = []

    for burst in bursts:
        data = data_layer.query_directional_spectrum(
            time_range=time_range,
            timestamp=burst["received_at"],
        )
        if not data:
            continue

        values = data.get(field, [])
        if not values:
            continue

        clean = [float(v) if v is not None else 0.0 for v in values]
        z_rows.append(clean)
        ts = burst.get("received_at")
        labels.append(str(ts) if ts else "")

        # Capture frequency axis from first successful burst
        if not freq_axis:
            freq_axis = list(data.get("frequencies", []))

    if not z_rows:
        return [], [], freq_axis

    # Pad rows to uniform length
    max_len = max(len(row) for row in z_rows)
    for row in z_rows:
        row.extend([0.0] * (max_len - len(row)))

    # Extend frequency axis if shorter than data
    if len(freq_axis) < max_len:
        step = freq_axis[1] - freq_axis[0] if len(freq_axis) > 1 else 0.01
        start = freq_axis[-1] + step if freq_axis else 0.0
        freq_axis = freq_axis + [start + i * step for i in range(max_len - len(freq_axis))]

    return z_rows, labels, freq_axis[:max_len]


def render_direction_surface_3d(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "md_3d",
) -> None:
    """Render mean direction (MD) as a 3D surface (Frequency × Burst × Direction).

    Shows how the mean wave direction varies across frequency and time for
    all bursts simultaneously.

    Args:
        data_layer: DataLayer instance for data access
        config: Configuration dict with time_range
        key_prefix: Unique key prefix for Streamlit session state

    """
    if st is None or go is None:
        raise ImportError("Streamlit and Plotly are required for this component.")
    config = config or {}

    time_range = config.get("time_range", "7d")
    colorscale = config.get("colorscale", "HSV")

    col1, col2 = st.columns(2)

    with col1:
        time_range = st.selectbox(
            "Observation Window",
            options=["1h", "6h", "24h", "7d", "30d", "all"],
            index=["1h", "6h", "24h", "7d", "30d", "all"].index(time_range)
            if time_range in ["1h", "6h", "24h", "7d", "30d", "all"]
            else 3,
            key=f"{key_prefix}_time_range",
        )

    with col2:
        colorscale = st.selectbox(
            "Color Scale",
            options=["HSV", "Turbo", "Viridis", "Plasma", "Inferno"],
            index=0,
            key=f"{key_prefix}_colorscale",
        )

    try:
        z_rows, labels, freq_axis = _query_directional_field_surface(
            data_layer, "directions", time_range
        )

        if not z_rows:
            st.info("No mean direction data found for 3D surface.")
            st.caption("Try increasing the Observation Window if data is older.")
            return

        z_data = np.array(z_rows, dtype=float)

        fig = go.Figure(
            data=go.Surface(
                z=z_data,
                x=freq_axis,
                y=labels,
                colorscale=colorscale,
                colorbar=dict(title="Direction (°)"),
                hovertemplate=(
                    "Freq: %{x:.3f} Hz<br>Time: %{y}<br>Direction: %{z:.1f}°<extra></extra>"
                ),
            ),
        )

        fig.update_layout(
            height=600,
            margin=dict(l=20, r=20, t=30, b=20),
            scene=dict(
                xaxis=dict(title="Frequency (Hz)"),
                yaxis=dict(
                    title="Time",
                    ticklen=25,
                    tickcolor="rgba(0,0,0,0)",
                ),
                zaxis=dict(title="Mean Direction (°)"),
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")
        st.caption(
            f"3D mean direction: {len(z_rows)} bursts × "
            f"{len(freq_axis)} frequency bins ({time_range})"
        )

    except Exception as e:
        st.error(f"Error rendering mean direction 3D surface: {e}")


def render_spread_surface_3d(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "ds_3d",
) -> None:
    """Render directional spread (DS) as a 3D surface (Frequency × Burst × Spread).

    Shows how the directional spread varies across frequency and time for
    all bursts simultaneously.

    Args:
        data_layer: DataLayer instance for data access
        config: Configuration dict with time_range
        key_prefix: Unique key prefix for Streamlit session state

    """
    if st is None or go is None:
        raise ImportError("Streamlit and Plotly are required for this component.")
    config = config or {}

    time_range = config.get("time_range", "7d")
    colorscale = config.get("colorscale", "Viridis")

    col1, col2 = st.columns(2)

    with col1:
        time_range = st.selectbox(
            "Observation Window",
            options=["1h", "6h", "24h", "7d", "30d", "all"],
            index=["1h", "6h", "24h", "7d", "30d", "all"].index(time_range)
            if time_range in ["1h", "6h", "24h", "7d", "30d", "all"]
            else 3,
            key=f"{key_prefix}_time_range",
        )

    with col2:
        colorscale = st.selectbox(
            "Color Scale",
            options=["Viridis", "Plasma", "Turbo", "Inferno", "Hot"],
            index=0,
            key=f"{key_prefix}_colorscale",
        )

    try:
        z_rows, labels, freq_axis = _query_directional_field_surface(
            data_layer, "spreads", time_range
        )

        if not z_rows:
            st.info("No directional spread data found for 3D surface.")
            st.caption("Try increasing the Observation Window if data is older.")
            return

        z_data = np.array(z_rows, dtype=float)

        fig = go.Figure(
            data=go.Surface(
                z=z_data,
                x=freq_axis,
                y=labels,
                colorscale=colorscale,
                colorbar=dict(title="Spread (°)"),
                hovertemplate=(
                    "Freq: %{x:.3f} Hz<br>Time: %{y}<br>Spread: %{z:.1f}°<extra></extra>"
                ),
            ),
        )

        fig.update_layout(
            height=600,
            margin=dict(l=20, r=20, t=30, b=20),
            scene=dict(
                xaxis=dict(title="Frequency (Hz)"),
                yaxis=dict(
                    title="Time",
                    ticklen=25,
                    tickcolor="rgba(0,0,0,0)",
                ),
                zaxis=dict(title="Directional Spread (°)"),
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")
        st.caption(
            f"3D directional spread: {len(z_rows)} bursts × "
            f"{len(freq_axis)} frequency bins ({time_range})"
        )

    except Exception as e:
        st.error(f"Error rendering directional spread 3D surface: {e}")
