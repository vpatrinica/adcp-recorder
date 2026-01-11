"""Unit tests for PNORF parser."""
import pytest
from adcp_recorder.parsers.pnorf import PNORF

class TestPNORF:
    def test_pnorf_parsing(self):
        sentence = "$PNORF,102115,090715,600.0,15.0,25.5*XX"
        msg = PNORF.from_nmea(sentence)
        assert msg.frequency == 600.0
        assert msg.transmit_power == 25.5

    def test_pnorf_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 6 fields"):
            PNORF.from_nmea("$PNORF,1,2,3,4*00")

    def test_pnorf_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORF.from_nmea("$NOTRF,1,2,3,4,5*00")

    def test_pnorf_to_dict(self):
        msg = PNORF("102115", "090715", 600.0, 15.0, 25.5)
        assert msg.to_dict()["sentence_type"] == "PNORF"
