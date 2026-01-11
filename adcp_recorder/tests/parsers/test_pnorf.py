"""Tests for PNORF Fourier coefficient spectra parser."""

import pytest
from adcp_recorder.parsers.pnorf import PNORF


class TestPNORFParser:
    """Test suite for PNORF parser."""

    def test_parse_real_spec_example(self):
        """Test parsing based on TELEMETRY_SPEC.md format with realistic data."""
        # Using a smaller example for clarity - 10 coefficients with mix of valid and invalid
        sentence = (
            "$PNORF,A1,120720,093150,1,0.02,0.01,10,"
            "0.0348,0.0958,0.1372,0.1049,-0.0215,-0.0143,0.0358,0.0903,"
            "-9.0000,-9.0000*0D"
        )
        
        pnorf = PNORF.from_nmea(sentence)
        
        assert pnorf.coefficient_flag == "A1"
        assert pnorf.date == "120720"
        assert pnorf.time == "093150"
        assert pnorf.spectrum_basis == 1  # Velocity-based
        assert pnorf.start_frequency == 0.02
        assert pnorf.step_frequency == 0.01
        assert pnorf.num_frequencies == 10
        assert len(pnorf.coefficients) == 10
        assert pnorf.checksum == "0D"
        
        # Verify first few coefficients
        assert pnorf.coefficients[0] == pytest.approx(0.0348)
        assert pnorf.coefficients[1] == pytest.approx(0.0958)
        assert pnorf.coefficients[2] == pytest.approx(0.1372)
        
        # Verify invalid data markers
        assert pnorf.coefficients[8] == pytest.approx(-9.0000)
        assert pnorf.coefficients[9] == pytest.approx(-9.0000)

    def test_all_coefficient_types(self):
        """Test all four coefficient types: A1, B1, A2, B2."""
        for coeff_type in ["A1", "B1", "A2", "B2"]:
            sentence = f"$PNORF,{coeff_type},120720,093150,0,0.05,0.02,3,1.234,2.345,3.456*00"
            pnorf = PNORF.from_nmea(sentence)
            assert pnorf.coefficient_flag == coeff_type

    def test_all_spectrum_basis_types(self):
        """Test all spectrum basis types: 0=Pressure, 1=Velocity, 3=AST."""
        for basis in [0, 1, 3]:
            sentence = f"$PNORF,A1,120720,093150,{basis},0.05,0.02,2,1.0,2.0*00"
            pnorf = PNORF.from_nmea(sentence)
            assert pnorf.spectrum_basis == basis

    def test_invalid_coefficient_flag(self):
        """Test that invalid coefficient flags are rejected."""
        sentence = "$PNORF,XX,120720,093150,1,0.05,0.02,2,1.0,2.0*00"
        with pytest.raises(ValueError, match="Invalid coefficient flag"):
            PNORF.from_nmea(sentence)

    def test_invalid_spectrum_basis(self):
        """Test that invalid spectrum basis values are rejected."""
        sentence = "$PNORF,A1,120720,093150,2,0.05,0.02,2,1.0,2.0*00"
        with pytest.raises(ValueError, match="Invalid spectrum basis"):
            PNORF.from_nmea(sentence)

    def test_coefficient_count_mismatch(self):
        """Test that coefficient count must match num_frequencies."""
        # Says 5 frequencies but only provides 3
        sentence = "$PNORF,A1,120720,093150,1,0.05,0.02,5,1.0,2.0,3.0*00"
        with pytest.raises(ValueError, match="Missing coefficient"):
            PNORF.from_nmea(sentence)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        sentence = "$PNORF,B1,120720,093150,3,0.03,0.01,4,1.1,2.2,3.3,4.4*00"
        pnorf = PNORF.from_nmea(sentence)
        data = pnorf.to_dict()
        
        assert data["sentence_type"] == "PNORF"
        assert data["coefficient_flag"] == "B1"
        assert data["date"] == "120720"
        assert data["time"] == "093150"
        assert data["spectrum_basis"] == 3
        assert data["start_frequency"] == 0.03
        assert data["step_frequency"] == 0.01
        assert data["num_frequencies"] == 4
        assert data["coefficients"] == [1.1, 2.2, 3.3, 4.4]
        assert data["checksum"] == "00"

    def test_negative_coefficients(self):
        """Test that negative coefficients are handled correctly."""
        sentence = "$PNORF,A2,120720,093150,1,0.05,0.02,5,-1.5,-2.5,-3.5,-4.5,-5.5*00"
        pnorf = PNORF.from_nmea(sentence)
        assert pnorf.coefficients == pytest.approx([-1.5, -2.5, -3.5, -4.5, -5.5])

    def test_large_coefficient_array(self):
        """Test with maximum allowed frequencies (999)."""
        # Generate 999 coefficients
        coeffs = ",".join(["1.0"] * 999)
        sentence = f"$PNORF,A1,120720,093150,1,0.01,0.01,999,{coeffs}*00"
        pnorf = PNORF.from_nmea(sentence)
        assert len(pnorf.coefficients) == 999
        assert all(c == 1.0 for c in pnorf.coefficients)

    def test_invalid_prefix(self):
        """Test that wrong prefix is rejected."""
        sentence = "$PNORS,A1,120720,093150,1,0.05,0.02,2,1.0,2.0*00"
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORF.from_nmea(sentence)

    def test_minimum_fields_check(self):
        """Test that sentences with too few fields are rejected."""
        sentence = "$PNORF,A1,120720,093150*00"
        with pytest.raises(ValueError, match="Expected at least 9 fields"):
            PNORF.from_nmea(sentence)

    def test_frequency_range_validation(self):
        """Test frequency parameter validation."""
        # Start frequency too high
        sentence = "$PNORF,A1,120720,093150,1,15.0,0.02,2,1.0,2.0*00"
        with pytest.raises(ValueError, match="Start frequency"):
            PNORF.from_nmea(sentence)
        
        # Step frequency negative
        sentence = "$PNORF,A1,120720,093150,1,0.05,-0.02,2,1.0,2.0*00"
        with pytest.raises(ValueError, match="Step frequency"):
            PNORF.from_nmea(sentence)
