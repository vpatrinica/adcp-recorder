"""Tests for velocity profile depth plot component."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("plotly")
pytest.importorskip("streamlit")

from adcp_recorder.ui.components.velocity_profile import (
    render_velocity_comparison,
    render_velocity_profile,
)


class TestVelocityProfile:
    """Test suite for velocity profile component."""

    @pytest.fixture
    def mock_data_layer(self):
        """Mock DataLayer."""
        return MagicMock()

    @pytest.fixture
    def mock_st(self):
        """Mock Streamlit."""
        with patch("adcp_recorder.ui.components.velocity_profile.st") as mock_st:
            mock_st.session_state = {}

            # Smart mock for columns
            def mock_columns(n):
                if isinstance(n, int):
                    return [MagicMock() for _ in range(n)]
                return [MagicMock() for _ in range(len(n))]

            mock_st.columns.side_effect = mock_columns

            mock_st.expander.return_value.__enter__.return_value = MagicMock()
            mock_st.sidebar.__enter__.return_value = MagicMock()

            # Default mocks
            mock_st.selectbox.return_value = "current_profile_12"
            mock_st.number_input.return_value = 1.0
            mock_st.multiselect.return_value = ["vel1", "vel2"]
            mock_st.slider.return_value = 0

            yield mock_st

    @pytest.fixture
    def mock_go(self):
        """Mock Plotly."""
        with patch("adcp_recorder.ui.components.velocity_profile.go") as mock_go:
            yield mock_go

    def test_render_velocity_profile_single(self, mock_data_layer, mock_st, mock_go):
        """Test single measurement velocity profile rendering with time slider."""
        mock_data_layer.get_source_metadata.return_value = MagicMock()
        mock_data_layer.get_available_sources.return_value = [MagicMock(name="current_profile_12")]
        mock_data_layer.get_available_bursts.return_value = [
            {"received_at": datetime(2026, 1, 23, 12, 0, 0), "label": "2026-01-23 12:00:00"}
        ]

        mock_data_layer.query_velocity_profile.return_value = {
            "depths": [1, 2, 3],
            "velocities": {"vel1": [0.1, 0.2, 0.3], "vel2": [0.4, 0.5, 0.6]},
        }

        render_velocity_profile(mock_data_layer)

        mock_data_layer.query_velocity_profile.assert_called_once()
        mock_st.plotly_chart.assert_called_once()
        assert mock_go.Scatter.called

    def test_render_velocity_comparison_basic(self, mock_data_layer, mock_st, mock_go):
        """Test standalone velocity comparison function."""
        timestamps = [datetime(2026, 1, 23, 12, 0), datetime(2026, 1, 23, 13, 0)]
        mock_data_layer.query_velocity_profile.return_value = {
            "depths": [1, 2],
            "velocities": {"vel1": [0.1, 0.2]},
        }

        render_velocity_comparison(mock_data_layer, timestamps)

        assert mock_data_layer.query_velocity_profile.call_count == 2
        mock_st.plotly_chart.assert_called_once()

    def test_render_velocity_profile_no_data(self, mock_data_layer, mock_st):
        """Test handling of missing profile data."""
        mock_data_layer.get_available_sources.return_value = []
        mock_data_layer.get_available_bursts.return_value = []
        mock_data_layer.query_velocity_profile.return_value = {}

        render_velocity_profile(mock_data_layer)

        mock_st.info.assert_called_with(
            "No velocity profile data available in the selected time range."
        )

    def test_render_velocity_profile_error(self, mock_data_layer, mock_st):
        """Test error handling in velocity profile rendering."""
        mock_data_layer.get_source_metadata.return_value = MagicMock()
        mock_data_layer.get_available_bursts.return_value = [
            {"received_at": datetime(2026, 1, 23, 12, 0, 0), "label": "B1"}
        ]
        mock_data_layer.query_velocity_profile.side_effect = Exception("Profile Error")

        render_velocity_profile(mock_data_layer)

        mock_st.error.assert_called_with("Error loading velocity profile: Profile Error")

    def test_render_velocity_profile_empty_depths(self, mock_data_layer, mock_st, mock_go):
        """Test handling of empty depth data for a measurement."""
        mock_data_layer.get_source_metadata.return_value = MagicMock()
        mock_data_layer.get_available_bursts.return_value = [
            {"received_at": datetime(2026, 1, 23, 12, 0, 0), "label": "B1"}
        ]

        mock_data_layer.query_velocity_profile.return_value = {
            "depths": [],
            "velocities": {},
        }

        render_velocity_profile(mock_data_layer)

        mock_st.info.assert_called_with("No velocity profile data for this measurement.")

    def test_render_velocity_profile_skip_empty_component(self, mock_data_layer, mock_st, mock_go):
        """Test skipping components with empty values."""
        mock_data_layer.get_source_metadata.return_value = MagicMock()
        mock_data_layer.get_available_bursts.return_value = [
            {"received_at": datetime(2026, 1, 23, 12, 0, 0), "label": "B1"}
        ]

        # vel1 has data, vel2 is empty
        mock_data_layer.query_velocity_profile.return_value = {
            "depths": [1, 2],
            "velocities": {"vel1": [0.1, 0.2], "vel2": []},
        }

        render_velocity_profile(mock_data_layer)

        mock_st.plotly_chart.assert_called_once()

    def test_render_velocity_comparison_partial_errors(self, mock_data_layer, mock_st):
        """Test partial errors during comparison rendering loop."""
        timestamps = [datetime(2026, 1, 23, 12, 0), datetime(2026, 1, 23, 13, 0)]

        # First call succeeds, second fails
        mock_data_layer.query_velocity_profile.side_effect = [
            {"depths": [1, 2], "velocities": {"vel1": [0.1, 0.2]}},
            Exception("Simulated Error"),
        ]

        render_velocity_comparison(mock_data_layer, timestamps)

        # Should still render what it got
        mock_st.plotly_chart.assert_called_once()

    def test_render_velocity_profile_time_slider(self, mock_data_layer, mock_st, mock_go):
        """Test time slider with multiple available bursts."""
        mock_data_layer.get_source_metadata.return_value = MagicMock()
        mock_data_layer.get_available_bursts.return_value = [
            {"received_at": datetime(2026, 1, 23, 12, 0, 0), "label": "B1"},
            {"received_at": datetime(2026, 1, 23, 13, 0, 0), "label": "B2"},
            {"received_at": datetime(2026, 1, 23, 14, 0, 0), "label": "B3"},
        ]
        # Slider selects second burst
        mock_st.slider.return_value = 1

        mock_data_layer.query_velocity_profile.return_value = {
            "depths": [1, 2],
            "velocities": {"vel1": [0.3, 0.4], "vel2": [0.5, 0.6]},
        }

        render_velocity_profile(mock_data_layer)

        # Should query with second burst's timestamp
        call_kwargs = mock_data_layer.query_velocity_profile.call_args
        assert call_kwargs[1]["timestamp"] == datetime(2026, 1, 23, 13, 0, 0)
        mock_st.plotly_chart.assert_called_once()

    def test_render_velocity_profile_auto_detect_source(self, mock_data_layer, mock_st, mock_go):
        """Test that velocity profile auto-detects the current profile view."""
        # Auto-detect returns pnorc_df100
        mock_data_layer.detect_current_profile_view.return_value = "pnorc_df100"
        mock_data_layer.get_source_metadata.return_value = MagicMock()
        mock_data_layer.get_available_bursts.return_value = [
            {"received_at": datetime(2026, 1, 23, 12, 0, 0), "label": "B1"}
        ]
        mock_data_layer.query_velocity_profile.return_value = {
            "depths": [1, 2],
            "velocities": {"vel1": [0.1, 0.2]},
        }

        # data_source config is ignored; auto-detect is used
        render_velocity_profile(mock_data_layer, config={"data_source": "current_profile_12"})

        mock_data_layer.detect_current_profile_view.assert_called_once()
        call_kwargs = mock_data_layer.query_velocity_profile.call_args
        assert call_kwargs[1]["source_name"] == "pnorc_df100"

    def test_render_velocity_profile_detect_returns_none(self, mock_data_layer, mock_st):
        """Test velocity profile when detect_current_profile_view returns None (lines 69-70)."""
        mock_data_layer.detect_current_profile_view.return_value = None

        render_velocity_profile(mock_data_layer)

        mock_st.info.assert_called_with(
            "No current profile data available. Waiting for PNORC data."
        )

    def test_render_velocity_comparison_detect_returns_none(self, mock_data_layer, mock_st):
        """Test velocity comparison when detect returns None (lines 257-258)."""
        mock_data_layer.detect_current_profile_view.return_value = None

        render_velocity_comparison(mock_data_layer, timestamps=[datetime(2026, 1, 23, 12, 0)])

        mock_st.info.assert_called_with("No current profile data available.")
