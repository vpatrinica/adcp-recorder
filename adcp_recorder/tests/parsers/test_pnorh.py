"""Unit tests for PNORH family parsers.
"""

import pytest
from adcp_recorder.parsers.pnorh import PNORH3, PNORH4


class TestPNORH3:
    def test_pnorh3_parsing_basic(self):
        sentence = "$PNORH3,102115,090715,20,1,50*XX"
        msg = PNORH3.from_nmea(sentence)
        assert msg.date == "102115"
        assert msg.num_cells == 20
        assert msg.first_cell == 1
        assert msg.ping_count == 50

    def test_pnorh3_validation_errors(self):
        # Invalid cell range
        with pytest.raises(ValueError, match="First cell out of range"):
            PNORH3.from_nmea("$PNORH3,102115,090715,20,21,50")
        
        # Invalid ping count
        with pytest.raises(ValueError, match="Ping count must be at least 1"):
            PNORH3.from_nmea("$PNORH3,102115,090715,20,1,0")


class TestPNORH4:
    def test_pnorh4_parsing_extended(self):
        sentence = "$PNORH4,102115,090715,20,1,50,ENU,60.0*XX"
        msg = PNORH4.from_nmea(sentence)
        assert msg.coordinate_system == "ENU"
        assert msg.profile_interval == 60.0

    def test_pnorh4_validation_errors(self):
        # Invalid coordinate system
        with pytest.raises(ValueError, match="Invalid coordinate system for header: ABC"):
            PNORH4.from_nmea("$PNORH4,102115,090715,20,1,50,ABC,60.0")
        
        # Invalid profile interval
        with pytest.raises(ValueError, match="Profile interval must be positive"):
            PNORH4.from_nmea("$PNORH4,102115,090715,20,1,50,ENU,0.0")
