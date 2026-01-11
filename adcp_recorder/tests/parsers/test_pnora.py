"""Unit tests for PNORA parser.
"""

import pytest
from adcp_recorder.parsers.pnora import PNORA


class TestPNORA:
    def test_pnora_parsing_basic(self):
        # 9 fields: prefix, date, time, method, distance, status, pitch, roll, pressure
        sentence = "$PNORA,250101,120000,1,15.50,1,1.5,2.3,10.5*11"
        msg = PNORA.from_nmea(sentence)
        assert msg.date == "250101"
        assert msg.time == "120000"
        assert msg.method == 1
        assert msg.distance == 15.50
        assert msg.status == 1
        assert msg.pitch == 1.5
        assert msg.roll == 2.3
        assert msg.pressure == 10.5

    def test_pnora_validation_errors(self):
        # Invalid method
        with pytest.raises(ValueError, match="Altitude method out of range"):
            PNORA.from_nmea("$PNORA,250101,120000,3,15.50,1,1.5,2.3,10.5")
        
        # Invalid distance
        with pytest.raises(ValueError, match="Distance out of range"):
            PNORA.from_nmea("$PNORA,250101,120000,1,1001.0,1,1.5,2.3,10.5")
        
    def test_pnora_to_dict(self):
        msg = PNORA(
            date="250101", time="120000", method=1, distance=15.5,
            status=1, pitch=1.5, roll=2.3, pressure=10.5
        )
        d = msg.to_dict()
        assert d["sentence_type"] == "PNORA"
        assert d["distance"] == 15.5
        assert d["pressure"] == 10.5

    def test_pnora_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 9 fields"):
            PNORA.from_nmea("$PNORA,1,2,3,4,5*00")
