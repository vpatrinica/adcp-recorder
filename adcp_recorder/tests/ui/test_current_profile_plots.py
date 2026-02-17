"""Tests for current profile plot components (speed heatmap + direction polar)."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("plotly")
pytest.importorskip("streamlit")

from adcp_recorder.ui.components.current_profile_plots import (
    render_current_direction_polar,
    render_current_speed_heatmap,
)


class TestCurrentSpeedHeatmap:
    """Test suite for current speed heatmap component."""

    @pytest.fixture
    def mock_data_layer(self):
        """Mock DataLayer."""
        return MagicMock()

    @pytest.fixture
    def mock_st(self):
        """Mock Streamlit."""
        with patch("adcp_recorder.ui.components.current_profile_plots.st") as mock_st:
            mock_st.session_state = {}
            mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
            mock_st.selectbox.side_effect = ["24h", "Viridis"]
            mock_st.checkbox.return_value = False
            yield mock_st

    @pytest.fixture
    def mock_go(self):
        """Mock Plotly."""
        with patch("adcp_recorder.ui.components.current_profile_plots.go") as mock_go:
            yield mock_go

    def test_render_heatmap_basic(self, mock_data_layer, mock_st, mock_go):
        """Test basic current speed heatmap rendering."""
        mock_data_layer.query_current_speed_heatmap.return_value = {
            "timestamps": [datetime(2026, 1, 23, 12, 0), datetime(2026, 1, 23, 13, 0)],
            "cell_indices": [0, 1, 2],
            "cell_distances": None,
            "speeds": [
                [0.1, 0.2],
                [0.3, 0.4],
                [0.5, 0.6],
            ],
            "directions": None,
        }

        render_current_speed_heatmap(mock_data_layer)

        mock_data_layer.query_current_speed_heatmap.assert_called_once()
        mock_st.plotly_chart.assert_called_once()
        mock_go.Heatmap.assert_called()

    def test_render_heatmap_no_data(self, mock_data_layer, mock_st):
        """Test heatmap with no data."""
        mock_data_layer.query_current_speed_heatmap.return_value = {}

        render_current_speed_heatmap(mock_data_layer)

        mock_st.info.assert_called_with(
            "No current profile data available in the selected time range."
        )

    def test_render_heatmap_with_distances(self, mock_data_layer, mock_st, mock_go):
        """Test heatmap with cell distance labels."""
        mock_data_layer.query_current_speed_heatmap.return_value = {
            "timestamps": [datetime(2026, 1, 23, 12, 0)],
            "cell_indices": [0, 1],
            "cell_distances": [2.5, 4.5],
            "speeds": [
                [0.1],
                [0.3],
            ],
            "directions": None,
        }

        render_current_speed_heatmap(mock_data_layer)

        mock_st.plotly_chart.assert_called_once()

    def test_render_heatmap_with_arrows(self, mock_data_layer, mock_st, mock_go):
        """Test heatmap with direction arrows enabled."""
        mock_st.checkbox.return_value = True

        mock_data_layer.query_current_speed_heatmap.return_value = {
            "timestamps": [datetime(2026, 1, 23, 12, 0)],
            "cell_indices": [0, 1],
            "cell_distances": None,
            "speeds": [
                [0.1],
                [0.3],
            ],
            "directions": [
                [90.0],
                [180.0],
            ],
        }

        render_current_speed_heatmap(mock_data_layer)

        mock_st.plotly_chart.assert_called_once()

    def test_render_heatmap_arrows_with_none_direction(self, mock_data_layer, mock_st, mock_go):
        """Test heatmap arrows skip cells with None direction/speed (line 196)."""
        mock_st.checkbox.return_value = True

        mock_data_layer.query_current_speed_heatmap.return_value = {
            "timestamps": [datetime(2026, 1, 23, 12, 0)],
            "cell_indices": [0, 1],
            "cell_distances": None,
            "speeds": [
                [0.1],
                [None],
            ],
            "directions": [
                [None],
                [180.0],
            ],
        }

        render_current_speed_heatmap(mock_data_layer)

        mock_st.plotly_chart.assert_called_once()

    def test_render_heatmap_error(self, mock_data_layer, mock_st):
        """Test error handling."""
        mock_data_layer.query_current_speed_heatmap.side_effect = Exception("DB Error")

        render_current_speed_heatmap(mock_data_layer)

        mock_st.error.assert_called_with("Error rendering current speed heatmap: DB Error")

    def test_render_heatmap_empty_arrays(self, mock_data_layer, mock_st):
        """Test heatmap with empty arrays."""
        mock_data_layer.query_current_speed_heatmap.return_value = {
            "timestamps": [],
            "cell_indices": [],
            "speeds": [],
            "directions": None,
        }

        render_current_speed_heatmap(mock_data_layer)

        mock_st.info.assert_called_with("Insufficient data for heatmap rendering.")

    def test_render_heatmap_detect_returns_none(self, mock_data_layer, mock_st):
        """Test heatmap when detect_current_profile_view returns None (lines 47-48)."""
        mock_data_layer.detect_current_profile_view.return_value = None

        render_current_speed_heatmap(mock_data_layer)

        mock_st.info.assert_called_with(
            "No current profile data available. Waiting for PNORC data."
        )


class TestCurrentDirectionPolar:
    """Test suite for current direction polar component."""

    @pytest.fixture
    def mock_data_layer(self):
        """Mock DataLayer."""
        return MagicMock()

    @pytest.fixture
    def mock_st(self):
        """Mock Streamlit."""
        with patch("adcp_recorder.ui.components.current_profile_plots.st") as mock_st:
            mock_st.session_state = {}
            mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
            mock_st.selectbox.return_value = "24h"
            yield mock_st

    @pytest.fixture
    def mock_go(self):
        """Mock Plotly."""
        with patch("adcp_recorder.ui.components.current_profile_plots.go") as mock_go:
            yield mock_go

    def test_render_polar_basic(self, mock_data_layer, mock_st, mock_go):
        """Test basic polar direction rendering."""
        mock_data_layer.query_current_speed_heatmap.return_value = {
            "timestamps": [datetime(2026, 1, 23, 12, 0)],
            "cell_indices": [0, 1],
            "cell_distances": None,
            "speeds": [
                [0.1],
                [0.3],
            ],
            "directions": [
                [90.0],
                [180.0],
            ],
        }

        render_current_direction_polar(mock_data_layer)

        mock_data_layer.query_current_speed_heatmap.assert_called_once()
        mock_st.plotly_chart.assert_called_once()
        mock_go.Scatterpolar.assert_called()

    def test_render_polar_no_data(self, mock_data_layer, mock_st):
        """Test polar with no data."""
        mock_data_layer.query_current_speed_heatmap.return_value = {}

        render_current_direction_polar(mock_data_layer)

        mock_st.info.assert_called_with(
            "No current profile data available in the selected time range."
        )

    def test_render_polar_no_directions(self, mock_data_layer, mock_st):
        """Test polar when direction data is not available."""
        mock_data_layer.query_current_speed_heatmap.return_value = {
            "timestamps": [datetime(2026, 1, 23, 12, 0)],
            "cell_indices": [0, 1],
            "speeds": [
                [0.1],
                [0.3],
            ],
            "directions": None,
        }

        render_current_direction_polar(mock_data_layer)

        mock_st.info.assert_called_with(
            "Direction data is required for polar plots but is not available."
        )

    def test_render_polar_none_values(self, mock_data_layer, mock_st, mock_go):
        """Test polar with some None speed/direction values."""
        mock_data_layer.query_current_speed_heatmap.return_value = {
            "timestamps": [datetime(2026, 1, 23, 12, 0)],
            "cell_indices": [0, 1],
            "speeds": [
                [None],
                [0.3],
            ],
            "directions": [
                [90.0],
                [180.0],
            ],
        }

        render_current_direction_polar(mock_data_layer)

        # Should render with just the valid point
        mock_st.plotly_chart.assert_called_once()

    def test_render_polar_all_none(self, mock_data_layer, mock_st):
        """Test polar when all values are None."""
        mock_data_layer.query_current_speed_heatmap.return_value = {
            "timestamps": [datetime(2026, 1, 23, 12, 0)],
            "cell_indices": [0],
            "speeds": [
                [None],
            ],
            "directions": [
                [None],
            ],
        }

        render_current_direction_polar(mock_data_layer)

        mock_st.info.assert_called_with("No valid speed/direction pairs found in the data.")

    def test_render_polar_error(self, mock_data_layer, mock_st):
        """Test error handling."""
        mock_data_layer.query_current_speed_heatmap.side_effect = Exception("Polar Error")

        render_current_direction_polar(mock_data_layer)

        mock_st.error.assert_called_with("Error rendering current direction polar: Polar Error")

    def test_render_polar_detect_returns_none(self, mock_data_layer, mock_st):
        """Test polar when detect_current_profile_view returns None (lines 248-249)."""
        mock_data_layer.detect_current_profile_view.return_value = None

        render_current_direction_polar(mock_data_layer)

        mock_st.info.assert_called_with(
            "No current profile data available. Waiting for PNORC data."
        )
