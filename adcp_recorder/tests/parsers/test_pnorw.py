"""Unit tests for PNORW and specialized parsers.
"""

import pytest
from adcp_recorder.parsers.pnorw import PNORW
from adcp_recorder.parsers.pnorw import PNORW


class TestPNORW:
    def test_pnorw_parsing(self):
        sentence = "$PNORW,102115,090715,2.50,4.10,8.5,285.0*XX"
        msg = PNORW.from_nmea(sentence)
        assert msg.sig_wave_height == 2.50
        assert msg.mean_direction == 285.0

    def test_pnorw_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 7 fields"):
            PNORW.from_nmea("$PNORW,1,2,3,4,5*00")

    def test_pnorw_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORW.from_nmea("$NOTRW,1,2,3,4,5,6*00")

    def test_pnorw_to_dict(self):
        msg = PNORW("102115", "090715", 1.0, 2.0, 3.0, 4.0)
        assert msg.to_dict()["sentence_type"] == "PNORW"


