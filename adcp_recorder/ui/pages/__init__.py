"""Streamlit pages module for multi-page dashboard navigation."""

from adcp_recorder.ui.pages.dashboard_editor import render_dashboard_editor
from adcp_recorder.ui.pages.data_explorer import render_data_explorer
from adcp_recorder.ui.pages.plot_builder import render_plot_builder

__all__ = [
    "render_dashboard_editor",
    "render_data_explorer",
    "render_plot_builder",
]
