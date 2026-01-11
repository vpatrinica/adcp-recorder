"""Unit tests for PNORB parser."""
import pytest
from adcp_recorder.parsers.pnorb import PNORB

class TestPNORB:
    def test_pnorb_parsing(self):
        sentence = "$PNORB,102115,090715,0.523,-0.312,0.001,45.20,88*XX"
        msg = PNORB.from_nmea(sentence)
        assert msg.vel_east == 0.523
        assert msg.bottom_dist == 45.20
        assert msg.quality == 88

    def test_pnorb_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 8 fields"):
            PNORB.from_nmea("$PNORB,1,2,3,4,5,6*00")

    def test_pnorb_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORB.from_nmea("$NOTRB,1,2,3,4,5,6,7*00")

    def test_pnorb_to_dict(self):
        msg = PNORB("102115", "090715", 1.0, 2.0, 3.0, 4.0, 5)
        assert msg.to_dict()["sentence_type"] == "PNORB"
