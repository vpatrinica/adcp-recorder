"""Unit tests for PNORB parser.
"""

import pytest
from adcp_recorder.parsers.pnorb import PNORB


class TestPNORB:
    def test_pnorb_parsing(self):
        # 14 fields: prefix, date, time, basis, method, flow, fhigh, hm0, tm02, tp, dir_tp, spr_tp, main, err
        sentence = "$PNORB,102115,090715,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*32"
        msg = PNORB.from_nmea(sentence)
        assert msg.spectrum_basis == 1
        assert msg.processing_method == 4
        assert msg.freq_low == 0.02
        assert msg.freq_high == 0.20
        assert msg.hm0 == 0.27
        assert msg.tm02 == 7.54
        assert msg.tp == 12.00
        assert msg.dir_tp == 82.42
        assert msg.spr_tp == 75.46
        assert msg.main_dir == 82.10
        assert msg.wave_error_code == "0000"

    def test_pnorb_optional_fields(self):
        # Test -9.0000 indicator
        sentence = "$PNORB,102115,090715,1,4,0.02,0.20,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,-9.0000,0001*XX"
        msg = PNORB.from_nmea(sentence)
        assert msg.hm0 is None
        assert msg.tp is None
        assert msg.main_dir is None

    def test_pnorb_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 14 fields"):
            PNORB.from_nmea("$PNORB,1,2,3,4,5,6*00")

    def test_pnorb_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORB.from_nmea("$NOTRB,102115,090715,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*XX")

    def test_pnorb_to_dict(self):
        msg = PNORB(
            date="102115", time="090715", spectrum_basis=1, processing_method=4,
            freq_low=0.02, freq_high=0.20, hm0=0.27, tm02=7.54, tp=12.00,
            dir_tp=82.42, spr_tp=75.46, main_dir=82.10, wave_error_code="0000"
        )
        d = msg.to_dict()
        assert d["sentence_type"] == "PNORB"
        assert d["hm0"] == 0.27
