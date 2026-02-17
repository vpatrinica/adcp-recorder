"""Tests for Plot Builder page - full coverage."""

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("plotly")
pytest.importorskip("streamlit")

from adcp_recorder.ui.config import PanelType
from adcp_recorder.ui.pages.plot_builder import (
    _get_plot_description,
    _render_amplitude_heatmap_builder,
    _render_current_direction_polar_builder,
    _render_current_speed_heatmap_builder,
    _render_heatmap_builder,
    _render_polar_builder,
    _render_spectrum_builder,
    _render_time_series_builder,
    _render_velocity_profile_builder,
    _render_wave_rose_builder,
    render_plot_builder,
)


# ---------------------------------------------------------------------------
# Plot descriptions
# ---------------------------------------------------------------------------
class TestPlotDescriptions:
    """Test _get_plot_description returns correct descriptions."""

    @pytest.mark.parametrize(
        "panel_type",
        list(PanelType),
    )
    def test_all_plot_types_have_descriptions(self, panel_type):
        """Every PanelType should have a description (even TABLE defaults)."""
        desc = _get_plot_description(panel_type)
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_unknown_type_returns_default(self):
        """An unrecognised value returns the fallback string."""
        # Use a string that is not a valid PanelType
        desc = _get_plot_description("__nonexistent__")  # type: ignore[arg-type]
        assert desc == "Select a plot type"


# ---------------------------------------------------------------------------
# Original render builders (TIME_SERIES, VP, SPECTRUM, HEATMAP, POLAR)
# ---------------------------------------------------------------------------
class TestTimeSeriesBuilder:
    """Tests for _render_time_series_builder."""

    @patch("adcp_recorder.ui.pages.plot_builder.render_time_series")
    @patch("adcp_recorder.ui.pages.plot_builder.st")
    def test_calls_render_time_series(self, mock_st, mock_render):
        dl = MagicMock()
        _render_time_series_builder(dl)
        mock_st.subheader.assert_called_once_with("Time Series Plot")
        mock_render.assert_called_once_with(data_layer=dl, config=None, key_prefix="pb_ts")


class TestVelocityProfileBuilder:
    """Tests for _render_velocity_profile_builder."""

    @patch("adcp_recorder.ui.pages.plot_builder.render_velocity_profile")
    @patch("adcp_recorder.ui.pages.plot_builder.st")
    def test_calls_render_velocity_profile(self, mock_st, mock_render):
        dl = MagicMock()
        _render_velocity_profile_builder(dl)
        mock_st.subheader.assert_called_once_with("Velocity Profile")
        mock_render.assert_called_once_with(data_layer=dl, config=None, key_prefix="pb_vp")


class TestSpectrumBuilder:
    """Tests for _render_spectrum_builder."""

    @patch("adcp_recorder.ui.pages.plot_builder.render_fourier_spectrum")
    @patch("adcp_recorder.ui.pages.plot_builder.st")
    def test_calls_render_fourier_spectrum(self, mock_st, mock_render):
        dl = MagicMock()
        _render_spectrum_builder(dl)
        mock_st.subheader.assert_called_once_with("Fourier Coefficient Spectrum")
        mock_render.assert_called_once_with(data_layer=dl, config=None, key_prefix="pb_fourier")


class TestHeatmapBuilder:
    """Tests for _render_heatmap_builder."""

    @patch("adcp_recorder.ui.pages.plot_builder.render_energy_heatmap")
    @patch("adcp_recorder.ui.pages.plot_builder.st")
    def test_calls_render_energy_heatmap(self, mock_st, mock_render):
        dl = MagicMock()
        _render_heatmap_builder(dl)
        mock_st.subheader.assert_called_once_with("Wave Energy Density Heatmap")
        mock_render.assert_called_once_with(data_layer=dl, config=None, key_prefix="pb_heatmap")


class TestPolarBuilder:
    """Tests for _render_polar_builder."""

    @patch("adcp_recorder.ui.pages.plot_builder.render_directional_spectrum")
    @patch("adcp_recorder.ui.pages.plot_builder.st")
    def test_calls_render_directional_spectrum(self, mock_st, mock_render):
        dl = MagicMock()
        _render_polar_builder(dl)
        mock_st.subheader.assert_called_once_with("Directional Spectrum (Polar)")
        mock_render.assert_called_once_with(data_layer=dl, config=None, key_prefix="pb_polar")


