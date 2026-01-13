"""Unit tests for PNORW and specialized parsers."""

import pytest

from adcp_recorder.parsers.pnorw import PNORW


class TestPNORW:
    def test_pnorw_parsing(self):
        # 22 fields: prefix, date, time, basis, method, hm0, h3, h10, hmax,
        # tm02, tp, tz, dir_tp, spr_tp, main_dir, ui, press, no, bad, ns_v,
        # ns_d, err
        sentence = (
            "$PNORW,102125,090715,1,2,2.50,2.30,2.40,4.10,8.5,10.0,9.0,"
            "285.0,15.0,280.0,0.95,10.5,0,0,0.1,180.0,0000*XX"
        )
        msg = PNORW.from_nmea(sentence)
        assert msg.date == "102125"
        assert msg.hm0 == 2.50
        assert msg.hmax == 4.10
        assert msg.tp == 10.0
        assert msg.near_surface_speed == 0.1
        assert msg.wave_error_code == "0000"

    def test_pnorw_optional_fields(self):
        # Test -9.000 indicator (should be None)
        sentence = (
            "$PNORW,102125,090715,1,2,-9.000,-9.000,-9.000,-9.000,-9.000,"
            "-9.000,-9.000,-9.000,-9.000,-9.000,-9.000,10.5,0,0,-9.000,"
            "-9.000,0001*XX"
        )
        msg = PNORW.from_nmea(sentence)
        assert msg.hm0 is None
        assert msg.tp is None
        assert msg.near_surface_speed is None
        assert msg.wave_error_code == "0001"

    def test_pnorw_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 22 fields"):
            PNORW.from_nmea("$PNORW,1,2,3,4,5*00")

    def test_pnorw_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORW.from_nmea("$NOTRW,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21*00")

    def test_pnorw_to_dict(self):
        msg = PNORW(
            date="102125",
            time="090715",
            spectrum_basis=1,
            processing_method=2,
            hm0=1.0,
            h3=1.1,
            h10=1.2,
            hmax=1.3,
            tm02=8.0,
            tp=9.0,
            tz=8.5,
            dir_tp=180.0,
            spr_tp=10.0,
            main_dir=185.0,
            uni_index=0.9,
            mean_pressure=10.0,
            num_no_detects=0,
            num_bad_detects=0,
            near_surface_speed=0.1,
            near_surface_dir=190.0,
            wave_error_code="0000",
        )
        d = msg.to_dict()
        assert d["sentence_type"] == "PNORW"
        assert d["hm0"] == 1.0
        assert d["wave_error_code"] == "0000"
