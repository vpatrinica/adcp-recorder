"""Tests for shared enumerations."""

import pytest
from adcp_recorder.core.enums import InstrumentType, CoordinateSystem


class TestInstrumentType:
    """Tests for InstrumentType enumeration."""

    def test_valid_instrument_types(self):
        """Test that all instrument types have correct values."""
        assert InstrumentType.AQUADOPP == 0
        assert InstrumentType.AQUADOPP_PROFILER == 2
        assert InstrumentType.SIGNATURE == 4

    def test_from_code_valid(self):
        """Test creating instrument type from valid codes."""
        assert InstrumentType.from_code(0) == InstrumentType.AQUADOPP
        assert InstrumentType.from_code(2) == InstrumentType.AQUADOPP_PROFILER
        assert InstrumentType.from_code(4) == InstrumentType.SIGNATURE

    def test_from_code_invalid_raises_error(self):
        """Test that invalid code raises ValueError."""
        with pytest.raises(ValueError, match="Invalid instrument type"):
            InstrumentType.from_code(99)

        with pytest.raises(ValueError, match="Invalid instrument type"):
            InstrumentType.from_code(1)

    def test_signature_beam_constraint(self):
        """Test that Signature has 4-beam constraint."""
        signature = InstrumentType.SIGNATURE
        assert signature.valid_beam_counts == (4,)

    def test_aquadopp_beam_constraint(self):
        """Test that Aquadopp allows 1-3 beams."""
        aquadopp = InstrumentType.AQUADOPP
        assert aquadopp.valid_beam_counts == (1, 2, 3)

        profiler = InstrumentType.AQUADOPP_PROFILER
        assert profiler.valid_beam_counts == (1, 2, 3)

    def test_instrument_names(self):
        """Test that instrument types have correct names."""
        assert InstrumentType.AQUADOPP.name == "AQUADOPP"
        assert InstrumentType.AQUADOPP_PROFILER.name == "AQUADOPP_PROFILER"
        assert InstrumentType.SIGNATURE.name == "SIGNATURE"


class TestCoordinateSystem:
    """Tests for CoordinateSystem enumeration."""

    def test_valid_coordinate_systems(self):
        """Test that all coordinate systems have correct values."""
        assert CoordinateSystem.ENU.value == "ENU"
        assert CoordinateSystem.XYZ.value == "XYZ"
        assert CoordinateSystem.BEAM.value == "BEAM"

    def test_from_code_numeric(self):
        """Test creating coordinate system from numeric codes."""
        assert CoordinateSystem.from_code(0) == CoordinateSystem.ENU
        assert CoordinateSystem.from_code(1) == CoordinateSystem.XYZ
        assert CoordinateSystem.from_code(2) == CoordinateSystem.BEAM

    def test_from_code_string(self):
        """Test creating coordinate system from string codes."""
        assert CoordinateSystem.from_code("ENU") == CoordinateSystem.ENU
        assert CoordinateSystem.from_code("XYZ") == CoordinateSystem.XYZ
        assert CoordinateSystem.from_code("BEAM") == CoordinateSystem.BEAM

    def test_from_code_lowercase_string(self):
        """Test that lowercase strings are handled."""
        assert CoordinateSystem.from_code("enu") == CoordinateSystem.ENU
        assert CoordinateSystem.from_code("xyz") == CoordinateSystem.XYZ
        assert CoordinateSystem.from_code("beam") == CoordinateSystem.BEAM

    def test_from_code_invalid_numeric_raises(self):
        """Test that invalid numeric code raises ValueError."""
        with pytest.raises(ValueError, match="Invalid coordinate system"):
            CoordinateSystem.from_code(99)

        with pytest.raises(ValueError, match="Invalid coordinate system"):
            CoordinateSystem.from_code(3)

    def test_from_code_invalid_string_raises(self):
        """Test that invalid string code raises ValueError."""
        with pytest.raises(ValueError, match="Invalid coordinate system"):
            CoordinateSystem.from_code("INVALID")

        with pytest.raises(ValueError, match="Invalid coordinate system"):
            CoordinateSystem.from_code("ABC")

    def test_to_numeric_code(self):
        """Test conversion from enum to numeric code."""
        assert CoordinateSystem.ENU.to_numeric_code() == 0
        assert CoordinateSystem.XYZ.to_numeric_code() == 1
        assert CoordinateSystem.BEAM.to_numeric_code() == 2

    def test_round_trip_conversion(self):
        """Test round-trip conversion between code and enum."""
        for code in [0, 1, 2]:
            coord_sys = CoordinateSystem.from_code(code)
            assert coord_sys.to_numeric_code() == code

        for coord_sys in [
            CoordinateSystem.ENU,
            CoordinateSystem.XYZ,
            CoordinateSystem.BEAM,
        ]:
            code = coord_sys.to_numeric_code()
            assert CoordinateSystem.from_code(code) == coord_sys
