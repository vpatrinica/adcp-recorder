"""Unit tests for PNORS family parsers.
"""

import pytest
from adcp_recorder.parsers.pnors import PNORS, PNORS1, PNORS2, PNORS3, PNORS4


class TestPNORS:
    def test_pnors_parsing_basic(self):
        sentence = "$PNORS,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,2.3,0.000,22.45,0,0*XX"
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
        sentence = "$PNORS1,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,2.3,0.000,22.45,0,0,35.0*XX"
        msg = PNORS1.from_nmea(sentence)
        assert msg.salinity == 35.0

    def test_pnors1_validation_errors(self):
        # Invalid salinity
        with pytest.raises(ValueError, match="Salinity out of range"):
            PNORS1.from_nmea("$PNORS1,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,2.3,0.000,22.45,0,0,51.0")

    def test_pnors1_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 15 fields"):
            PNORS1.from_nmea("$PNORS1,1,2,3,4,5*00")

    def test_pnors1_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORS1.from_nmea("$NOTRS1,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,2.3,0.000,22.45,0,0,35.0*00")

    def test_pnors1_to_dict(self):
        msg = PNORS1("102115", "090715", "00000000", "00000000", 12.0, 1500.0, 0.0, 0.0, 0.0, 10.0, 15.0, 0, 0, 35.0)
        assert msg.to_dict()["sentence_type"] == "PNORS1"


class TestPNORS2:
    def test_pnors2_parsing_tagged(self):
        # Order shouldn't matter
        sentence = "$PNORS2,DT=102115,TM=090715,ER=00000000,ST=2A480000,BT=14.4,SS=1523.0,HD=275.9,PT=15.7,RL=2.3,PR=0.000,TP=22.45,A1=0,A2=0*XX"
        msg = PNORS2.from_nmea(sentence)
        assert msg.date == "102115"
        assert msg.battery == 14.4

    def test_pnors2_missing_tags(self):
        with pytest.raises(ValueError, match="Expected at least 14 fields"):
            PNORS2.from_nmea("$PNORS2,DT=102115,TM=090715,ER=00000000,ST=2A480000,BT=14.4,SS=1523.0,HD=275.9,PT=15.7,RL=2.3,PR=0.000,TP=22.45,A1=0")

    def test_pnors2_duplicate_tags(self):
        with pytest.raises(ValueError, match="Duplicate tag"):
            PNORS2.from_nmea("$PNORS2,DT=102115,TM=090715,ER=00000000,ST=2A480000,BT=14.4,SS=1523.0,HD=275.9,PT=15.7,RL=2.3,PR=0.000,TP=22.45,A1=0,A1=0")

    def test_pnors2_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORS2.from_nmea("$NOTRS2,DT=102115,TM=090715,ER=00000000,ST=00000000,BT=12,SS=1500,HD=0,PT=0,RL=0,PR=0,TP=15,A1=0,A2=0*00")

    def test_pnors2_to_dict(self):
        msg = PNORS2("102115", "090715", "00000000", "00000000", 12.0, 1500.0, 0.0, 0.0, 0.0, 10.0, 15.0, 0, 0)
        assert msg.to_dict()["sentence_type"] == "PNORS2"


class TestPNORS3:
    def test_pnors3_parsing_compact(self):
        sentence = "$PNORS3,102115,090715,14.4,275.9,15.7,2.3,0.000,22.45*XX"
        msg = PNORS3.from_nmea(sentence)
        assert msg.date == "102115"
        assert msg.pressure == 0.0

    def test_pnors3_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 9 fields"):
            PNORS3.from_nmea("$PNORS3,1,2,3,4,5,6,7*00")

    def test_pnors3_to_dict(self):
        msg = PNORS3("102115", "090715", 12.0, 0.0, 0.0, 0.0, 10.0, 15.0)
        assert msg.to_dict()["sentence_type"] == "PNORS3"


class TestPNORS4:
    def test_pnors4_parsing_minimal(self):
        sentence = "$PNORS4,102115,090715,275.9,0.000,22.45*XX"
        msg = PNORS4.from_nmea(sentence)
        assert msg.heading == 275.9
        assert msg.temperature == 22.45

    def test_pnors4_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 6 fields"):
            PNORS4.from_nmea("$PNORS4,1,2,3,4*00")

    def test_pnors4_to_dict(self):
        msg = PNORS4("102115", "090715", 0.0, 10.0, 15.0)
        assert msg.to_dict()["sentence_type"] == "PNORS4"
