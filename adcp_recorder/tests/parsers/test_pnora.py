"""Unit tests for PNORA parser.
"""

import pytest
from adcp_recorder.parsers.pnora import PNORA


class TestPNORA:
    def test_pnora_parsing_basic(self):
        sentence = "$PNORA,102115,090715,1,15.50,95*XX"
        msg = PNORA.from_nmea(sentence)
        assert msg.date == "102115"
        assert msg.method == 1
        assert msg.distance == 15.50
        assert msg.quality == 95

    def test_pnora_validation_errors(self):
        # Invalid method
        with pytest.raises(ValueError, match="Altitude method out of range"):
            PNORA.from_nmea("$PNORA,102115,090715,3,15.50,95")
        
        # Invalid distance
        with pytest.raises(ValueError, match="Distance out of range"):
            PNORA.from_nmea("$PNORA,102115,090715,1,1001.0,95")
        
        # Invalid quality
        with pytest.raises(ValueError, match="Quality out of range"):
            PNORA.from_nmea("$PNORA,102115,090715,1,15.50,101")
