"""Unit tests for PNORA parser."""

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
        # Invalid pressure (exceeds ddd.ddd format - max 999.999)
        with pytest.raises(ValueError, match="Pressure out of range"):
            PNORA.from_nmea("$PNORA,250101,120000,1000.0,15.50,95,01,1.5,2.3")

        # Invalid distance (exceeds ddd.ddd format - max 999.999)
        with pytest.raises(ValueError, match="Distance out of range"):
            PNORA.from_nmea("$PNORA,250101,120000,10.5,1000.0,95,01,1.5,2.3")

    def test_pnora_to_dict(self):
        msg = PNORA(
            date="250101",
            time="120000",
            pressure=10.5,
            distance=15.5,
            quality=95,
            status="01",
            pitch=1.5,
            roll=2.3,
        )
        d = msg.to_dict()
        assert d["sentence_type"] == "PNORA"
        assert d["distance"] == 15.5
        assert d["quality"] == 95

    def test_pnora_tagged_format(self):
        # Tagged format (DF=201)
        sentence = "$PNORA,DATE=190902,TIME=122341,P=0.000,A=24.274,Q=13068,ST=08,PI=-2.6,R=-0.8*72"
        msg = PNORA.from_nmea(sentence)
        assert msg.date == "190902"
        assert msg.time == "122341"
        assert msg.pressure == 0.000
        assert msg.distance == 24.274
        assert msg.quality == 13068
        assert msg.status == "08"
        assert msg.pitch == -2.6
        assert msg.roll == -0.8

    def test_pnora_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 9 fields"):
            PNORA.from_nmea("$PNORA,1,2,3,4,5*00")
