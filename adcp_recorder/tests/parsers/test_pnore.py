"""Unit tests for PNORE parser."""
import pytest
from adcp_recorder.parsers.pnore import PNORE

class TestPNORE:
    def test_pnore_parsing(self):
        sentence = "$PNORE,102115,090715,1,145,152,148,150*XX"
        msg = PNORE.from_nmea(sentence)
        assert msg.cell_index == 1
        assert msg.echo1 == 145
        assert msg.echo4 == 150

    def test_pnore_invalid_field_count(self):
        with pytest.raises(ValueError, match="Expected 8 fields"):
            PNORE.from_nmea("$PNORE,1,2,3,4,5,6*00")

    def test_pnore_invalid_prefix(self):
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORE.from_nmea("$NOTRE,1,2,3,4,5,6,7*00")

    def test_pnore_to_dict(self):
        msg = PNORE("102115", "090715", 1, 100, 101, 102, 103)
        assert msg.to_dict()["sentence_type"] == "PNORE"
