"""Tests for PNORWD wave directional spectra parser."""

import pytest
from adcp_recorder.parsers.pnorwd import PNORWD


class TestPNORWDParser:
    """Test suite for PNORWD parser."""

    def test_parse_main_direction(self):
        """Test parsing main direction (MD) spectrum."""
        # Using 10 direction values for clarity
        sentence = (
            "$PNORWD,MD,120720,093150,1,0.02,0.01,10,"
            "326.5,335.8,11.6,8.2,147.6,107.1,74.8,55.4,55.0,50.8*00"
        )
        
        pnorwd = PNORWD.from_nmea(sentence)
        
        assert pnorwd.direction_type == "MD"
        assert pnorwd.date == "120720"
        assert pnorwd.time == "093150"
        assert pnorwd.spectrum_basis == 1  # Velocity-based
        assert pnorwd.start_frequency == 0.02
        assert pnorwd.step_frequency == 0.01
        assert pnorwd.num_frequencies == 10
        assert len(pnorwd.values) == 10
        assert pnorwd.checksum == "00"
        
        # Verify direction values
        assert pnorwd.values[0] == pytest.approx(326.5)
        assert pnorwd.values[1] == pytest.approx(335.8)
        assert pnorwd.values[9] == pytest.approx(50.8)

    def test_parse_directional_spread(self):
        """Test parsing directional spread (DS) spectrum."""
        sentence = (
            "$PNORWD,DS,120720,093150,1,0.02,0.01,5,"
            "45.2,38.7,52.1,41.3,39.8*00"
        )
        
        pnorwd = PNORWD.from_nmea(sentence)
        
        assert pnorwd.direction_type == "DS"
        assert len(pnorwd.values) == 5

    def test_both_direction_types(self):
        """Test both MD and DS direction types."""
        for dir_type in ["MD", "DS"]:
            sentence = f"$PNORWD,{dir_type},120720,093150,1,0.05,0.02,2,45.0,90.0*00"
            pnorwd = PNORWD.from_nmea(sentence)
            assert pnorwd.direction_type == dir_type

    def test_all_spectrum_basis_types(self):
        """Test all spectrum basis types: 0=Pressure, 1=Velocity, 3=AST."""
        for basis in [0, 1, 3]:
            sentence = f"$PNORWD,MD,120720,093150,{basis},0.05,0.02,2,45.0,90.0*00"
            pnorwd = PNORWD.from_nmea(sentence)
            assert pnorwd.spectrum_basis == basis

    def test_invalid_direction_type(self):
        """Test that invalid direction types are rejected."""
        sentence = "$PNORWD,XX,120720,093150,1,0.05,0.02,2,45.0,90.0*00"
        with pytest.raises(ValueError, match="Invalid direction type"):
            PNORWD.from_nmea(sentence)

    def test_invalid_spectrum_basis(self):
        """Test that invalid spectrum basis values are rejected."""
        sentence = "$PNORWD,MD,120720,093150,2,0.05,0.02,2,45.0,90.0*00"
        with pytest.raises(ValueError, match="Invalid spectrum basis"):
            PNORWD.from_nmea(sentence)

    def test_value_count_mismatch(self):
        """Test that value count must match num_frequencies."""
        # Says 5 frequencies but only provides 3
        sentence = "$PNORWD,MD,120720,093150,1,0.05,0.02,5,45.0,90.0,135.0*00"
        with pytest.raises(ValueError, match="Missing value"):
            PNORWD.from_nmea(sentence)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        sentence = "$PNORWD,DS,120720,093150,3,0.03,0.01,4,30.5,45.2,60.8,75.1*00"
        pnorwd = PNORWD.from_nmea(sentence)
        data = pnorwd.to_dict()
        
        assert data["sentence_type"] == "PNORWD"
        assert data["direction_type"] == "DS"
        assert data["date"] == "120720"
        assert data["time"] == "093150"
        assert data["spectrum_basis"] == 3
        assert data["start_frequency"] == 0.03
        assert data["step_frequency"] == 0.01
        assert data["num_frequencies"] == 4
        assert data["values"] == pytest.approx([30.5, 45.2, 60.8, 75.1])
        assert data["checksum"] == "00"

    def test_invalid_data_markers(self):
        """Test that invalid data markers (-9.0000) are handled."""
        sentence = "$PNORWD,MD,120720,093150,1,0.05,0.02,5,45.0,-9.0000,-9.0000,90.0,135.0*00"
        pnorwd = PNORWD.from_nmea(sentence)
        # Verify invalid data markers
        assert pnorwd.values[1] is None
        assert pnorwd.values[2] is None

    def test_large_value_array(self):
        """Test with maximum allowed frequencies (999)."""
        # Generate 999 direction values
        values = ",".join(["180.0"] * 999)
        sentence = f"$PNORWD,MD,120720,093150,1,0.01,0.01,999,{values}*00"
        pnorwd = PNORWD.from_nmea(sentence)
        assert len(pnorwd.values) == 999
        assert all(v == 180.0 for v in pnorwd.values)

    def test_invalid_prefix(self):
        """Test that wrong prefix is rejected."""
        sentence = "$PNORE,MD,120720,093150,1,0.05,0.02,2,45.0,90.0*00"
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORWD.from_nmea(sentence)

    def test_minimum_fields_check(self):
        """Test that sentences with too few fields are rejected."""
        sentence = "$PNORWD,MD,120720,093150*00"
        with pytest.raises(ValueError, match="Expected at least 9 fields"):
            PNORWD.from_nmea(sentence)

    def test_frequency_range_validation(self):
        """Test frequency parameter validation."""
        # Start frequency too high
        sentence = "$PNORWD,MD,120720,093150,1,15.0,0.02,2,45.0,90.0*00"
        with pytest.raises(ValueError, match="Start frequency"):
            PNORWD.from_nmea(sentence)
        
        # Step frequency negative
        sentence = "$PNORWD,MD,120720,093150,1,0.05,-0.02,2,45.0,90.0*00"
        with pytest.raises(ValueError, match="Step frequency"):
            PNORWD.from_nmea(sentence)
