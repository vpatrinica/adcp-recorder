"""Tests for wave rose / polar scatter component."""

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("plotly")
pytest.importorskip("streamlit")

from adcp_recorder.ui.components.wave_rose import render_wave_rose


class TestWaveRose:
    """Test suite for wave rose component."""

    @pytest.fixture
    def mock_data_layer(self):
        """Mock DataLayer."""
        return MagicMock()

    @pytest.fixture
    def mock_st(self):
        """Mock Streamlit."""
        with patch("adcp_recorder.ui.components.wave_rose.st") as mock_st:
            mock_st.session_state = {}
            mock_st.columns.return_value = [MagicMock(), MagicMock()]
            mock_st.radio.return_value = "full_spectrum"
            mock_st.selectbox.return_value = "7d"
            yield mock_st

    @pytest.fixture
    def mock_go(self):
        """Mock Plotly."""
        with patch("adcp_recorder.ui.components.wave_rose.go") as mock_go:
            yield mock_go

    def test_render_wave_rose_basic(self, mock_data_layer, mock_st, mock_go):
        """Test basic wave rose rendering."""
        mock_data_layer.query_wave_rose_data.return_value = [
            {"dir_tp": 90.0, "hm0": 1.5, "tp": 8.0},
            {"dir_tp": 180.0, "hm0": 2.0, "tp": 10.0},
            {"dir_tp": 270.0, "hm0": 0.8, "tp": 6.0},
        ]

        render_wave_rose(mock_data_layer)

        mock_data_layer.query_wave_rose_data.assert_called_once()
        mock_st.plotly_chart.assert_called_once()
        mock_go.Scatterpolar.assert_called()

    def test_render_wave_rose_no_data(self, mock_data_layer, mock_st):
        """Test wave rose with no data."""
        mock_data_layer.query_wave_rose_data.return_value = []

        render_wave_rose(mock_data_layer)

        mock_st.info.assert_called_with("No wave rose data available in the selected time range.")

    def test_render_wave_rose_none_values(self, mock_data_layer, mock_st):
        """Test wave rose filtering out None values."""
        mock_data_layer.query_wave_rose_data.return_value = [
            {"dir_tp": None, "hm0": 1.5, "tp": 8.0},
            {"dir_tp": 90.0, "hm0": None, "tp": 10.0},
            {"dir_tp": 180.0, "hm0": 2.0, "tp": None},
        ]

        render_wave_rose(mock_data_layer)

        mock_st.info.assert_called_with(
            "No valid wave parameters with complete DirTp, Hm0, and Tp values."
        )

    def test_render_wave_rose_frequency_bands(self, mock_data_layer, mock_st, mock_go):
        """Test wave rose in frequency_bands mode."""
        mock_st.radio.return_value = "frequency_bands"

        mock_data_layer.query_wave_rose_data.return_value = [
            {"dir_tp": 45.0, "hm0": 0.5, "tp": 4.0},
        ]

        render_wave_rose(mock_data_layer)

        # Should query with band_source
        call_args = mock_data_layer.query_wave_rose_data.call_args
        assert call_args[1]["source_name"] == "pnorb_data"

    def test_render_wave_rose_error(self, mock_data_layer, mock_st):
        """Test error handling in wave rose."""
        mock_data_layer.query_wave_rose_data.side_effect = Exception("Query Error")

        render_wave_rose(mock_data_layer)

        mock_st.error.assert_called_with("Error rendering wave rose: Query Error")

    def test_render_wave_rose_config(self, mock_data_layer, mock_st, mock_go):
        """Test wave rose with custom config."""
        mock_data_layer.query_wave_rose_data.return_value = [
            {"dir_tp": 90.0, "hm0": 1.5, "tp": 8.0},
        ]

        config = {
            "data_source": "custom_wave_view",
            "band_source": "custom_band",
            "mode": "full_spectrum",
            "time_range": "30d",
        }

        render_wave_rose(mock_data_layer, config=config)

        mock_st.plotly_chart.assert_called_once()

    def test_render_wave_rose_summary_metrics(self, mock_data_layer, mock_st, mock_go):
        """Test that summary metrics (st.metric) and caption are rendered."""
        mock_st.columns.side_effect = [
            [MagicMock(), MagicMock()],  # for controls
            [MagicMock(), MagicMock(), MagicMock()],  # for metrics
        ]
        mock_data_layer.query_wave_rose_data.return_value = [
            {"dir_tp": 90.0, "hm0": 1.0, "tp": 6.0},
            {"dir_tp": 180.0, "hm0": 2.0, "tp": 10.0},
        ]

        render_wave_rose(mock_data_layer)

        # Should call st.metric 3 times (Records, Avg Hm0, Avg Tp)
        assert mock_st.metric.call_count == 3
        calls = mock_st.metric.call_args_list
        assert calls[0][0][0] == "Records"
        assert calls[0][0][1] == 2
        assert calls[1][0][0] == "Avg Hm0"
        assert calls[2][0][0] == "Avg Tp"
        # Should render caption
        mock_st.caption.assert_called_once()
