"""Unit tests for PNORH family parsers.
"""

import pytest
from adcp_recorder.parsers.pnorh import PNORH3, PNORH4


class TestPNORH3:
    def test_pnorh3_parsing_tagged(self):
        # 15 tags
        sentence = "$PNORH3,ID=MyInst,TYPE=4,SN=12345,FW=1.2.3,DATE=250101,TIME=120000,MODE=1,LEN=1024,INT=3600,SAMP=2.0,NBEAM=4,NCELL=20,BLANK=0.5,CELL=1.0,COORD=ENU*XX"
        msg = PNORH3.from_nmea(sentence)
        assert msg.instrument_id == "MyInst"
        assert msg.instrument_type == 4
        assert msg.date == "250101"
        assert msg.burst_length == 1024
        assert msg.num_beams == 4
        assert msg.coordinate_system == "ENU"

    def test_pnorh3_to_dict(self):
        msg = PNORH3("ID", 4, "SN", "FW", "250101", "120000", 1, 1024, 3600, 2.0, 4, 20, 0.5, 1.0, "ENU")
        d = msg.to_dict()
        assert d["sentence_type"] == "PNORH3"
        assert d["blanking"] == 0.5
        assert d["coordinate_system"] == "ENU"


class TestPNORH4:
    def test_pnorh4_parsing_positional(self):
        # 16 fields: prefix, ID, Type, SN, FW, YYMMDD, HHMMSS, Mode, Len, Int, Samp, NBeam, NCell, Blank, Cell, Coord
        sentence = "$PNORH4,MyInst,4,12345,1.2.3,250101,120000,1,1024,3600,2.0,4,20,0.5,1.0,ENU*XX"
        msg = PNORH4.from_nmea(sentence)
        assert msg.instrument_id == "MyInst"
        assert msg.instrument_type == 4
        assert msg.sample_rate == 2.0
        assert msg.num_cells == 20
        assert msg.coordinate_system == "ENU"

    def test_pnorh4_to_dict(self):
        msg = PNORH4("ID", 4, "SN", "FW", "250101", "120000", 1, 1024, 3600, 2.0, 4, 20, 0.5, 1.0, "ENU")
        d = msg.to_dict()
        assert d["sentence_type"] == "PNORH4"
        assert d["cell_size"] == 1.0
