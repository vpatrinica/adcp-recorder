"""Spectrum visualization components for Fourier coefficients and wave energy."""

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

    # Burst Selection
    bursts = data_layer.get_available_bursts(time_range=time_range, source_name=source_name)
    selected_bursts = []

    if bursts:
        selected_labels = st.multiselect(
            "Select Bursts to Display",
            options=[b["label"] for b in bursts],
            default=[bursts[0]["label"]] if bursts else [],
            key=f"{key_prefix}_bursts",
        )
        selected_bursts = [b for b in bursts if b["label"] in selected_labels]

    # Query spectrum data
    try:
        # If bursts selected, we query specific timestamps or just filter the results
        spectrum_data = data_layer.query_spectrum_data(
            source_name=source_name,
            coefficient=coefficient,
            time_range=time_range,
        )

        if not spectrum_data:
            st.info(f"No {coefficient} spectrum data available in the selected time range.")
            return

        # Filter by selected bursts if any
        if selected_bursts:
            burst_labels = {b["label"] for b in selected_bursts}
            spectrum_data = [
                s
                for s in spectrum_data
                if f"{s.get('measurement_date', '')} {s.get('measurement_time', '')}"
                in burst_labels
            ]

        fig = go.Figure()

        # Limit number of spectra shown if not explicit
        if not selected_bursts:
            max_spectra = len(spectrum_data) if show_all else min(5, len(spectrum_data))
            display_data = spectrum_data[:max_spectra]
        else:
            display_data = spectrum_data

        for i, record in enumerate(display_data):
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

        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")

        if not selected_bursts:
            st.caption(f"Showing {max_spectra} of {len(spectrum_data)} spectra in time range")
        else:
            st.caption(f"Showing {len(display_data)} selected spectra")

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
    col1, col2, col3 = st.columns([1, 1, 1])

    start_time = None
    end_time = None

    with col1:
        time_range = st.selectbox(
            "Observation Window",
            options=["1h", "6h", "24h", "7d", "30d", "all", "Custom"],
            index=["1h", "6h", "24h", "7d", "30d", "all", "Custom"].index(time_range)
            if time_range in ["1h", "6h", "24h", "7d", "30d", "all", "Custom"]
            else 2,
            key=f"{key_prefix}_time_range",
        )

        if time_range == "Custom":
            sd = st.date_input("Start", key=f"{key_prefix}_sd")
            st_val = st.time_input("Start Time", key=f"{key_prefix}_st")
            ed = st.date_input("End", key=f"{key_prefix}_ed")
            et_val = st.time_input("End Time", key=f"{key_prefix}_et")

            if sd and ed:
                from datetime import datetime

                start_time = datetime.combine(sd, st_val)
                end_time = datetime.combine(ed, et_val)
        else:
            # For standard ranges, we let data_layer parse it, OR we parse it here to filter bursts?
            # get_available_bursts takes time_range str.
            pass

    # Burst Selection
    # Note: We need to update get_available_bursts to support explicit start/end times
    # For now, if Custom, we might need to rely on a future update to DataLayer
    # or pass a dummy 'all' and filter?
    # Let's assume we will update DataLayer to accept start_time/end_time kwargs.

    bursts = data_layer.get_available_bursts(
        time_range=time_range if time_range != "Custom" else "all",
        start_time=start_time,
        end_time=end_time,
    )
    selected_burst = None

    if bursts:
        with col2:
            burst_labels = [b["label"] for b in bursts]
            selected_label = st.selectbox(
                "Select Burst",
                options=burst_labels,
                index=0,
                key=f"{key_prefix}_burst",
            )
            selected_burst = next(b for b in bursts if b["label"] == selected_label)
    else:
        with col2:
            st.warning("No wave bursts found in this window.")
            st.caption("Try increasing the **Observation Window** (e.g. to 7d) if data is older.")

    with col3:
        plot_style = st.radio(
            "Visualization Style",
            options=["Bubble Plot", "Heatmap (Reconstructed)"],
            index=0,
            key=f"{key_prefix}_style",
            horizontal=True,
        )

    # Note: query_directional_spectrum can now take a specific timestamp
    try:
        ts_param = selected_burst["received_at"] if selected_burst else None
        data = data_layer.query_directional_spectrum(time_range=time_range, timestamp=ts_param)

        if not data:
            st.info("No merged directional spectrum data found.")
            st.caption(
                "This requires both Wave Energy (**PNORE**) and Directional Spread (**PNORWD**) "
                "records with matching date/time. Check the **Select Burst** dropdown."
            )
            return

        if data.get("frequencies"):
            with col3:
                st.write(
                    f"**Latest Burst:** {data.get('measurement_date', '')} "
                    f"{data.get('measurement_time', '')}"
                )
                min_f = min(data["frequencies"])
                max_f = max(data["frequencies"])
                st.write(
                    f"**Frequency Range:** {min_f:.2f} - {max_f:.2f} Hz"
                    if min_f is not None and max_f is not None
                    else "**Frequency Range:** N/A"
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
            e_label = f"{peak_e:.4f} m²/Hz" if peak_e is not None else "N/A"
            d_label = f"{peak_d:.1f}°" if peak_d is not None else "N/A"

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
                        + (f"Dir: {d:.1f}°<br>" if d is not None else "Dir: N/A<br>")
                        + (f"Energy: {e:.4f}<br>" if e is not None else "Energy: N/A<br>")
                        + (f"Spread: {s:.1f}°" if s is not None else "Spread: N/A")
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
            # Shape: (len(freqs), len(theta_bins))
            intensity_grid = []

            for i, f in enumerate(freqs):
                e_total = data["energy"][i] if data["energy"][i] is not None else 0.0
                theta_m = data["directions"][i] if data["directions"][i] is not None else 0.0
                sigma = (
                    data["spreads"][i] if data["spreads"][i] is not None else 20.0
                )  # Default spread

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

            intensity_arr = np.array(intensity_grid)

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
                            color=intensity_arr[i],
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
    source_name = config.get("data_source", "pnorc12")
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
