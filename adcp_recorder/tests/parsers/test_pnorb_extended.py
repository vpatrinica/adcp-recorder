"""Extended unit tests for PNORB parser."""

import pytest

from adcp_recorder.parsers.pnorb import PNORB


class TestPNORBExtended:
    def test_pnorb_high_hm0(self):
        # User reported 182.29
        sentence = "$PNORB,102115,090715,1,4,0.02,0.20,182.29,7.54,12.00,82.42,75.46,82.10,0000*00"
        # We don't care about checksum in from_nmea if it's not verified yet
        msg = PNORB.from_nmea(sentence)
        assert msg.hm0 == 182.29

    def test_pnorb_max_range(self):
        sentence = (
            "$PNORB,102115,090715,1,4,0.02,0.20,1000.0,1000.0,1000.0,360.0,360.0,360.0,0000*00"
        )
        msg = PNORB.from_nmea(sentence)
        assert msg.hm0 == 1000.0
        assert msg.tm02 == 1000.0
        assert msg.tp == 1000.0
        assert msg.dir_tp == 360.0
        assert msg.spr_tp == 360.0
        assert msg.main_dir == 360.0

    def test_pnorb_out_of_new_range(self):
        with pytest.raises(ValueError, match="Hm0 out of range"):
            PNORB(
                date="102115",
                time="090715",
                spectrum_basis=1,
                processing_method=4,
                freq_low=0.02,
                freq_high=0.20,
                hm0=1000.1,
                tm02=7.54,
                tp=12.00,
                dir_tp=82.42,
                spr_tp=75.46,
                main_dir=82.10,
                wave_error_code="0000",
            )

    def test_pnorb_direction_out_of_range(self):
        with pytest.raises(ValueError, match="DirTp out of range"):
            PNORB(
                date="102115",
                time="090715",
                spectrum_basis=1,
                processing_method=4,
                freq_low=0.02,
                freq_high=0.20,
                hm0=10.0,
                tm02=7.54,
                tp=12.00,
                dir_tp=360.1,
                spr_tp=75.46,
                main_dir=82.10,
                wave_error_code="0000",
            )
