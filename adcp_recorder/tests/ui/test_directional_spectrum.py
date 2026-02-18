import json
from datetime import datetime
from unittest.mock import MagicMock, patch

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

        # Mock metadata resolution
        mock_pnore = MagicMock(name="pq_pnore")
        mock_pnore.name = "pq_pnore"
        mock_pnore.timestamp_column = "received_at"
        mock_pnorwd = MagicMock(name="pq_pnorwd")
        mock_pnorwd.name = "pq_pnorwd"

        def meta_side_effect(name):
            if name == "wave_measurement_full":
                return None
            if "pnore" in name and "pnorwd" not in name:
                return mock_pnore
            return mock_pnorwd

        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.side_effect = meta_side_effect

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

        # Mock metadata resolution
        mock_pnore = MagicMock(name="pq_pnore")
        mock_pnore.name = "pq_pnore"
        mock_pnore.timestamp_column = "received_at"
        mock_pnorwd = MagicMock(name="pq_pnorwd")
        mock_pnorwd.name = "pq_pnorwd"

        def meta_side_effect(name):
            if name == "wave_measurement_full":
                return None
            if "pnore" in name and "pnorwd" not in name:
                return mock_pnore
            return mock_pnorwd

        with patch.object(data_layer, "get_source_metadata") as mock_meta:
            mock_meta.side_effect = meta_side_effect

            mock_conn.execute.return_value.fetchone.side_effect = [
                (0.1, 0.05, 2, json.dumps([5.0, 6.0]), ts, "160126", "103000"),  # Energy (7 values)
                (json.dumps([45.0, 135.0]),),  # MD
                (json.dumps([5.0, 8.0]),),  # DS
            ]

            result = data_layer.query_directional_spectrum(timestamp=ts)

            # The function uses timestamp for direct lookup when timestamp is provided
            assert result["frequencies"] == [0.1, 0.15]
            assert result["energy"] == [5.0, 6.0]
            assert result["directions"] == [45.0, 135.0]
            assert result["spreads"] == [5.0, 8.0]

    def test_query_directional_spectrum_with_alternative_field_names(self, data_layer, mock_conn):
        """If the joined view uses alternative column names,
        `pick` returns the first non-None key.
        """
        ts = datetime(2026, 1, 16, 12, 0, 0)

        # metadata for the joined full view
        mock_full = MagicMock(name="pq_wave_full")
        mock_full.name = "pq_wave_full"
        mock_full.timestamp_column = "received_at"

        def meta_side_effect(name):
            if name == "wave_measurement_full":
                return mock_full
            return None

        with patch.object(data_layer, "get_source_metadata", side_effect=meta_side_effect):
            # Provide description (column names) and a single row using alternative keys
            mock_conn.description = [
                ("received_at",),
                ("start_freq",),
                ("step_freq",),
                ("num_freq",),
                ("energy",),
                ("directions",),
                ("spreads",),
            ]

            mock_conn.execute.return_value.fetchone.return_value = (
                ts,
                0.1,
                0.05,
                3,
                json.dumps([1.0, 2.0, 3.0]),
                json.dumps([90.0, 180.0, 270.0]),
                json.dumps([10.0, 15.0, 20.0]),
            )

            result = data_layer.query_directional_spectrum()
            assert result["frequencies"] == [0.1, 0.15, 0.2]
            assert result["energy"] == [1.0, 2.0, 3.0]
            assert result["directions"] == [90.0, 180.0, 270.0]
            assert result["spreads"] == [10.0, 15.0, 20.0]

        # If no joined view is available, the function should fall back and return empty
        with patch.object(data_layer, "get_source_metadata", return_value=None):
            assert data_layer.query_directional_spectrum() == {}
