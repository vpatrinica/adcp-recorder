import pytest
from adcp_recorder.parsers.pnorb import PNORB


class TestPNORB:
    def test_pnorb_parsing(self):
        sentence = "$PNORB,102115,090715,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*XX"
        msg = PNORB.from_nmea(sentence)
        assert msg.spectrum_basis == 1
        assert msg.processing_method == 4
        assert msg.freq_low == 0.02
        assert msg.freq_high == 0.20
        assert msg.hmo == 0.27
        assert msg.tm02 == 7.54
        assert msg.tp == 12.00
        assert msg.dirtp == 82.42
        assert msg.sprtp == 75.46
        assert msg.main_dir == 82.10
        assert msg.wave_error_code == "0000"

    def test_pnorb_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 14 fields"):
            PNORB.from_nmea("$PNORB,1,2,3,4,5,6*00")

    def test_pnorb_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORB.from_nmea("$NOTRB,102115,090715,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*XX")