# ---------------------------------------------------------------------------
# New render builders (kept from original tests)
# ---------------------------------------------------------------------------
class TestWaveRoseBuilder:
    """Tests for _render_wave_rose_builder."""

    @patch("adcp_recorder.ui.pages.plot_builder.render_wave_rose")
    @patch("adcp_recorder.ui.pages.plot_builder.st")
    def test_calls_render_wave_rose(self, mock_st, mock_render):
        dl = MagicMock()
        _render_wave_rose_builder(dl)
        mock_st.subheader.assert_called_once_with("Wave Rose (Polar Scatter)")
        mock_render.assert_called_once_with(data_layer=dl, config=None, key_prefix="pb_wave_rose")


class TestCurrentSpeedHeatmapBuilder:
    """Tests for _render_current_speed_heatmap_builder."""

    @patch("adcp_recorder.ui.pages.plot_builder.render_current_speed_heatmap")
    @patch("adcp_recorder.ui.pages.plot_builder.st")
    def test_calls_render_current_speed_heatmap(self, mock_st, mock_render):
        dl = MagicMock()
        _render_current_speed_heatmap_builder(dl)
        mock_st.subheader.assert_called_once_with("Current Speed Heatmap")
        mock_render.assert_called_once_with(
            data_layer=dl, config=None, key_prefix="pb_speed_heatmap"
        )


class TestCurrentDirectionPolarBuilder:
    """Tests for _render_current_direction_polar_builder."""

    @patch("adcp_recorder.ui.pages.plot_builder.render_current_direction_polar")
    @patch("adcp_recorder.ui.pages.plot_builder.st")
    def test_calls_render_current_direction_polar(self, mock_st, mock_render):
        dl = MagicMock()
        _render_current_direction_polar_builder(dl)
        mock_st.subheader.assert_called_once_with("Current Direction Polar")
        mock_render.assert_called_once_with(
            data_layer=dl, config=None, key_prefix="pb_current_polar"
        )


class TestAmplitudeHeatmapBuilder:
    """Tests for _render_amplitude_heatmap_builder."""

    @patch("adcp_recorder.ui.pages.plot_builder.render_amplitude_heatmap")
    @patch("adcp_recorder.ui.pages.plot_builder.st")
    def test_calls_render_amplitude_heatmap(self, mock_st, mock_render):
        dl = MagicMock()
        _render_amplitude_heatmap_builder(dl)
        mock_st.subheader.assert_called_once_with("Amplitude Heatmap (Signal Strength)")
        mock_render.assert_called_once_with(data_layer=dl, config=None, key_prefix="pb_amp_heatmap")


