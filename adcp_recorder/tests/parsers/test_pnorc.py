"""Unit tests for PNORC family parsers.
"""

import pytest
from adcp_recorder.parsers.pnorc import PNORC, PNORC1, PNORC2, PNORC3, PNORC4


class TestPNORC:
    def test_pnorc_parsing_basic(self):
        # 17 fields: prefix, date, time, cell, dist, vel1-4, amp1-4, corr1-4
        sentence = "$PNORC,102115,090715,1,1.00,0.1,0.2,0.3,0.4,100,101,102,103,90,91,92,93*11"
        msg = PNORC.from_nmea(sentence)
        assert msg.date == "102115"
        assert msg.cell_index == 1
        assert msg.distance == 1.0
        assert msg.vel1 == 0.1
        assert msg.vel4 == 0.4
        assert msg.amp1 == 100
        assert msg.corr4 == 93

    def test_pnorc_validation_errors(self):
        # Invalid cell index
        with pytest.raises(ValueError, match="Cell index out of range"):
            PNORC.from_nmea("$PNORC,102115,090715,0,1.00,0.1,0.2,0.3,0.4,100,101,102,103,90,91,92,93")
        
    def test_pnorc_to_dict(self):
        msg = PNORC(
            date="102115", time="090715", cell_index=1, distance=1.0,
            vel1=0.1, vel2=0.2, vel3=0.3, vel4=0.4,
            amp1=100, amp2=101, amp3=102, amp4=103,
            corr1=90, corr2=91, corr3=92, corr4=93
        )
        d = msg.to_dict()
        assert d["sentence_type"] == "PNORC"
        assert d["vel4"] == 0.4

    def test_pnorc_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 17 fields"):
            PNORC.from_nmea("$PNORC,1,2,3,4,5*00")


class TestPNORC1:
    def test_pnorc1_parsing(self):
        # Amplitudes are floats (dB)
        sentence = "$PNORC1,102115,090715,1,1.00,0.1,0.2,0.3,0.4,45.5,46.0,45.8,45.2,90,91,92,93*XX"
        msg = PNORC1.from_nmea(sentence)
        assert msg.amp1 == 45.5
        assert msg.corr1 == 90

    def test_pnorc1_to_dict(self):
        msg = PNORC1(
            date="102115", time="090715", cell_index=1, distance=1.0,
            vel1=0.1, vel2=0.2, vel3=0.3, vel4=0.4,
            amp1=45.5, amp2=46.0, amp3=45.8, amp4=45.2,
            corr1=90, corr2=91, corr3=92, corr4=93
        )
        assert msg.to_dict()["sentence_type"] == "PNORC1"


class TestPNORC2:
    def test_pnorc2_parsing_tagged(self):
        # Flexible tags: VE/VN/VU/VU2, etc.
        sentence = "$PNORC2,DATE=102115,TIME=090715,CN=1,CP=1.00,VE=0.1,VN=0.2,VU=0.3,VU2=0.4,A1=45.5,A2=46.0,A3=45.8,A4=45.2,C1=90,C2=91,C3=92,C4=93*XX"
        msg = PNORC2.from_nmea(sentence)
        assert msg.cell_index == 1
        assert msg.vel1 == 0.1
        assert msg.amp1 == 45.5

    def test_pnorc2_flexible_vel_tags(self):
        sentence = "$PNORC2,DATE=102115,TIME=090715,CN=1,CP=1.00,VX=0.1,VY=0.2,VZ=0.3,VZ2=0.4,A1=45.5,A2=46.0,A3=45.8,A4=45.2,C1=90,C2=91,C3=92,C4=93*XX"
        msg = PNORC2.from_nmea(sentence)
        assert msg.vel1 == 0.1
        assert msg.vel4 == 0.4

    def test_pnorc2_to_dict(self):
        msg = PNORC2(
            date="102115", time="090715", cell_index=1, distance=1.0,
            vel1=0.1, vel2=0.2, vel3=0.3, vel4=0.4,
            amp1=45.5, amp2=46.0, amp3=45.8, amp4=45.2,
            corr1=90, corr2=91, corr3=92, corr4=93
        )
        assert msg.to_dict()["sentence_type"] == "PNORC2"


class TestPNORC3:
    def test_pnorc3_parsing_averaged(self):
        # $PNORC3,CP=Dist,SP=Speed,DIR=Dir,AA=AvgAmp,AC=AvgCorr*CS
        sentence = "$PNORC3,CP=10.5,SP=1.23,DIR=180.5,AA=150,AC=95*XX"
        msg = PNORC3.from_nmea(sentence)
        assert msg.distance == 10.5
        assert msg.speed == 1.23
        assert msg.direction == 180.5
        assert msg.avg_amplitude == 150
        assert msg.avg_correlation == 95

    def test_pnorc3_to_dict(self):
        msg = PNORC3(10.5, 1.23, 180.5, 150, 95)
        assert msg.to_dict()["sentence_type"] == "PNORC3"


class TestPNORC4:
    def test_pnorc4_parsing_averaged(self):
        # $PNORC4,Dist,Speed,Dir,AA,AC*CS
        sentence = "$PNORC4,10.5,1.23,180.5,150,95*XX"
        msg = PNORC4.from_nmea(sentence)
        assert msg.distance == 10.5
        assert msg.speed == 1.23
        assert msg.avg_correlation == 95

    def test_pnorc4_to_dict(self):
        msg = PNORC4(10.5, 1.23, 180.5, 150, 95)
        assert msg.to_dict()["sentence_type"] == "PNORC4"
