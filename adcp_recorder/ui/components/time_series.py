"""Time series plot component with multi-series support."""

from typing import Any

try:
    import plotly.graph_objects as go
    import streamlit as st
except ImportError:
    go = None  # type: ignore
    st = None  # type: ignore

from adcp_recorder.ui.data_layer import DataLayer

# Default color palette for multiple series
DEFAULT_COLORS = [
    "#FF6B6B",  # Coral Red
    "#4ECDC4",  # Teal
    "#45B7D1",  # Sky Blue
    "#96CEB4",  # Sage Green
    "#FFEAA7",  # Pale Yellow
    "#DDA0DD",  # Plum
    "#98D8C8",  # Mint
    "#F7DC6F",  # Soft Yellow
]


def render_time_series(
    data_layer: DataLayer,
    config: dict[str, Any] | None = None,
    key_prefix: str = "ts",
) -> None:
    """Render a time series plot with support for multiple data series.

    Args:
        data_layer: DataLayer instance for data access
        config: Configuration dict with series, time_range, show_legend, y_axis_label
        key_prefix: Unique key prefix for Streamlit session state

    """
    if st is None or go is None:
        raise ImportError("Streamlit and Plotly are required for this component.")
    config = config or {}

    # Series configuration
    series_config = config.get("series", [])
    time_range = config.get("time_range", "24h")
    show_legend = config.get("show_legend", True)
    y_axis_label = config.get("y_axis_label", "")

    # Interactive configuration if no series provided
    if not series_config:
        series_config = _render_series_builder(data_layer, key_prefix)

    # Time range selector
    col1, col2 = st.columns([1, 4])
    with col1:
        time_range = st.selectbox(
            "Time Range",
            options=["1h", "6h", "24h", "7d", "30d", "all"],
            index=["1h", "6h", "24h", "7d", "30d", "all"].index(time_range)
            if time_range in ["1h", "6h", "24h", "7d", "30d", "all"]
            else 2,
            key=f"{key_prefix}_time_range",
        )

    if not series_config:
        st.info("Add at least one data series to display the plot.")
        return

    # Build the plot
    fig = go.Figure()

    for i, series in enumerate(series_config):
        source_name = series.get("source")
        x_col = series.get("x", "received_at")
        y_col = series.get("y")
        label = series.get("label", f"{source_name}.{y_col}")
        color = series.get("color") or DEFAULT_COLORS[i % len(DEFAULT_COLORS)]

        if not source_name or not y_col:
            continue

        try:
            # Query time series data
            data = data_layer.query_time_series(
                source_name=source_name,
                y_columns=[y_col],
                time_range=time_range,
                x_column=x_col,
            )

            x_values = data.get("x", [])
            y_values = data.get("series", {}).get(y_col, [])

            if x_values and y_values:
                fig.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=y_values,
                        mode="lines",
                        name=label,
                        line=dict(color=color, width=2),
                        hovertemplate=f"{label}: %{{y:.3f}}<br>%{{x}}<extra></extra>",
                    ),
                )
        except Exception as e:
            st.warning(f"Could not load series {label}: {e}")

    # Update layout
    fig.update_layout(
        height=400,
        margin=dict(l=50, r=20, t=30, b=50),
        xaxis=dict(
            title="Time",
            showgrid=True,
            gridcolor="rgba(128,128,128,0.2)",
        ),
        yaxis=dict(
            title=y_axis_label,
            showgrid=True,
            gridcolor="rgba(128,128,128,0.2)",
        ),
        showlegend=show_legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # Display with Streamlit
    st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")


def _render_series_builder(data_layer: DataLayer, key_prefix: str) -> list[dict[str, Any]]:
    """Render UI for building series configuration interactively."""
    if st is None:
        raise ImportError("Streamlit is required for this component.")
    series_list = []

    # Get available sources
    sources = data_layer.get_available_sources(include_views=True)
    source_names = [s.name for s in sources]

    if not source_names:
        st.warning("No data sources available.")
        return []

    # Session state for number of series
    num_series_key = f"{key_prefix}_num_series"
    if num_series_key not in st.session_state:
        st.session_state[num_series_key] = 1

    st.subheader("Configure Data Series")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add Series", key=f"{key_prefix}_add"):
            st.session_state[num_series_key] += 1
        if st.session_state[num_series_key] > 1 and st.button(
            "➖ Remove Series", key=f"{key_prefix}_remove"
        ):
            st.session_state[num_series_key] -= 1

    for idx in range(st.session_state[num_series_key]):
        with st.container():
            st.markdown(f"**Series {idx + 1}**")
            cols = st.columns(4)

            with cols[0]:
                source = st.selectbox(
                    "Source",
                    options=source_names,
                    key=f"{key_prefix}_source_{idx}",
                    label_visibility="collapsed",
                )

            # Get columns for selected source
            source_meta = data_layer.get_source_metadata(source)
            numeric_cols = source_meta.get_numeric_columns() if source_meta else []

            with cols[1]:
                y_col = st.selectbox(
                    "Y Column",
                    options=numeric_cols if numeric_cols else ["(no numeric columns)"],
                    key=f"{key_prefix}_y_{idx}",
                    label_visibility="collapsed",
                )

            with cols[2]:
                label = st.text_input(
                    "Label",
                    value=f"{y_col}" if y_col else "",
                    key=f"{key_prefix}_label_{idx}",
                    label_visibility="collapsed",
                )

            with cols[3]:
                color = st.color_picker(
                    "Color",
                    value=DEFAULT_COLORS[idx % len(DEFAULT_COLORS)],
                    key=f"{key_prefix}_color_{idx}",
                    label_visibility="collapsed",
                )

            if source and y_col and y_col != "(no numeric columns)":
                series_list.append(
                    {
                        "source": source,
                        "x": "received_at",
                        "y": y_col,
                        "label": label or y_col,
                        "color": color,
                    },
                )

    return series_list


def render_time_range_selector(
    default: str = "24h",
    key: str = "time_range",
) -> str:
    """Standalone time range selector widget."""
    if st is None:
        raise ImportError("Streamlit is required for this component.")
    options = ["1h", "6h", "24h", "7d", "30d", "all"]
    idx = options.index(default) if default in options else 2
    return st.selectbox("Time Range", options=options, index=idx, key=key)