# ---------------------------------------------------------------------------
# Dispatch (render_plot_builder selects the right builder)
# ---------------------------------------------------------------------------
class TestPlotBuilderDispatch:
    """Test render_plot_builder dispatches to correct builders."""

    @pytest.fixture
    def mock_st(self):
        """Mock streamlit module in plot_builder."""
        with patch("adcp_recorder.ui.pages.plot_builder.st") as mock_st:
            mock_st.session_state = {}
            col_mock = MagicMock()
            mock_st.columns.return_value = [col_mock, col_mock]
            mock_st.selectbox.return_value = "Wave Rose"
            yield mock_st

    # Original 5 types -------------------------------------------------------
    @patch("adcp_recorder.ui.pages.plot_builder.render_time_series")
    def test_dispatches_time_series(self, mock_render, mock_st):
        mock_st.selectbox.return_value = "Time Series"
        render_plot_builder(MagicMock())
        mock_render.assert_called_once()

    @patch("adcp_recorder.ui.pages.plot_builder.render_velocity_profile")
    def test_dispatches_velocity_profile(self, mock_render, mock_st):
        mock_st.selectbox.return_value = "Velocity Profile"
        render_plot_builder(MagicMock())
        mock_render.assert_called_once()

    @patch("adcp_recorder.ui.pages.plot_builder.render_fourier_spectrum")
    def test_dispatches_spectrum(self, mock_render, mock_st):
        mock_st.selectbox.return_value = "Fourier Spectrum"
        render_plot_builder(MagicMock())
        mock_render.assert_called_once()

    @patch("adcp_recorder.ui.pages.plot_builder.render_energy_heatmap")
    def test_dispatches_heatmap(self, mock_render, mock_st):
        mock_st.selectbox.return_value = "Wave Energy Heatmap"
        render_plot_builder(MagicMock())
        mock_render.assert_called_once()

    @patch("adcp_recorder.ui.pages.plot_builder.render_directional_spectrum")
    def test_dispatches_polar(self, mock_render, mock_st):
        mock_st.selectbox.return_value = "Directional Spectrum (Polar)"
        render_plot_builder(MagicMock())
        mock_render.assert_called_once()

    # New 4 types -------------------------------------------------------------
    @patch("adcp_recorder.ui.pages.plot_builder.render_wave_rose")
    def test_dispatches_wave_rose(self, mock_render, mock_st):
        mock_st.selectbox.return_value = "Wave Rose"
        render_plot_builder(MagicMock())
        mock_render.assert_called_once()

    @patch("adcp_recorder.ui.pages.plot_builder.render_current_speed_heatmap")
    def test_dispatches_current_speed_heatmap(self, mock_render, mock_st):
        mock_st.selectbox.return_value = "Current Speed Heatmap"
        render_plot_builder(MagicMock())
        mock_render.assert_called_once()

    @patch("adcp_recorder.ui.pages.plot_builder.render_current_direction_polar")
    def test_dispatches_current_direction_polar(self, mock_render, mock_st):
        mock_st.selectbox.return_value = "Current Direction Polar"
        render_plot_builder(MagicMock())
        mock_render.assert_called_once()

    @patch("adcp_recorder.ui.pages.plot_builder.render_amplitude_heatmap")
    def test_dispatches_amplitude_heatmap(self, mock_render, mock_st):
        mock_st.selectbox.return_value = "Amplitude Heatmap"
        render_plot_builder(MagicMock())
        mock_render.assert_called_once()


