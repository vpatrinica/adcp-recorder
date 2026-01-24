"""Tests for UI component ImportError handling."""

from unittest.mock import MagicMock, patch

import pytest

from adcp_recorder.ui.components import (
    spectrum_plots,
    table_view,
    time_series,
    velocity_profile,
)
from adcp_recorder.ui.data_layer import DataLayer


class TestUIImportErrors:
    """Test behavior when optional dependencies are missing."""

    @pytest.fixture
    def mock_data_layer(self):
        return MagicMock(spec=DataLayer)

    def test_spectrum_plots_missing_deps(self, mock_data_layer):
        """Test spectrum_plots raises ImportError when deps are missing."""
        with patch.object(spectrum_plots, "st", None), patch.object(spectrum_plots, "go", None):
            with pytest.raises(ImportError, match="Streamlit and Plotly are required"):
                spectrum_plots.render_fourier_spectrum(mock_data_layer)

            with pytest.raises(ImportError, match="Streamlit and Plotly are required"):
                spectrum_plots.render_energy_heatmap(mock_data_layer)

            with pytest.raises(ImportError, match="Streamlit and Plotly are required"):
                spectrum_plots.render_directional_spectrum(mock_data_layer)

            with pytest.raises(ImportError, match="Streamlit and Plotly are required"):
                spectrum_plots.render_amplitude_heatmap(mock_data_layer)

    def test_table_view_missing_deps(self, mock_data_layer):
        """Test table_view raises ImportError when deps are missing."""
        with patch.object(table_view, "st", None):
            with pytest.raises(ImportError, match="Streamlit is required"):
                table_view.render_table_view(mock_data_layer, "source")

            with pytest.raises(ImportError, match="Streamlit is required"):
                table_view.render_column_selector(MagicMock())

    def test_time_series_missing_deps(self, mock_data_layer):
        """Test time_series raises ImportError when deps are missing."""
        with patch.object(time_series, "st", None), patch.object(time_series, "go", None):
            with pytest.raises(ImportError, match="Streamlit and Plotly are required"):
                time_series.render_time_series(mock_data_layer)

            with pytest.raises(ImportError, match="Streamlit is required"):
                time_series._render_series_builder(mock_data_layer, "prefix")

            with pytest.raises(ImportError, match="Streamlit is required"):
                time_series.render_time_range_selector()

    def test_velocity_profile_missing_deps(self, mock_data_layer):
        """Test velocity_profile raises ImportError when deps are missing."""
        with patch.object(velocity_profile, "st", None), patch.object(velocity_profile, "go", None):
            with pytest.raises(ImportError, match="Streamlit and Plotly are required"):
                velocity_profile.render_velocity_profile(mock_data_layer)

            with pytest.raises(ImportError, match="Streamlit and Plotly are required"):
                velocity_profile.render_velocity_comparison(mock_data_layer, [])

    def test_top_level_import_errors(self):
        """Test top-level ImportError handling (lines 12-14 etc)."""
        import importlib
        import sys
        from unittest.mock import patch

        # Helper to reload with missing deps
        def check_reload_missing_deps(module_name):
            with patch.dict(sys.modules, {"streamlit": None, "plotly": None}):
                # Force reload to hit the top-level try/except
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                else:
                    importlib.import_module(module_name)

                mod = sys.modules[module_name]
                assert mod.st is None
                if hasattr(mod, "go"):
                    assert mod.go is None

        # Test each module
        # Note: We must reload them back to normal state afterwards to not break other tests
        modules = [
            "adcp_recorder.ui.components.spectrum_plots",
            "adcp_recorder.ui.components.table_view",
            "adcp_recorder.ui.components.time_series",
            "adcp_recorder.ui.components.velocity_profile",
        ]

        try:
            for mod_name in modules:
                check_reload_missing_deps(mod_name)
        finally:
            # Restore modules to normal state
            for mod_name in modules:
                if mod_name in sys.modules:
                    importlib.reload(sys.modules[mod_name])
