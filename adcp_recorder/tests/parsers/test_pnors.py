"""Unit tests for PNORS family parsers.
"""

import pytest
from adcp_recorder.parsers.pnors import PNORS, PNORS1, PNORS2, PNORS3, PNORS4


class TestPNORS:
    def test_pnors_parsing_basic(self):
        # 14 fields: prefix, date, time, err, status, batt, ss, h, pi, r, p, t, a1, a2
        sentence = "$PNORS,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,2.3,0.000,22.45,0,0*11"
        msg = PNORS.from_nmea(sentence)
        assert msg.date == "102115"
        assert msg.time == "090715"
        assert msg.error_code == "00000000"
        assert msg.status_code == "2A480000"
        assert msg.battery == 14.4
        assert msg.sound_speed == 1523.0
        assert msg.heading == 275.9
        assert msg.pitch == 15.7
        assert msg.roll == 2.3
        assert msg.pressure == 0.0
        assert msg.temperature == 22.45
        assert msg.analog1 == 0
        assert msg.analog2 == 0

    def test_pnors_validation_errors(self):
        # Invalid heading
        with pytest.raises(ValueError, match="Heading out of range"):
            PNORS.from_nmea("$PNORS,102115,090715,00000000,2A480000,14.4,1523.0,361.0,15.7,2.3,0.000,22.45,0,0")
        
        # Invalid pitch
        with pytest.raises(ValueError, match="Pitch out of range"):
            PNORS.from_nmea("$PNORS,102115,090715,00000000,2A480000,14.4,1523.0,275.9,91.0,2.3,0.000,22.45,0,0")

    def test_pnors_to_dict(self):
        msg = PNORS(
            date="102115", time="090715", error_code="00000000", status_code="00000000",
            battery=12.0, sound_speed=1500.0, heading=0.0, pitch=0.0, roll=0.0,
            pressure=10.0, temperature=15.0, analog1=0, analog2=0
        )
        d = msg.to_dict()
        assert d["sentence_type"] == "PNORS"
        assert d["battery"] == 12.0

    def test_pnors_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 14 fields"):
            PNORS.from_nmea("$PNORS,1,2,3,4,5*00")

    def test_pnors_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORS.from_nmea("$NOTRS,1,2,3,4,5,6,7,8,9,10,11,12,13*00")


class TestPNORS1:
    def test_pnors1_parsing(self):
        # 16 fields: prefix, date, time, ec, sc, batt, ss, hsd, h, pi, pisd, r, rsd, p, psd, t
        sentence = "$PNORS1,102115,090715,0,2A480000,14.4,1523.0,0.1,275.9,15.7,0.2,2.3,0.3,0.000,0.001,22.45*2E"
        msg = PNORS1.from_nmea(sentence)
        assert msg.heading_std_dev == 0.1
        assert msg.pressure_std_dev == 0.001
        assert msg.temperature == 22.45

    def test_pnors1_validation_errors(self):
        # Invalid EC (not int)
        with pytest.raises(ValueError):
            PNORS1.from_nmea("$PNORS1,102115,090715,XY,2A480000,14.4,1523.0,0.1,275.9,15.7,0.2,2.3,0.3,0.000,0.001,22.45")

    def test_pnors1_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 16 fields"):
            PNORS1.from_nmea("$PNORS1,1,2,3,4,5*00")

    def test_pnors1_to_dict(self):
        msg = PNORS1("102115", "090715", 0, "00000000", 12.0, 1500.0, 0.1, 0.0, 0.0, 0.1, 0.0, 0.1, 10.0, 0.001, 15.0)
        assert msg.to_dict()["sentence_type"] == "PNORS1"
        assert msg.to_dict()["error_code"] == 0


class TestPNORS2:
    def test_pnors2_parsing_tagged(self):
        sentence = "$PNORS2,DATE=102115,TIME=090715,EC=0,SC=2A480000,BV=14.4,SS=1523.0,HSD=0.1,H=275.9,PI=15.7,PISD=0.2,R=2.3,RSD=0.3,P=0.000,PSD=0.001,T=22.45*XX"
        msg = PNORS2.from_nmea(sentence)
        assert msg.date == "102115"
        assert msg.battery == 14.4
        assert msg.heading_std_dev == 0.1

    def test_pnors2_missing_tags(self):
        with pytest.raises(ValueError, match="Missing required tags"):
            PNORS2.from_nmea("$PNORS2,DATE=102115,TIME=090715,EC=0")

    def test_pnors2_to_dict(self):
        msg = PNORS2("102115", "090715", 0, "00000000", 12.0, 1500.0, 0.1, 0.0, 0.0, 0.1, 0.0, 0.1, 10.0, 0.001, 15.0)
        assert msg.to_dict()["sentence_type"] == "PNORS2"


class TestPNORS3:
    def test_pnors3_parsing_tagged(self):
        sentence = "$PNORS3,BV=14.4,SS=1523.0,H=275.9,PI=15.7,R=2.3,P=0.000,T=22.45*XX"
        msg = PNORS3.from_nmea(sentence)
        assert msg.battery == 14.4
        assert msg.pressure == 0.0

    def test_pnors3_to_dict(self):
        msg = PNORS3(12.0, 1500.0, 0.0, 0.0, 0.0, 10.0, 15.0)
        assert msg.to_dict()["sentence_type"] == "PNORS3"


class TestPNORS4:
    def test_pnors4_parsing(self):
        # 8 fields: prefix, batt, ss, h, pi, r, p, t
        sentence = "$PNORS4,14.4,1523.0,275.9,15.7,2.3,0.000,22.45*XX"
        msg = PNORS4.from_nmea(sentence)
        assert msg.heading == 275.9
        assert msg.battery == 14.4
        assert msg.temperature == 22.45

    def test_pnors4_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 8 fields"):
            PNORS4.from_nmea("$PNORS4,1,2,3,4*00")

    def test_pnors4_to_dict(self):
        msg = PNORS4(12.0, 1500.0, 0.0, 0.0, 0.0, 10.0, 15.0)
        assert msg.to_dict()["sentence_type"] == "PNORS4"
