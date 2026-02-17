"""Tests for spectrum visualization components."""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("plotly")
pytest.importorskip("streamlit")

from adcp_recorder.ui.components.spectrum_plots import (
    render_amplitude_heatmap,
    render_directional_spectrum,
    render_energy_heatmap,
    render_fourier_spectrum,
)


class TestSpectrumPlots:
    """Test suite for spectrum visualization components."""

    @pytest.fixture
    def mock_data_layer(self):
        """Mock DataLayer."""
        return MagicMock()

    @pytest.fixture
    def mock_st(self):
        """Mock Streamlit."""
        with patch("adcp_recorder.ui.components.spectrum_plots.st") as mock_st:
            # Setup common mocks
            mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
            mock_st.session_state = {}
            yield mock_st

    @pytest.fixture
    def mock_go(self):
        """Mock plotly.graph_objects."""
        with patch("adcp_recorder.ui.components.spectrum_plots.go") as mock_go:
            yield mock_go

    def test_render_fourier_spectrum_basic(self, mock_data_layer, mock_st, mock_go):
        """Test basic rendering of Fourier spectrum with time slider."""
        # Setup mocks
        mock_st.selectbox.side_effect = ["A1", "24h"]
        mock_st.checkbox.return_value = False
        mock_st.slider.return_value = 0

        mock_data_layer.query_spectrum_data.return_value = [
            {
                "measurement_date": "2026-01-23",
                "measurement_time": "12:00:00",
                "start_frequency": 0.1,
                "step_frequency": 0.05,
                "num_frequencies": 3,
                "coefficients": [1.0, 1.1, 1.2],
            }
        ]

        render_fourier_spectrum(mock_data_layer)

        # Verify calls
        mock_data_layer.query_spectrum_data.assert_called_once_with(
            source_name="pnorf_data", coefficient="A1", time_range="24h"
        )
        mock_st.plotly_chart.assert_called_once()
        mock_st.slider.assert_called_once()
        assert mock_go.Figure.called
        assert mock_go.Scatter.called

    def test_render_fourier_spectrum_json_string(self, mock_data_layer, mock_st, mock_go):
        """Test rendering Fourier spectrum with JSON string coefficients."""
        mock_st.selectbox.side_effect = ["B1", "6h"]
        mock_st.checkbox.return_value = True
        mock_st.slider.return_value = 0

        mock_data_layer.query_spectrum_data.return_value = [
            {
                "measurement_date": "2026-01-23",
                "measurement_time": "12:00:00",
                "start_frequency": 0.1,
                "step_frequency": 0.05,
                "num_frequencies": 3,
                "coefficients": json.dumps([2.0, 2.1, 2.2]),
            }
        ]

        render_fourier_spectrum(mock_data_layer)
        mock_go.Scatter.assert_called()

    def test_render_fourier_spectrum_no_data(self, mock_data_layer, mock_st):
        """Test rendering Fourier spectrum when no data is available."""
        mock_st.selectbox.side_effect = ["A1", "24h"]
        mock_st.checkbox.return_value = False
        mock_data_layer.query_spectrum_data.return_value = []
        render_fourier_spectrum(mock_data_layer)
        mock_st.info.assert_called()

    def test_render_energy_heatmap_basic(self, mock_data_layer, mock_st, mock_go):
        """Test basic rendering of energy heatmap."""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]  # 2 columns
        mock_st.selectbox.side_effect = ["24h", "Viridis"]

        mock_data_layer.query_wave_energy.return_value = [
            {
                "received_at": datetime(2026, 1, 23, 12, 0, 0),
                "start_frequency": 0.1,
                "step_frequency": 0.05,
                "energy_densities": [0.5, 0.6, 0.7],
            }
        ]

        render_energy_heatmap(mock_data_layer)

        mock_data_layer.query_wave_energy.assert_called_once()
        mock_st.plotly_chart.assert_called_once()
        assert mock_go.Heatmap.called

    def test_render_energy_heatmap_json_string(self, mock_data_layer, mock_st, mock_go):
        """Test rendering energy heatmap with JSON string energies."""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.selectbox.side_effect = ["24h", "Viridis"]
        mock_data_layer.query_wave_energy.return_value = [
            {
                "received_at": datetime(2026, 1, 23, 12, 0, 0),
                "start_frequency": 0.1,
                "step_frequency": 0.05,
                "energy_densities": json.dumps([0.5, 0.6]),
            }
        ]
        render_energy_heatmap(mock_data_layer)
        mock_st.plotly_chart.assert_called()

    def test_render_directional_spectrum_bubble(self, mock_data_layer, mock_st, mock_go):
        """Test directional spectrum bubble plot with time slider."""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.selectbox.return_value = "24h"
        mock_st.radio.return_value = "Bubble Plot"
        mock_st.slider.return_value = 0

        mock_data_layer.get_available_bursts.return_value = [
            {"label": "2026-01-23 12:00:00", "received_at": datetime(2026, 1, 23, 12, 0, 0)}
        ]

        mock_data_layer.query_directional_spectrum.return_value = {
            "frequencies": [0.1, 0.2],
            "directions": [90.0, 180.0],
            "energy": [1.0, 2.0],
            "spreads": [10.0, 15.0],
            "measurement_date": "2026-01-23",
            "measurement_time": "12:00:00",
        }

        render_directional_spectrum(mock_data_layer)

        mock_go.Scatterpolar.assert_called()
        mock_st.plotly_chart.assert_called()

    def test_render_directional_spectrum_heatmap(self, mock_data_layer, mock_st, mock_go):
        """Test directional spectrum heatmap (reconstructed) style."""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.selectbox.return_value = "all"
        mock_st.radio.return_value = "Heatmap (Reconstructed)"
        mock_st.slider.return_value = 0

        mock_data_layer.get_available_bursts.return_value = [
            {"label": "2026-01-23 12:00:00", "received_at": datetime(2026, 1, 23, 12, 0, 0)}
        ]

        mock_data_layer.query_directional_spectrum.return_value = {
            "frequencies": [0.1, 0.2],
            "directions": [90.0, 180.0],
            "energy": [1.0, 2.0],
            "spreads": [10.0, 15.0],
        }

        render_directional_spectrum(mock_data_layer)

        mock_go.Barpolar.assert_called()
        mock_st.plotly_chart.assert_called()

    def test_render_amplitude_heatmap_basic(self, mock_data_layer, mock_st, mock_go):
        """Test basic rendering of amplitude heatmap with auto-detected source."""
        mock_st.selectbox.return_value = "24h"

        # Auto-detect returns a known source
        mock_data_layer.detect_current_profile_view.return_value = "pnorc12"

        mock_data_layer.query_amplitude_heatmap.return_value = [
            {"received_at": datetime(2026, 1, 23, 12, 0, 0), "amplitudes": [10, 20, 30]},
            {
                "received_at": datetime(2026, 1, 23, 13, 0, 0),
                "amplitudes": [15, 25, 35, 45],  # Different length
            },
        ]

        render_amplitude_heatmap(mock_data_layer)

        mock_data_layer.detect_current_profile_view.assert_called_once()
        mock_data_layer.query_amplitude_heatmap.assert_called_with("pnorc12", "24h")
        mock_st.plotly_chart.assert_called_once()
        assert mock_go.Heatmap.called

    def test_render_amplitude_heatmap_no_data(self, mock_data_layer, mock_st):
        """Test amplitude heatmap with no data."""
        mock_data_layer.detect_current_profile_view.return_value = "pnorc12"
        mock_data_layer.query_amplitude_heatmap.return_value = []
        render_amplitude_heatmap(mock_data_layer)
        mock_st.info.assert_called_with("No amplitude data found for the selected time range.")

    def test_error_handling(self, mock_data_layer, mock_st):
        """Test exception handling in render functions."""
        # Fourier spectrum error
        mock_st.selectbox.side_effect = ["A1", "24h"]
        mock_st.checkbox.return_value = False
        mock_data_layer.query_spectrum_data.side_effect = Exception("Test Error")
        render_fourier_spectrum(mock_data_layer)
        mock_st.error.assert_called_with("Error loading Fourier spectrum: Test Error")

        # Energy heatmap error
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.selectbox.side_effect = ["24h", "Viridis"]
        mock_data_layer.query_wave_energy.side_effect = Exception("Test Heatmap Error")
        render_energy_heatmap(mock_data_layer)
        mock_st.error.assert_called_with("Error loading wave energy heatmap: Test Heatmap Error")

        # Directional spectrum error
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.selectbox.side_effect = None
        mock_st.selectbox.return_value = "24h"
        mock_st.radio.return_value = "Bubble Plot"
        mock_st.slider.return_value = 0
        mock_data_layer.get_available_bursts.return_value = [
            {"label": "2026-01-23 12:00:00", "received_at": datetime(2026, 1, 23, 12, 0, 0)}
        ]
        mock_data_layer.query_directional_spectrum.side_effect = Exception("Test Polar Error")
        render_directional_spectrum(mock_data_layer)
        mock_st.error.assert_called_with("Error rendering directional spectrum: Test Polar Error")

    def test_render_fourier_spectrum_json_error(self, mock_data_layer, mock_st):
        """Test JSONDecodeError handling in Fourier spectrum."""
        mock_st.selectbox.side_effect = ["A1", "24h"]
        mock_st.checkbox.return_value = False
        mock_st.slider.return_value = 0
        mock_data_layer.query_spectrum_data.return_value = [
            {
                "coefficients": "INVALID_JSON",
                "start_frequency": 0.1,
                "step_frequency": 0.1,
                "num_frequencies": 10,
            }
        ]
        render_fourier_spectrum(mock_data_layer)
        # Should just continue/skip without erroring
        mock_st.plotly_chart.assert_called()

    def test_render_fourier_spectrum_invalid_coefficients(self, mock_data_layer, mock_st):
        """Test handling of invalid coefficient types."""
        mock_st.selectbox.side_effect = ["A1", "24h"]
        mock_st.checkbox.return_value = False
        mock_st.slider.return_value = 0
        mock_data_layer.query_spectrum_data.return_value = [
            {
                "coefficients": {},  # Not a list
                "start_frequency": 0.1,
                "step_frequency": 0.1,
                "num_frequencies": 10,
            },
            {
                "coefficients": [],  # Empty list
                "start_frequency": 0.1,
                "step_frequency": 0.1,
                "num_frequencies": 10,
            },
        ]
        render_fourier_spectrum(mock_data_layer)
        mock_st.plotly_chart.assert_called()

    def test_render_energy_heatmap_json_error(self, mock_data_layer, mock_st):
        """Test JSONDecodeError handling in energy heatmap."""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.selectbox.side_effect = ["24h", "Viridis"]
        mock_data_layer.query_wave_energy.return_value = [
            {
                "received_at": datetime(2026, 1, 23, 12, 0, 0),
                "energy_densities": "INVALID_JSON",
            }
        ]
        render_energy_heatmap(mock_data_layer)
        mock_st.info.assert_called_with("No valid wave energy records found.")

    def test_render_energy_heatmap_invalid_energies(self, mock_data_layer, mock_st):
        """Test handling of invalid energy types."""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.selectbox.side_effect = ["24h", "Viridis"]
        mock_data_layer.query_wave_energy.return_value = [
            {
                "received_at": datetime(2026, 1, 23, 12, 0, 0),
                "energy_densities": {},  # Not a list
            }
        ]
        render_energy_heatmap(mock_data_layer)
        mock_st.info.assert_called_with("No valid wave energy records found.")

    def test_render_directional_spectrum_no_spectrum(self, mock_data_layer, mock_st):
        """Test directional spectrum with missing frequency data."""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.selectbox.return_value = "24h"
        mock_st.radio.return_value = "Bubble Plot"
        mock_st.slider.return_value = 0
        mock_data_layer.get_available_bursts.return_value = [
            {"label": "2026-01-23 12:00:00", "received_at": datetime(2026, 1, 23, 12, 0, 0)}
        ]
        # Return empty data structure
        mock_data_layer.query_directional_spectrum.return_value = {}

        render_directional_spectrum(mock_data_layer)
        mock_st.info.assert_called_with("No merged directional spectrum data found.")

    def test_render_energy_heatmap_no_data(self, mock_data_layer, mock_st):
        """Test energy heatmap with no data."""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_data_layer.query_wave_energy.return_value = []
        render_energy_heatmap(mock_data_layer)
        mock_st.info.assert_called_with("No wave energy data available in the selected time range.")

    def test_render_directional_spectrum_no_bursts(self, mock_data_layer, mock_st):
        """Test directional spectrum when no bursts are available."""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.selectbox.return_value = "24h"
        mock_st.radio.return_value = "Bubble Plot"
        mock_data_layer.get_available_bursts.return_value = []

        render_directional_spectrum(mock_data_layer)
        mock_st.info.assert_called()

    def test_render_amplitude_heatmap_detect_returns_none(self, mock_data_layer, mock_st):
        """Test amplitude heatmap when detect_current_profile_view returns None (lines 602-603)."""
        mock_data_layer.detect_current_profile_view.return_value = None

        render_amplitude_heatmap(mock_data_layer)

        mock_st.info.assert_called_with("No current profile data available for amplitude heatmap.")
