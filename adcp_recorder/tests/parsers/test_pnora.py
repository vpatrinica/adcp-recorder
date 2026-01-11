"""Unit tests for PNORA parser.
"""

import pytest
from adcp_recorder.parsers.pnora import PNORA


class TestPNORA:
    def test_pnora_parsing_basic(self):
        # 9 fields: prefix, date, time, pressure, distance, quality, status, pitch, roll
        sentence = "$PNORA,250101,120000,10.5,15.50,95,01,1.5,2.3*11"
        msg = PNORA.from_nmea(sentence)
        assert msg.date == "250101"
        assert msg.time == "120000"
        assert msg.pressure == 10.5
        assert msg.distance == 15.50
        assert msg.quality == 95
        assert msg.status == "01"
        assert msg.pitch == 1.5
        assert msg.roll == 2.3

    def test_pnora_validation_errors(self):
        # Invalid pressure
        with pytest.raises(ValueError, match="Pressure out of range"):
            PNORA.from_nmea("$PNORA,250101,120000,20000.1,15.50,95,01,1.5,2.3")
        
        # Invalid distance
        with pytest.raises(ValueError, match="Distance out of range"):
            PNORA.from_nmea("$PNORA,250101,120000,10.5,1001.0,95,01,1.5,2.3")
        
    def test_pnora_to_dict(self):
        msg = PNORA(
            date="250101", time="120000", pressure=10.5, distance=15.5,
            quality=95, status="01", pitch=1.5, roll=2.3
        )
        d = msg.to_dict()
        assert d["sentence_type"] == "PNORA"
        assert d["distance"] == 15.5
        assert d["quality"] == 95

    def test_pnora_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 9 fields"):
            PNORA.from_nmea("$PNORA,1,2,3,4,5*00")
