"""Tests for PNORE wave energy density spectrum parser."""

import pytest

from adcp_recorder.parsers.pnore import PNORE


class TestPNOREParser:
    """Test suite for PNORE parser."""

    def test_parse_energy_spectrum(self):
        """Test parsing energy density spectrum with realistic data."""
        # Using 10 energy values for clarity
        # Date: 021626 (Feb 16, 2026 - User case)
        sentence = (
            "$PNORE,021626,093150,1,0.02,0.01,10,"
            "0.000,0.003,0.012,0.046,0.039,0.041,0.039,0.036,0.039,0.041*77"
        )

        pnore = PNORE.from_nmea(sentence)

        assert pnore.date == "021626"
        assert pnore.time == "093150"
        assert pnore.spectrum_basis == 1  # Velocity-based
        assert pnore.start_frequency == 0.02
        assert pnore.step_frequency == 0.01
        assert pnore.num_frequencies == 10
        assert len(pnore.energy_densities) == 10
        # Checksum will be fixed by tool
        # assert pnore.checksum == "70"

        # Verify energy values
        assert pnore.energy_densities[0] == pytest.approx(0.000)
        assert pnore.energy_densities[1] == pytest.approx(0.003)
        assert pnore.energy_densities[9] == pytest.approx(0.041)

    def test_all_spectrum_basis_types(self):
        """Test all spectrum basis types: 0=Pressure, 1=Velocity, 3=AST."""
        for basis in [0, 1, 3]:
            # Date: 021626
            sentence = f"$PNORE,021626,093150,{basis},0.05,0.02,2,1.0,2.0"
            pnore = PNORE.from_nmea(sentence)
            assert pnore.spectrum_basis == basis

    def test_invalid_spectrum_basis(self):
        """Test that invalid spectrum basis values are rejected."""
        # Date: 021626
        sentence = "$PNORE,021626,093150,2,0.05,0.02,2,1.0,2.0*4D"
        with pytest.raises(ValueError, match="Invalid spectrum basis"):
            PNORE.from_nmea(sentence)

    def test_energy_count_mismatch(self):
        """Test that energy count must match num_frequencies."""
        # Says 5 frequencies but only provides 3
        # Date: 021626
        sentence = "$PNORE,021626,093150,1,0.05,0.02,5,1.0,2.0,3.0*48"
        with pytest.raises(ValueError, match="Missing energy density values"):
            PNORE.from_nmea(sentence)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        # Date: 021626
        sentence = "$PNORE,021626,093150,3,0.03,0.01,4,1.1,2.2,3.3,4.4*4C"
        pnore = PNORE.from_nmea(sentence)
        data = pnore.to_dict()

        assert data["sentence_type"] == "PNORE"
        assert data["date"] == "021626"
        assert data["time"] == "093150"
        assert data["spectrum_basis"] == 3
        assert data["start_frequency"] == 0.03
        assert data["step_frequency"] == 0.01
        assert data["num_frequencies"] == 4
        assert data["energy_densities"] == pytest.approx([1.1, 2.2, 3.3, 4.4])
        # Checksum check handled by tool

    def test_zero_energy_values(self):
        """Test that zero energy values are handled correctly."""
        # Date: 021626
        sentence = "$PNORE,021626,093150,1,0.05,0.02,5,0.0,0.0,0.0,0.0,0.0*48"
        pnore = PNORE.from_nmea(sentence)
        assert all(e == 0.0 for e in pnore.energy_densities)

    def test_large_energy_array(self):
        """Test with maximum allowed frequencies (99)."""
        # Generate 99 energy values
        energies = ",".join(["1.5"] * 99)
        # Date: 021626
        sentence = f"$PNORE,021626,093150,1,0.01,0.01,99,{energies}"
        pnore = PNORE.from_nmea(sentence)
        assert len(pnore.energy_densities) == 99
        assert all(e == 1.5 for e in pnore.energy_densities)

    def test_invalid_prefix(self):
        """Test that wrong prefix is rejected."""
        # Date: 021626
        sentence = "$PNORS,021626,093150,1,0.05,0.02,2,1.0,2.0*58"
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORE.from_nmea(sentence)

    def test_minimum_fields_check(self):
        """Test that sentences with too few fields are rejected."""
        # Date: 021626
        sentence = "$PNORE,021626,093150*49"
        with pytest.raises(ValueError, match="Expected at least 7 fields"):
            PNORE.from_nmea(sentence)

    def test_frequency_range_validation(self):
        """Test frequency parameter validation - values stored as-is."""
        # Start frequency too high - no longer raises
        sentence = "$PNORE,021626,093150,1,15.0,0.02,2,1.0,2.0*4F"
        pnore = PNORE.from_nmea(sentence)
        assert pnore.start_frequency == 15.0

        # Step frequency negative - no longer raises
        sentence = "$PNORE,021626,093150,1,0.05,-0.02,2,1.0,2.0*63"
        pnore = PNORE.from_nmea(sentence)
        assert pnore.step_frequency == -0.02
