"""Tests for velocity profile depth plot component."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

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
            mock_st.selectbox.return_value = "pnorc_df101"
            mock_st.number_input.return_value = 1.0
            mock_st.multiselect.return_value = []  # Safer default

            yield mock_st

    @pytest.fixture
    def mock_go(self):
        """Mock Plotly."""
        with patch("adcp_recorder.ui.components.velocity_profile.go") as mock_go:
            yield mock_go

    def test_render_velocity_profile_single(self, mock_data_layer, mock_st, mock_go):
        """Test single burst velocity profile rendering."""
        mock_data_layer.get_source_metadata.return_value = MagicMock()
        mock_data_layer.get_available_sources.return_value = [MagicMock(name="pnorc_df101")]
        mock_data_layer.get_available_bursts.return_value = [
            {"received_at": datetime(2026, 1, 23, 12, 0, 0), "label": "2026-01-23 12:00:00"}
        ]

        # Velocity components, Then burst selection
        mock_st.multiselect.side_effect = [["vel1", "vel2"], ["2026-01-23 12:00:00"]]

        mock_data_layer.query_velocity_profile.return_value = {
            "depths": [1, 2, 3],
            "velocities": {"vel1": [0.1, 0.2, 0.3], "vel2": [0.4, 0.5, 0.6]},
        }

        render_velocity_profile(mock_data_layer)

        mock_data_layer.query_velocity_profile.assert_called_once()
        mock_st.plotly_chart.assert_called_once()
        assert mock_go.Scatter.called

    def test_render_velocity_profile_multi(self, mock_data_layer, mock_st, mock_go):
        """Test multiple burst comparison rendering."""
        mock_data_layer.get_source_metadata.return_value = MagicMock()
        mock_data_layer.get_available_bursts.return_value = [
            {"received_at": datetime(2026, 1, 23, 12, 0, 0), "label": "B1"},
            {"received_at": datetime(2026, 1, 23, 13, 0, 0), "label": "B2"},
        ]

        # side_effect for selectbox: source, component to compare
        mock_st.selectbox.side_effect = ["pnorc_df101", "vel1"]
        # side_effect for multiselect: components, then bursts
        mock_st.multiselect.side_effect = [
            ["vel1"],  # components
            ["2026-01-23 12:00:00", "2026-01-23 13:00:00"],  # bursts
        ]

        mock_data_layer.query_velocity_profiles.return_value = [
            {"depths": [1, 2], "velocities": {"vel1": [0.1, 0.2]}},
            {"depths": [1, 2], "velocities": {"vel1": [0.3, 0.4]}},
        ]

        render_velocity_profile(mock_data_layer)

        mock_data_layer.query_velocity_profiles.assert_called_once()
        mock_st.plotly_chart.assert_called_once()

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

        mock_st.info.assert_called_with("No velocity profile data available.")

    def test_render_velocity_profile_error(self, mock_data_layer, mock_st):
        """Test error handling in velocity profile rendering."""
        mock_data_layer.get_source_metadata.return_value = MagicMock()
        mock_data_layer.get_available_bursts.return_value = [
            {"received_at": datetime(2026, 1, 23, 12, 0, 0), "label": "B1"}
        ]
        mock_st.multiselect.side_effect = [["vel1"], ["2026-01-23 12:00:00"]]
        mock_data_layer.query_velocity_profile.side_effect = Exception("Profile Error")

        render_velocity_profile(mock_data_layer)

        mock_st.error.assert_called_with("Error loading velocity profile: Profile Error")

    def test_render_velocity_profile_multi_skip_empty(self, mock_data_layer, mock_st, mock_go):
        """Test skipping empty profiles in multi-burst mode."""
        mock_data_layer.get_source_metadata.return_value = MagicMock()
        mock_data_layer.get_available_bursts.return_value = [
            {"received_at": datetime(2026, 1, 23, 12, 0, 0), "label": "B1"},
            {"received_at": datetime(2026, 1, 23, 13, 0, 0), "label": "B2"},
        ]

        mock_st.selectbox.side_effect = ["pnorc_df101", "vel1"]
        ts1_str = "2026-01-23 12:00:00"
        ts2_str = "2026-01-23 13:00:00"

        mock_st.multiselect.side_effect = [
            ["vel1"],
            [ts1_str, ts2_str],
        ]

        # One valid profile, one empty profile
        mock_data_layer.query_velocity_profiles.return_value = [
            {"depths": [1, 2], "velocities": {"vel1": [0.1, 0.2]}},
            {"depths": [], "velocities": {}},  # Empty
        ]

        render_velocity_profile(mock_data_layer)

        # Should have added at least one trace
        mock_st.plotly_chart.assert_called_once()
        # Verify that we processed the valid one and skipped the empty one safely

    def test_render_velocity_profile_single_skip_empty(self, mock_data_layer, mock_st, mock_go):
        """Test skipping components with empty values in single-burst mode."""
        mock_data_layer.get_source_metadata.return_value = MagicMock()
        mock_data_layer.get_available_bursts.return_value = [
            {"received_at": datetime(2026, 1, 23, 12, 0, 0), "label": "B1"}
        ]

        ts1_str = "2026-01-23 12:00:00"
        mock_st.multiselect.side_effect = [["vel1", "vel2"], [ts1_str]]

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
