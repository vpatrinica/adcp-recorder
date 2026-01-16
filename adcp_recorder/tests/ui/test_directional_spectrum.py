import json
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from adcp_recorder.ui.data_layer import DataLayer


class TestDirectionalSpectrum:
    """Test suite for directional spectrum data retrieval and merging."""

    @pytest.fixture
    def mock_conn(self):
        """Create a mock DuckDB connection."""
        return MagicMock()

    @pytest.fixture
    def data_layer(self, mock_conn):
        """Create DataLayer with mock connection."""
        return DataLayer(mock_conn)

    def test_query_directional_spectrum_latest(self, data_layer, mock_conn):
        """Test fetching the latest directional spectrum."""
        # Setup mocks for finding latest
        ts = datetime(2026, 1, 16, 12, 0, 0)
        mock_conn.execute.return_value.fetchone.side_effect = [
            ("160126", "120000", ts),  # Latest burst
            (0.1, 0.05, 3, json.dumps([1.0, 2.0, 3.0]), ts),  # Energy
            (json.dumps([90.0, 180.0, 270.0]),),  # MD
            (json.dumps([10.0, 15.0, 20.0]),),  # DS
        ]

        result = data_layer.query_directional_spectrum()

        assert result["measurement_date"] == "160126"
        assert result["measurement_time"] == "120000"
        assert result["frequencies"] == [0.1, 0.15, 0.2]
        assert result["energy"] == [1.0, 2.0, 3.0]
        assert result["directions"] == [90.0, 180.0, 270.0]
        assert result["spreads"] == [10.0, 15.0, 20.0]
        assert result["timestamp"] == ts

    def test_query_directional_spectrum_by_timestamp(self, data_layer, mock_conn):
        """Test fetching directional spectrum for a specific timestamp."""
        ts = datetime(2026, 1, 16, 10, 30, 0)

        mock_conn.execute.return_value.fetchone.side_effect = [
            (0.1, 0.05, 2, json.dumps([5.0, 6.0]), ts),  # Energy
            (json.dumps([45.0, 135.0]),),  # MD
            (json.dumps([5.0, 8.0]),),  # DS
        ]

        result = data_layer.query_directional_spectrum(timestamp=ts)

        # Verify SQL calls used correct date/time strings
        last_calls = [call.args[1] for call in mock_conn.execute.call_args_list]
        assert ["160126", "103000"] in last_calls

        assert result["frequencies"] == [0.1, 0.15]
        assert result["energy"] == [5.0, 6.0]
        assert result["directions"] == [45.0, 135.0]
        assert result["spreads"] == [5.0, 8.0]

    def test_query_directional_spectrum_no_data(self, data_layer, mock_conn):
        """Test handling of missing data."""
        mock_conn.execute.return_value.fetchone.return_value = None

        result = data_layer.query_directional_spectrum()
        assert result == {}
