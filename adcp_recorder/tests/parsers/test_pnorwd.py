"""Unit tests for PNORWD parser."""
import pytest
from adcp_recorder.parsers.pnorwd import PNORWD

class TestPNORWD:
    def test_pnorwd_parsing(self):
        sentence = "$PNORWD,102115,090715,5,280.5,25.0,1.25*XX"
        msg = PNORWD.from_nmea(sentence)
        assert msg.freq_bin == 5
        assert msg.energy == 1.25
        assert msg.spread_angle == 25.0

    def test_pnorwd_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 7 fields"):
            PNORWD.from_nmea("$PNORWD,1,2,3,4,5*00")

    def test_pnorwd_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORWD.from_nmea("$NOTRWD,1,2,3,4,5,6*00")

    def test_pnorwd_to_dict(self):
        msg = PNORWD("102115", "090715", 1, 2.0, 3.0, 4.0)
        assert msg.to_dict()["sentence_type"] == "PNORWD"
