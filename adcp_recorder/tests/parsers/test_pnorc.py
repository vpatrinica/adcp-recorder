"""Unit tests for PNORC family parsers.
"""

import pytest
from adcp_recorder.parsers.pnorc import PNORC, PNORC1, PNORC2, PNORC3, PNORC4


class TestPNORC:
    def test_pnorc_parsing_basic(self):
        sentence = "$PNORC,102115,090715,1,0.123,-0.456,0.012*XX"
        msg = PNORC.from_nmea(sentence)
        assert msg.date == "102115"
        assert msg.cell_index == 1
        assert msg.vel1 == 0.123
        assert msg.vel3 == 0.012

    def test_pnorc_validation_errors(self):
        # Invalid cell index
        with pytest.raises(ValueError, match="Cell index out of range"):
            PNORC.from_nmea("$PNORC,102115,090715,0,0.123,-0.456,0.012")
        
        # Invalid velocity
        with pytest.raises(ValueError, match="Velocity 1 out of range"):
            PNORC.from_nmea("$PNORC,102115,090715,1,11.0,-0.456,0.012")

    def test_pnorc_to_dict(self):
        msg = PNORC(date="102115", time="090715", cell_index=1, vel1=1.0, vel2=2.0, vel3=3.0)
        d = msg.to_dict()
        assert d["sentence_type"] == "PNORC"
        assert d["vel1"] == 1.0

    def test_pnorc_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 7 fields"):
            PNORC.from_nmea("$PNORC,1,2,3,4,5*00")

    def test_pnorc_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORC.from_nmea("$NOTRC,1,2,3,4,5,6*00")


class TestPNORC1:
    def test_pnorc1_parsing(self):
        sentence = "$PNORC1,102115,090715,1,0.123,-0.456,0.012,95,92,88*XX"
        msg = PNORC1.from_nmea(sentence)
        assert msg.corr1 == 95
        assert msg.corr3 == 88

    def test_pnorc1_validation_errors(self):
        # Invalid correlation
        with pytest.raises(ValueError, match="Correlation 1 out of range"):
            PNORC1.from_nmea("$PNORC1,102115,090715,1,0.123,-0.456,0.012,101,92,88")

    def test_pnorc1_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 10 fields"):
            PNORC1.from_nmea("$PNORC1,1,2,3,4,5,6,7,8*00")

    def test_pnorc1_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORC1.from_nmea("$NOTRC1,1,2,3,4,5,6,7,8,9*00")

    def test_pnorc1_to_dict(self):
        msg = PNORC1("102115", "090715", 1, 1.0, 2.0, 3.0, 90, 91, 92)
        assert msg.to_dict()["sentence_type"] == "PNORC1"


class TestPNORC2:
    def test_pnorc2_parsing_tagged(self):
        sentence = "$PNORC2,DT=102115,TM=090715,CI=1,VE=0.123,VN=-0.456,VU=0.012*XX"
        msg = PNORC2.from_nmea(sentence)
        assert msg.date == "102115"
        assert msg.cell_index == 1
        assert msg.vel1 == 0.123

    def test_pnorc2_missing_tags(self):
        with pytest.raises(ValueError, match="Expected at least 7 fields"):
            PNORC2.from_nmea("$PNORC2,DT=102115,TM=090715,CI=1,VE=0.123,VN=-0.456")

    def test_pnorc2_invalid_tag_format(self):
        with pytest.raises(ValueError, match="must contain '='"):
            PNORC2.from_nmea("$PNORC2,DT=102115,TM=090715,CI=1,VE=0.123,VN=-0.456,INVALID*00")

    def test_pnorc2_unknown_tag_raises_error(self):
        # Unknown tags are NOT allowed in the current strict implementation
        sentence = "$PNORC2,DT=102115,TM=090715,CI=1,VE=0.123,VN=-0.456,VU=0.012,XX=1*XX"
        with pytest.raises(ValueError, match="Unknown tags in PNORC2"):
            PNORC2.from_nmea(sentence)

    def test_pnorc2_duplicate_tag(self):
        with pytest.raises(ValueError, match="Duplicate tag in PNORC2"):
            PNORC2.from_nmea("$PNORC2,DT=102115,DT=102115,TM=090715,CI=1,VE=0.123,VN=-0.456*00")

    def test_pnorc2_missing_required_tag(self):
        with pytest.raises(ValueError, match="Missing required tags"):
            # 7 fields: prefix + 6 data. One is unknown (XX=1), so 'VU' is missing
            PNORC2.from_nmea("$PNORC2,DT=102115,TM=090715,CI=1,VE=0.123,VN=-0.456,XX=1*00")

    def test_pnorc2_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORC2.from_nmea("$NOTRC2,DT=102115,TM=090715,CI=1,VE=0.123,VN=-0.456,VU=0.012*00")

    def test_pnorc2_to_dict(self):
        msg = PNORC2("102115", "090715", 1, 1.0, 2.0, 3.0)
        assert msg.to_dict()["sentence_type"] == "PNORC2"


class TestPNORC3:
    def test_pnorc3_parsing_amplitude(self):
        sentence = "$PNORC3,102115,090715,1,0.123,-0.456,0.012,145,152,148,150*XX"
        msg = PNORC3.from_nmea(sentence)
        assert msg.amp1 == 145
        assert msg.amp4 == 150

    def test_pnorc3_validation_errors(self):
        # Invalid amplitude
        with pytest.raises(ValueError, match="Amplitude 1 out of range"):
            PNORC3.from_nmea("$PNORC3,102115,090715,1,0.123,-0.456,0.012,256,152,148,150")

    def test_pnorc3_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 11 fields"):
            PNORC3.from_nmea("$PNORC3,1,2,3,4,5,6,7,8,9*00")

    def test_pnorc3_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORC3.from_nmea("$NOTRC3,1,2,3,4,5,6,7,8,9,10*00")

    def test_pnorc3_to_dict(self):
        msg = PNORC3("102115", "090715", 1, 1.0, 2.0, 3.0, 100, 101, 102, 103)
        assert msg.to_dict()["sentence_type"] == "PNORC3"


class TestPNORC4:
    def test_pnorc4_parsing_complete(self):
        sentence = "$PNORC4,102115,090715,1,0.123,-0.456,0.012,95,92,88,145,152,148,150*XX"
        msg = PNORC4.from_nmea(sentence)
        assert msg.corr1 == 95
        assert msg.amp1 == 145
        assert msg.amp4 == 150

    def test_pnorc4_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 14 fields"):
            PNORC4.from_nmea("$PNORC4,1,2,3,4,5,6,7,8,9,10,11,12*00")

    def test_pnorc4_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORC4.from_nmea("$NOTRC4,1,2,3,4,5,6,7,8,9,10,11,12,13*00")

    def test_pnorc4_to_dict(self):
        msg = PNORC4("102115", "090715", 1, 1.0, 2.0, 3.0, 90, 91, 92, 100, 101, 102, 103)
        assert msg.to_dict()["sentence_type"] == "PNORC4"
