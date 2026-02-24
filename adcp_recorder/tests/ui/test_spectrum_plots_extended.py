"""Extended tests for spectrum visualization components to close coverage gaps."""

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("plotly")
pytest.importorskip("streamlit")

from adcp_recorder.ui.components.spectrum_plots import (
    render_direction_surface_3d,
    render_energy_surface_3d,
    render_fourier_surface_3d,
    render_spread_surface_3d,
)


class TestSpectrumPlotsExtended:
    """Test suite for spectrum visualization components - extended cases."""

    @pytest.fixture
    def mock_data_layer(self):
        """Mock DataLayer."""
        return MagicMock()

    @pytest.fixture
    def mock_st(self):
        """Mock Streamlit."""
        with patch("adcp_recorder.ui.components.spectrum_plots.st") as mock_st:
            mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n)]
            mock_st.session_state = {}
            yield mock_st

    @pytest.fixture
    def mock_go(self):
        """Mock plotly.graph_objects."""
        with patch("adcp_recorder.ui.components.spectrum_plots.go") as mock_go:
            yield mock_go

    def test_render_fourier_surface_3d_import_error(self, mock_data_layer):
        """Test ImportError in render_fourier_surface_3d (line 733)."""
        with patch("adcp_recorder.ui.components.spectrum_plots.st", None):
            with pytest.raises(ImportError, match="Streamlit and Plotly are required"):
                render_fourier_surface_3d(mock_data_layer)

    def test_render_fourier_surface_3d_json_error(self, mock_data_layer, mock_st, mock_go):
        """Test JSONDecodeError handling in Fourier 3D surface (lines 792-795)."""
        mock_st.selectbox.side_effect = ["A1", "7d", "Viridis"]
        mock_data_layer.query_spectrum_data.return_value = [
            {"coefficients": "INVALID_JSON"},
            {"coefficients": [1.0, 2.0]},  # Valid one to ensure it proceeds
        ]
        render_fourier_surface_3d(mock_data_layer)
        mock_go.Surface.assert_called()

    def test_render_fourier_surface_3d_invalid_format(self, mock_data_layer, mock_st, mock_go):
        """Test handling of non-list coefficients in Fourier 3D surface (line 797)."""
        mock_st.selectbox.side_effect = ["A1", "7d", "Viridis"]
        mock_data_layer.query_spectrum_data.return_value = [
            {"coefficients": {"not": "a list"}},
            {"coefficients": [1.0, 2.0]},  # Valid one to ensure it proceeds
        ]
        render_fourier_surface_3d(mock_data_layer)
        mock_go.Surface.assert_called()

    def test_render_fourier_surface_3d_no_valid_records(self, mock_data_layer, mock_st):
        """Test Fourier 3D surface when no records are valid (lines 805-806)."""
        mock_st.selectbox.side_effect = ["A1", "7d", "Viridis"]
        mock_data_layer.query_spectrum_data.return_value = [
            {"coefficients": None},
        ]
        render_fourier_surface_3d(mock_data_layer)
        mock_st.info.assert_called_with("No valid Fourier records for 3D surface.")

    def test_render_fourier_surface_3d_exception(self, mock_data_layer, mock_st):
        """Test general exception handling in Fourier 3D surface (lines 855-856)."""
        mock_data_layer.query_spectrum_data.side_effect = Exception("General Error")
        render_fourier_surface_3d(mock_data_layer)
        mock_st.error.assert_called()
        assert "Error rendering Fourier 3D surface" in mock_st.error.call_args[0][0]

    def test_render_energy_surface_3d_import_error(self, mock_data_layer):
        """Test ImportError in render_energy_surface_3d (line 876)."""
        with patch("adcp_recorder.ui.components.spectrum_plots.st", None):
            with pytest.raises(ImportError, match="Streamlit and Plotly are required"):
                render_energy_surface_3d(mock_data_layer)

    def test_render_energy_surface_3d_json_error(self, mock_data_layer, mock_st, mock_go):
        """Test JSONDecodeError handling in energy 3D surface (lines 922-925)."""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.selectbox.side_effect = ["7d", "Plasma"]
        mock_data_layer.query_wave_energy.return_value = [
            {"energy_densities": "INVALID_JSON"},
            {"energy_densities": [0.5, 0.6]},  # Valid one
        ]
        render_energy_surface_3d(mock_data_layer)
        mock_go.Surface.assert_called()

    def test_render_energy_surface_3d_invalid_format(self, mock_data_layer, mock_st, mock_go):
        """Test handling of non-list energies in energy 3D surface (line 927)."""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.selectbox.side_effect = ["7d", "Plasma"]
        mock_data_layer.query_wave_energy.return_value = [
            {"energy_densities": 123},
            {"energy_densities": [0.5, 0.6]},  # Valid one
        ]
        render_energy_surface_3d(mock_data_layer)
        mock_go.Surface.assert_called()

    def test_render_energy_surface_3d_no_valid_records(self, mock_data_layer, mock_st):
        """Test energy 3D surface when no records are valid (lines 934-935)."""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.selectbox.side_effect = ["7d", "Plasma"]
        mock_data_layer.query_wave_energy.return_value = [
            {"energy_densities": None},
        ]
        render_energy_surface_3d(mock_data_layer)
        mock_st.info.assert_called_with("No valid energy records for 3D surface.")

    def test_render_energy_surface_3d_exception(self, mock_data_layer, mock_st):
        """Test general exception handling in energy 3D surface (lines 978-979)."""
        mock_data_layer.query_wave_energy.side_effect = Exception("General Error")
        render_energy_surface_3d(mock_data_layer)
        mock_st.error.assert_called()
        assert "Error rendering energy 3D surface" in mock_st.error.call_args[0][0]

    def test_render_direction_surface_3d_import_error(self, mock_data_layer):
        """Test ImportError in render_direction_surface_3d (line 1060)."""
        with patch("adcp_recorder.ui.components.spectrum_plots.st", None):
            with pytest.raises(ImportError, match="Streamlit and Plotly are required"):
                render_direction_surface_3d(mock_data_layer)

    def test_render_direction_surface_3d_exception(self, mock_data_layer, mock_st):
        """Test general exception handling in direction 3D surface (lines 1129-1130)."""
        mock_data_layer.get_available_bursts.side_effect = Exception("General Error")
        render_direction_surface_3d(mock_data_layer)
        mock_st.error.assert_called()
        assert "Error rendering mean direction 3D surface" in mock_st.error.call_args[0][0]

    def test_render_spread_surface_3d_import_error(self, mock_data_layer):
        """Test ImportError in render_spread_surface_3d (line 1150)."""
        with patch("adcp_recorder.ui.components.spectrum_plots.st", None):
            with pytest.raises(ImportError, match="Streamlit and Plotly are required"):
                render_spread_surface_3d(mock_data_layer)

    def test_render_spread_surface_3d_exception(self, mock_data_layer, mock_st):
        """Test general exception handling in spread 3D surface (lines 1219-1220)."""
        mock_data_layer.get_available_bursts.side_effect = Exception("General Error")
        render_spread_surface_3d(mock_data_layer)
        mock_st.error.assert_called()
        assert "Error rendering directional spread 3D surface" in mock_st.error.call_args[0][0]

    def test_functional_import_errors(self, mock_data_layer):
        """Test ImportError raises in various render functions (lines 47, 217, 363, 643)."""
        with patch("adcp_recorder.ui.components.spectrum_plots.st", None):
            from adcp_recorder.ui.components.spectrum_plots import (
                render_amplitude_heatmap,
                render_directional_spectrum,
                render_energy_heatmap,
                render_fourier_spectrum,
            )

            with pytest.raises(ImportError):
                render_fourier_spectrum(mock_data_layer)
            with pytest.raises(ImportError):
                render_energy_heatmap(mock_data_layer)
            with pytest.raises(ImportError):
                render_directional_spectrum(mock_data_layer)
            with pytest.raises(ImportError):
                render_amplitude_heatmap(mock_data_layer)

    def test_module_import_error(self):
        """Test module-level ImportError (lines 16-18)."""
        from importlib import reload

        with patch.dict(
            "sys.modules", {"streamlit": None, "plotly": None, "plotly.graph_objects": None}
        ):
            import adcp_recorder.ui.components.spectrum_plots as sp

            reload(sp)
            assert sp.st is None
            assert sp.go is None

        # Restore for other tests
        reload(sp)

    def test_query_directional_field_surface_all_gaps(self, mock_data_layer, mock_st, mock_go):
        """Cover all remaining gaps in the shared helper (1012, 1016, 1027, 1036-1038)."""
        # Ensure we have enough mock values for all selectbox calls
        mock_st.selectbox.side_effect = ["24h", "HSV", "24h", "HSV", "24h", "HSV", "24h", "HSV"]

        # 1. Test 1027 (not z_rows)
        mock_data_layer.get_available_bursts.return_value = [{"received_at": "ts"}]
        mock_data_layer.query_directional_spectrum.side_effect = None
        mock_data_layer.query_directional_spectrum.return_value = None  # Hits 1012, then 1027
        render_direction_surface_3d(mock_data_layer)
        mock_st.info.assert_called_with("No mean direction data found for 3D surface.")

        # 2. Test 1012, 1016, 1036-1038 in one go
        mock_st.info.reset_mock()
        mock_data_layer.get_available_bursts.return_value = [
            {"received_at": "ts1"},
            {"received_at": "ts2"},
            {"received_at": "ts3"},
        ]
        mock_data_layer.query_directional_spectrum.side_effect = [
            None,  # line 1012: continue
            {"directions": []},  # line 1016: continue
            {  # success + padding 1036-1038
                "frequencies": [0.1],
                "directions": [90, 180],
            },
        ]
        render_direction_surface_3d(mock_data_layer, key_prefix="comprehensive")
        mock_go.Surface.assert_called()