# ---------------------------------------------------------------------------
# Save panel UI (_render_save_panel_ui)
# ---------------------------------------------------------------------------
class TestSavePanelUI:
    """Test save panel configuration extraction for all plot types."""

    @pytest.fixture
    def mock_st(self):
        """Mock streamlit with save panel interactions."""
        with patch("adcp_recorder.ui.pages.plot_builder.st") as mock_st:
            mock_st.session_state = {}
            col_mock = MagicMock()
            mock_st.columns.return_value = [col_mock, col_mock]
            mock_st.text_input.side_effect = lambda label, **kw: kw.get("value", "")
            mock_st.button.return_value = True  # Save button clicked
            yield mock_st

    def _setup_save(self, mock_st, mock_dc, plot_type_name, target="test_dash"):
        """Helper to set up mocks for a save-panel test."""
        mock_st.selectbox.side_effect = [plot_type_name, target]
        mock_dc.list_dashboards.return_value = [target]
        mock_dashboard = MagicMock()
        mock_dc.load.return_value = mock_dashboard
        return mock_dashboard

    # -- Original 5 types ---------------------------------------------------
    @patch("adcp_recorder.ui.config.DashboardConfig")
    @patch("adcp_recorder.ui.pages.plot_builder.render_time_series")
    def test_save_time_series_panel(self, mock_render, mock_dc, mock_st):
        """Save TIME_SERIES panel reconstructs series from session state."""
        mock_dashboard = self._setup_save(mock_st, mock_dc, "Time Series")
        # Populate session state with series data
        mock_st.session_state["pb_ts_num_series"] = 2
        mock_st.session_state["pb_ts_source_0"] = "pnors_df100"
        mock_st.session_state["pb_ts_y_0"] = "temperature"
        mock_st.session_state["pb_ts_label_0"] = "Temp"
        mock_st.session_state["pb_ts_color_0"] = "#FF0000"
        mock_st.session_state["pb_ts_source_1"] = "pnors_df100"
        mock_st.session_state["pb_ts_y_1"] = "pressure"
        mock_st.session_state["pb_ts_label_1"] = None  # Falls back to y value
        mock_st.session_state["pb_ts_color_1"] = None
        mock_st.session_state["pb_ts_time_range"] = "7d"

        render_plot_builder(MagicMock())

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.type == PanelType.TIME_SERIES
        assert len(panel.config["series"]) == 2
        assert panel.config["series"][0]["source"] == "pnors_df100"
        assert panel.config["series"][0]["y"] == "temperature"
        assert panel.config["series"][0]["label"] == "Temp"
        assert panel.config["series"][1]["label"] == "pressure"  # fallback to y
        assert panel.config["time_range"] == "7d"

    @patch("adcp_recorder.ui.config.DashboardConfig")
    @patch("adcp_recorder.ui.pages.plot_builder.render_time_series")
    def test_save_time_series_panel_no_valid_series(self, mock_render, mock_dc, mock_st):
        """TIME_SERIES save with no valid series data produces empty list."""
        mock_dashboard = self._setup_save(mock_st, mock_dc, "Time Series")
        # No series session state keys set (defaults to num_series=1, no source/y)

        render_plot_builder(MagicMock())

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.config["series"] == []

    @patch("adcp_recorder.ui.config.DashboardConfig")
    @patch("adcp_recorder.ui.pages.plot_builder.render_velocity_profile")
    def test_save_velocity_profile_panel(self, mock_render, mock_dc, mock_st):
        """Save VELOCITY_PROFILE panel extracts time_range."""
        mock_dashboard = self._setup_save(mock_st, mock_dc, "Velocity Profile")
        mock_st.session_state["pb_vp_time_range"] = "6h"

        render_plot_builder(MagicMock())

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.type == PanelType.VELOCITY_PROFILE
        assert panel.config["time_range"] == "6h"

    @patch("adcp_recorder.ui.config.DashboardConfig")
    @patch("adcp_recorder.ui.pages.plot_builder.render_fourier_spectrum")
    def test_save_spectrum_panel(self, mock_render, mock_dc, mock_st):
        """Save SPECTRUM panel extracts coefficient and time_range."""
        mock_dashboard = self._setup_save(mock_st, mock_dc, "Fourier Spectrum")
        mock_st.session_state["pb_fourier_coeff"] = "B2"
        mock_st.session_state["pb_fourier_time_range"] = "1h"

        render_plot_builder(MagicMock())

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.type == PanelType.SPECTRUM
        assert panel.config["coefficient"] == "B2"
        assert panel.config["time_range"] == "1h"

    @patch("adcp_recorder.ui.config.DashboardConfig")
    @patch("adcp_recorder.ui.pages.plot_builder.render_energy_heatmap")
    def test_save_heatmap_panel(self, mock_render, mock_dc, mock_st):
        """Save HEATMAP panel extracts time_range."""
        mock_dashboard = self._setup_save(mock_st, mock_dc, "Wave Energy Heatmap")

        render_plot_builder(MagicMock())

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.type == PanelType.HEATMAP
        assert panel.config["time_range"] == "24h"  # default

    @patch("adcp_recorder.ui.config.DashboardConfig")
    @patch("adcp_recorder.ui.pages.plot_builder.render_directional_spectrum")
    def test_save_polar_panel(self, mock_render, mock_dc, mock_st):
        """Save POLAR panel extracts time_range."""
        mock_dashboard = self._setup_save(mock_st, mock_dc, "Directional Spectrum (Polar)")

        render_plot_builder(MagicMock())

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.type == PanelType.POLAR
        assert panel.config["time_range"] == "24h"

    # -- New 4 types --------------------------------------------------------
    @patch("adcp_recorder.ui.config.DashboardConfig")
    @patch("adcp_recorder.ui.pages.plot_builder.render_wave_rose")
    def test_save_wave_rose_panel(self, mock_render, mock_dc, mock_st):
        """Save WAVE_ROSE panel extracts time_range with 7d default."""
        mock_dashboard = self._setup_save(mock_st, mock_dc, "Wave Rose")

        render_plot_builder(MagicMock())

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.type == PanelType.WAVE_ROSE
        assert panel.config["time_range"] == "7d"

    @patch("adcp_recorder.ui.config.DashboardConfig")
    @patch("adcp_recorder.ui.pages.plot_builder.render_current_speed_heatmap")
    def test_save_current_speed_heatmap_panel(self, mock_render, mock_dc, mock_st):
        """Save CURRENT_SPEED_HEATMAP panel extracts time_range."""
        mock_dashboard = self._setup_save(mock_st, mock_dc, "Current Speed Heatmap")

        render_plot_builder(MagicMock())

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.type == PanelType.CURRENT_SPEED_HEATMAP
        assert panel.config["time_range"] == "24h"

    @patch("adcp_recorder.ui.config.DashboardConfig")
    @patch("adcp_recorder.ui.pages.plot_builder.render_current_direction_polar")
    def test_save_current_direction_polar_panel(self, mock_render, mock_dc, mock_st):
        """Save CURRENT_DIRECTION_POLAR panel with 24h default."""
        mock_dashboard = self._setup_save(mock_st, mock_dc, "Current Direction Polar")

        render_plot_builder(MagicMock())

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.type == PanelType.CURRENT_DIRECTION_POLAR
        assert panel.config["time_range"] == "24h"

    @patch("adcp_recorder.ui.config.DashboardConfig")
    @patch("adcp_recorder.ui.pages.plot_builder.render_amplitude_heatmap")
    def test_save_amplitude_heatmap_panel(self, mock_render, mock_dc, mock_st):
        """Save AMPLITUDE_HEATMAP panel with 24h default."""
        mock_dashboard = self._setup_save(mock_st, mock_dc, "Amplitude Heatmap")

        render_plot_builder(MagicMock())

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.type == PanelType.AMPLITUDE_HEATMAP
        assert panel.config["time_range"] == "24h"

    # -- Error branches ------------------------------------------------------
    @patch("adcp_recorder.ui.config.DashboardConfig")
    @patch("adcp_recorder.ui.pages.plot_builder.render_wave_rose")
    def test_save_panel_value_error(self, mock_render, mock_dc, mock_st):
        """ValueError (duplicate panel ID) shows error message."""
        mock_dashboard = self._setup_save(mock_st, mock_dc, "Wave Rose")
        mock_dashboard.add_panel.side_effect = ValueError("duplicate ID")

        render_plot_builder(MagicMock())

        mock_st.error.assert_called()
        assert "already exists" in str(mock_st.error.call_args)

    @patch("adcp_recorder.ui.config.DashboardConfig")
    @patch("adcp_recorder.ui.pages.plot_builder.render_wave_rose")
    def test_save_panel_general_exception(self, mock_render, mock_dc, mock_st):
        """General exception during save shows error message."""
        mock_dashboard = self._setup_save(mock_st, mock_dc, "Wave Rose")
        mock_dashboard.add_panel.side_effect = Exception("db error")

        render_plot_builder(MagicMock())

        mock_st.error.assert_called()
        assert "Failed to save" in str(mock_st.error.call_args)

    @patch("adcp_recorder.ui.pages.plot_builder.render_wave_rose")
    def test_save_panel_no_dashboard_or_id(self, mock_render, mock_st):
        """When no dashboard or panel_id, shows warning."""
        mock_st.selectbox.return_value = "Wave Rose"
        # text_input returns empty string for panel_id
        mock_st.text_input.side_effect = lambda label, **kw: ""
        mock_st.button.return_value = True

        # No dashboards available -> target_dashboard = None
        with patch("adcp_recorder.ui.config.DashboardConfig") as mock_dc:
            mock_dc.list_dashboards.return_value = []

            render_plot_builder(MagicMock())

            # Should show info about no dashboards, button disabled
            mock_st.info.assert_called()

    @patch("adcp_recorder.ui.config.DashboardConfig")
    @patch("adcp_recorder.ui.pages.plot_builder.render_wave_rose")
    def test_save_panel_warning_empty_panel_id(self, mock_render, mock_dc, mock_st):
        """When target_dashboard is set but panel_id is empty, shows warning."""
        mock_st.selectbox.side_effect = ["Wave Rose", "test_dash"]
        mock_dc.list_dashboards.return_value = ["test_dash"]
        # Return empty panel_id but non-empty panel_title
        mock_st.text_input.side_effect = lambda label, **kw: ""
        mock_st.button.return_value = True

        render_plot_builder(MagicMock())

        mock_st.warning.assert_called()
        assert "Please select" in str(mock_st.warning.call_args)

    @patch("adcp_recorder.ui.pages.plot_builder.render_wave_rose")
    def test_save_no_dashboards_shows_info(self, mock_render, mock_st):
        """When no dashboards exist, shows info message."""
        mock_st.selectbox.return_value = "Wave Rose"
        mock_st.text_input.side_effect = lambda label, **kw: kw.get("value", "")
        mock_st.button.return_value = False  # Save button not clicked

        with patch("adcp_recorder.ui.config.DashboardConfig") as mock_dc:
            mock_dc.list_dashboards.return_value = []
            render_plot_builder(MagicMock())
            mock_st.info.assert_called()
