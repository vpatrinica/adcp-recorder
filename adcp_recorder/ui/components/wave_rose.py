"""Wave rose and polar scatter visualization components.

Plots wave parameters from PNORW (full spectrum) and PNORB (frequency bands)
as polar scatter plots: theta=DirTp (peak direction), r=Hm0 (wave height),
color=Tp (peak period). Uses continuous time-slider navigation.
"""

from typing import Any

try:
    import plotly.graph_objects as go
    import streamlit as st
except ImportError:  # pragma: no cover
    go = None  # type: ignore
    st = None  # type: ignore

from adcp_recorder.ui.data_layer import DataLayer


def render_wave_rose(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "wave_rose",
) -> None:
    """Render a wave rose / polar scatter plot.

    Plots theta=DirTp, r=Hm0, color=Tp from PNORW or PNORB data.

    Args:
        data_layer: DataLayer instance for data access
        config: Configuration dict with data_source, band_source, mode, time_range
        key_prefix: Unique key prefix for Streamlit session state

    """
    if st is None or go is None:
        raise ImportError(
            "Streamlit and Plotly are required for this component."
        )  # pragma: no cover
    config = config or {}

    # Configuration
    data_source = config.get("data_source", "wave_measurement_full")
    band_source = config.get("band_source", "pnorb_data")
    mode = config.get("mode", "full_spectrum")
    time_range = config.get("time_range", "7d")

    # Controls
    col1, col2 = st.columns(2)

    with col1:
        mode = st.radio(
            "Data Mode",
            options=["full_spectrum", "frequency_bands"],
            format_func=lambda x: (
                "Full Spectrum (PNORW)" if x == "full_spectrum" else "Frequency Bands (PNORB)"
            ),
            index=0 if mode == "full_spectrum" else 1,
            key=f"{key_prefix}_mode",
            horizontal=True,
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

    # Choose source based on mode
    source = data_source if mode == "full_spectrum" else band_source

    try:
        data = data_layer.query_wave_rose_data(
            source_name=source,
            time_range=time_range,
        )

        if not data:
            st.info("No wave rose data available in the selected time range.")
            return

        # Extract fields
        dir_tp_values = [row.get("dir_tp") for row in data]
        hm0_values = [row.get("hm0") for row in data]
        tp_values = [row.get("tp") for row in data]

        # Filter out rows with None values
        valid = [
            (d, h, t)
            for d, h, t in zip(dir_tp_values, hm0_values, tp_values, strict=False)
            if d is not None and h is not None and t is not None
        ]

        if not valid:
            st.info("No valid wave parameters with complete DirTp, Hm0, and Tp values.")
            return

        dir_tp, hm0, tp = zip(*valid, strict=False)

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=list(hm0),
                theta=list(dir_tp),
                mode="markers",
                marker=dict(
                    size=8,
                    color=list(tp),
                    colorscale="Plasma",
                    showscale=True,
                    colorbar=dict(title="Tp (s)"),
                    line=dict(width=0.5, color="white"),
                ),
                text=[
                    f"DirTp: {d:.1f}\u00b0<br>Hm0: {h:.2f} m<br>Tp: {t:.1f} s"
                    for d, h, t in zip(dir_tp, hm0, tp, strict=False)
                ],
                hoverinfo="text",
                name="Wave Rose",
            ),
        )

        fig.update_layout(
            height=550,
            polar=dict(
                radialaxis=dict(
                    title="Hm0 (m)",
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

        # Summary metrics
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Records", len(valid))
        with col_m2:
            avg_hm0 = sum(hm0) / len(hm0)
            st.metric("Avg Hm0", f"{avg_hm0:.2f} m")
        with col_m3:
            avg_tp = sum(tp) / len(tp)
            st.metric("Avg Tp", f"{avg_tp:.1f} s")

        mode_label = (
            "Full Spectrum (PNORW)" if mode == "full_spectrum" else "Frequency Bands (PNORB)"
        )
        st.caption(f"Source: {source} | Mode: {mode_label} | {len(valid)} observations")

    except Exception as e:
        st.error(f"Error rendering wave rose: {e}")
