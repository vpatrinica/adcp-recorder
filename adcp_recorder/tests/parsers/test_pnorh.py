"""Unit tests for PNORH family parsers."""

from adcp_recorder.parsers.pnorh import PNORH3, PNORH4


class TestPNORH3:
    def test_pnorh3_parsing_tagged(self):
        # 4 tags: DATE, TIME, EC, SC
        sentence = "$PNORH3,DATE=141112,TIME=081946,EC=0,SC=2A4C0000*5F"
        msg = PNORH3.from_nmea(sentence)
        assert msg.date == "141112"
        assert msg.time == "081946"
        assert msg.error_code == 0
        assert msg.status_code == "2A4C0000"

    def test_pnorh3_to_dict(self):
        msg = PNORH3("141112", "081946", 0, "2A4C0000")
        d = msg.to_dict()
        assert d["sentence_type"] == "PNORH3"
        assert d["date"] == "141112"
        assert d["status_code"] == "2A4C0000"


class TestPNORH4:
    def test_pnorh4_parsing_positional(self):
        # 5 fields: prefix, date, time, ec, sc
        sentence = "$PNORH4,141112,083149,0,2A4C0000*4A"
        msg = PNORH4.from_nmea(sentence)
        assert msg.date == "141112"
        assert msg.time == "083149"
        assert msg.error_code == 0
        assert msg.status_code == "2A4C0000"

    def test_pnorh4_to_dict(self):
        msg = PNORH4("141112", "083149", 0, "2A4C0000")
        d = msg.to_dict()
        assert d["sentence_type"] == "PNORH4"
        assert d["time"] == "083149"
