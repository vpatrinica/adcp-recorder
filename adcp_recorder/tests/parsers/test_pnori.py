"""Tests for PNORI family parsers."""

from adcp_recorder.core.enums import CoordinateSystem, InstrumentType
from adcp_recorder.parsers import PNORI, PNORI1, PNORI2, PNORITag
import pytest


class TestPNORI:
    """Test PNORI parser (positional, numeric coords)."""

    def test_parse_valid_sentence(self):
        """Test parsing a valid PNORI sentence."""
        sentence = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E"
        config = PNORI.from_nmea(sentence)

        assert config.instrument_type == InstrumentType.SIGNATURE
        assert config.head_id == "Signature1000900001"
        assert config.beam_count == 4
        assert config.cell_count == 20
        assert config.blanking_distance == 0.20
        assert config.cell_size == 1.00
        assert config.coordinate_system == CoordinateSystem.ENU
        assert config.checksum == "2E"

    def test_parse_without_checksum(self):
        """Test parsing sentence without checksum."""
        sentence = "$PNORI,4,Test123,4,20,0.20,1.00,0"
        config = PNORI.from_nmea(sentence)

        assert config.head_id == "Test123"
        assert config.checksum is None

    def test_round_trip_serialization(self):
        """Test parsing and serialization round-trip."""
        original = "$PNORI,4,Test123,4,20,0.20,1.00,0*2E"
        config = PNORI.from_nmea(original)
        reserialized = config.to_nmea()

        config2 = PNORI.from_nmea(reserialized)
        assert config.instrument_type == config2.instrument_type
        assert config.head_id == config2.head_id
        assert config.beam_count == config2.beam_count

    def test_invalid_prefix_raises_error(self):
        """Test that invalid prefix raises ValueError."""
        sentence = "$PNORS,4,Test,4,20,0.20,1.00,0*00"
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORI.from_nmea(sentence)

    def test_wrong_field_count_raises_error(self):
        """Test that wrong number of fields raises ValueError."""
        sentence = "$PNORI,4,Test,4,20,0.20*00"  # Missing fields
        with pytest.raises(ValueError, match="Expected 8 fields"):
            PNORI.from_nmea(sentence)

    def test_invalid_instrument_type_raises_error(self):
        """Test that invalid instrument type raises ValueError."""
        sentence = "$PNORI,99,Test,4,20,0.20,1.00,0*00"
        with pytest.raises(ValueError, match="Invalid instrument type"):
            PNORI.from_nmea(sentence)

    def test_invalid_coordinate_system_raises_error(self):
        """Test that invalid coordinate system raises ValueError."""
        sentence = "$PNORI,4,Test,4,20,0.20,1.00,99*00"
        with pytest.raises(ValueError, match="Invalid coordinate system"):
            PNORI.from_nmea(sentence)

    def test_head_id_too_long_raises_error(self):
        """Test that head ID longer than 30 chars raises ValueError."""
        sentence = f"$PNORI,4,{'A' * 31},4,20,0.20,1.00,0*00"
        with pytest.raises(ValueError, match="Head ID too long"):
            PNORI.from_nmea(sentence)

    def test_head_id_empty_raises_error(self):
        """Test that empty head ID raises ValueError."""
        sentence = "$PNORI,4,,4,20,0.20,1.00,0*00"
        with pytest.raises(ValueError, match="Head ID cannot be empty"):
            PNORI.from_nmea(sentence)

    def test_head_id_invalid_chars_raises_error(self):
        """Test that head ID with invalid characters raises ValueError."""
        sentence = "$PNORI,4,Test@#$,4,20,0.20,1.00,0*00"
        with pytest.raises(ValueError, match="invalid characters"):
            PNORI.from_nmea(sentence)

    def test_signature_requires_four_beams(self):
        """Test that Signature instruments must have 4 beams."""
        sentence = "$PNORI,4,Test,3,20,0.20,1.00,0*00"
        with pytest.raises(ValueError, match="SIGNATURE requires beam count"):
            PNORI.from_nmea(sentence)

    def test_aquadopp_beam_count_valid(self):
        """Test that Aquadopp can have 1-3 beams."""
        for beam_count in [1, 2, 3]:
            sentence = f"$PNORI,0,Test,{beam_count},20,0.20,1.00,0*00"
            config = PNORI.from_nmea(sentence)
            assert config.beam_count == beam_count

    def test_aquadopp_invalid_beam_count(self):
        """Test that Aquadopp cannot have 4 beams."""
        sentence = "$PNORI,0,Test,4,20,0.20,1.00,0*00"
        with pytest.raises(ValueError, match="AQUADOPP requires beam count"):
            PNORI.from_nmea(sentence)

    def test_cell_count_min_max(self):
        """Test cell count validation."""
        # Too low
        sentence = "$PNORI,4,Test,4,0,0.20,1.00,0*00"
        with pytest.raises(ValueError, match="Cell count must be 1-1000"):
            PNORI.from_nmea(sentence)

        # Too high
        sentence = "$PNORI,4,Test,4,1001,0.20,1.00,0*00"
        with pytest.raises(ValueError, match="Cell count must be 1-1000"):
            PNORI.from_nmea(sentence)

    def test_blanking_distance_validation(self):
        """Test blanking distance validation."""
        # Negative
        sentence = "$PNORI,4,Test,4,20,-0.20,1.00,0*00"
        with pytest.raises(ValueError, match="Blanking distance must be positive"):
            PNORI.from_nmea(sentence)

        # Too large
        sentence = "$PNORI,4,Test,4,20,101.00,1.00,0*00"
        with pytest.raises(ValueError, match="Blanking distance too large"):
            PNORI.from_nmea(sentence)

    def test_cell_size_validation(self):
        """Test cell size validation."""
        # Negative
        sentence = "$PNORI,4,Test,4,20,0.20,-1.00,0*00"
        with pytest.raises(ValueError, match="Cell size must be positive"):
            PNORI.from_nmea(sentence)

        # Too large
        sentence = "$PNORI,4,Test,4,20,0.20,101.00,0*00"
        with pytest.raises(ValueError, match="Cell size too large"):
            PNORI.from_nmea(sentence)

    def test_to_dict_method(self):
        """Test conversion to dictionary."""
        sentence = "$PNORI,4,Test123,4,20,0.20,1.00,0*2E"
        config = PNORI.from_nmea(sentence)
        data_dict = config.to_dict()

        assert data_dict["sentence_type"] == "PNORI"
        assert data_dict["instrument_type_name"] == "SIGNATURE"
        assert data_dict["instrument_type_code"] == 4
        assert data_dict["head_id"] == "Test123"
        assert data_dict["beam_count"] == 4
        assert data_dict["cell_count"] == 20
        assert data_dict["blanking_distance"] == 0.20
        assert data_dict["cell_size"] == 1.00
        assert data_dict["coord_system_name"] == "ENU"
        assert data_dict["coord_system_code"] == 0
        assert data_dict["checksum"] == "2E"

    def test_to_nmea_without_checksum(self):
        """Test serialization without checksum."""
        sentence = "$PNORI,4,Test,4,20,0.20,1.00,0"
        config = PNORI.from_nmea(sentence)
        nmea = config.to_nmea(include_checksum=False)

        assert "*" not in nmea
        assert nmea.startswith("$PNORI,")


class TestPNORI1:
    """Test PNORI1 parser (positional, string coords)."""

    def test_parse_valid_sentence(self):
        """Test parsing valid PNORI1 sentence."""
        sentence = "$PNORI1,4,123456,4,30,1.00,5.00,BEAM*5B"
        config = PNORI1.from_nmea(sentence)

        assert config.instrument_type == InstrumentType.SIGNATURE
        assert config.head_id == "123456"
        assert config.coordinate_system == CoordinateSystem.BEAM

    def test_parse_all_coordinate_systems(self):
        """Test parsing all coordinate system variants."""
        for coord_sys in ["ENU", "XYZ", "BEAM"]:
            sentence = f"$PNORI1,4,Test,4,20,0.20,1.00,{coord_sys}*00"
            config = PNORI1.from_nmea(sentence)
            assert config.coordinate_system.value == coord_sys

    def test_invalid_coordinate_string_raises_error(self):
        """Test that invalid coordinate string raises ValueError."""
        sentence = "$PNORI1,4,Test,4,20,0.20,1.00,INVALID*00"
        with pytest.raises(ValueError, match="Invalid coordinate system"):
            PNORI1.from_nmea(sentence)

    def test_round_trip_serialization(self):
        """Test parsing and serialization round-trip."""
        original = "$PNORI1,4,Test,4,20,0.20,1.00,XYZ*00"
        config = PNORI1.from_nmea(original)
        reserialized = config.to_nmea()

        config2 = PNORI1.from_nmea(reserialized)
        assert config.coordinate_system == config2.coordinate_system

    def test_all_pnori_validation_rules_apply(self):
        """Test that PNORI validation rules apply to PNORI1."""
        # Signature must have 4 beams
        sentence = "$PNORI1,4,Test,3,20,0.20,1.00,ENU*00"
        with pytest.raises(ValueError):
            PNORI1.from_nmea(sentence)

        # Cell count range
        sentence = "$PNORI1,4,Test,4,1001,0.20,1.00,ENU*00"
        with pytest.raises(ValueError):
            PNORI1.from_nmea(sentence)

    def test_to_dict_with_string_coords(self):
        """Test to_dict includes string coordinate system."""
        sentence = "$PNORI1,4,Test,4,20,0.20,1.00,BEAM*00"
        config = PNORI1.from_nmea(sentence)
        data_dict = config.to_dict()

        assert data_dict["sentence_type"] == "PNORI1"
        assert data_dict["coord_system_name"] == "BEAM"
        assert data_dict["coord_system_code"] == 2  # BEAM maps to 2


class TestPNORI2:
    """Test PNORI2 parser (tagged, string coords)."""

    def test_parse_valid_tagged_sentence(self):
        """Test parsing valid PNORI2 tagged sentence."""
        sentence = "$PNORI2,IT=4,SN=123456,NB=4,NC=30,BD=1.00,CS=5.00,CY=BEAM*68"
        config = PNORI2.from_nmea(sentence)

        assert config.instrument_type == InstrumentType.SIGNATURE
        assert config.head_id == "123456"
        assert config.beam_count == 4
        assert config.cell_count == 30
        assert config.blanking_distance == 1.00
        assert config.cell_size == 5.00
        assert config.coordinate_system == CoordinateSystem.BEAM

    def test_parse_fields_in_different_order(self):
        """Test that field order doesn't matter."""
        sentence = "$PNORI2,CY=ENU,CS=1.00,BD=0.20,NC=20,NB=4,SN=Test,IT=4*00"
        config = PNORI2.from_nmea(sentence)

        assert config.head_id == "Test"
        assert config.coordinate_system == CoordinateSystem.ENU

    def test_missing_required_tag_raises_error(self):
        """Test that missing required tag raises ValueError."""
        # Provides enough fields (8), but CY=XYZ is missing because XX=1 is used instead
        sentence = "$PNORI2,IT=4,SN=Test,NB=4,NC=20,BD=0.20,CS=1.00,XX=1*00"
        with pytest.raises(ValueError, match="Missing required tags"):
            PNORI2.from_nmea(sentence)

    def test_unknown_tag_raises_error(self):
        """Test that unknown tag raises ValueError."""
        sentence = "$PNORI2,IT=4,SN=Test,NB=4,NC=20,BD=0.20,CS=1.00,CY=ENU,XX=99*00"
        with pytest.raises(ValueError, match="Unknown tags"):
            PNORI2.from_nmea(sentence)

    def test_invalid_tag_format_no_equals_raises_error(self):
        """Test that field without '=' raises ValueError."""
        sentence = "$PNORI2,IT=4,SN=Test,NB=4,NC=20,BD=0.20,CS=1.00,CYENU*00"
        with pytest.raises(ValueError, match="must contain '='"):
            PNORI2.from_nmea(sentence)

    def test_duplicate_tag_raises_error(self):
        """Test that duplicate tags raise ValueError."""
        sentence = "$PNORI2,IT=4,IT=2,SN=Test,NB=4,NC=20,BD=0.20,CS=1.00,CY=ENU*00"
        with pytest.raises(ValueError, match="Duplicate tag"):
            PNORI2.from_nmea(sentence)

    def test_round_trip_serialization(self):
        """Test parsing and serialization round-trip."""
        original = "$PNORI2,IT=4,SN=Test,NB=4,NC=20,BD=0.20,CS=1.00,CY=XYZ*00"
        config = PNORI2.from_nmea(original)
        reserialized = config.to_nmea()

        config2 = PNORI2.from_nmea(reserialized)
        assert config.head_id == config2.head_id
        assert config.coordinate_system == config2.coordinate_system

    def test_all_pnori_validation_rules_apply(self):
        """Test that PNORI validation rules apply to PNORI2."""
        # Signature must have 4 beams
        sentence = "$PNORI2,IT=4,SN=Test,NB=3,NC=20,BD=0.20,CS=1.00,CY=ENU*00"
        with pytest.raises(ValueError):
            PNORI2.from_nmea(sentence)

    def test_to_dict_method(self):
        """Test conversion to dictionary."""
        sentence = "$PNORI2,IT=4,SN=Test,NB=4,NC=20,BD=0.20,CS=1.00,CY=BEAM*00"
        config = PNORI2.from_nmea(sentence)
        data_dict = config.to_dict()

        assert data_dict["sentence_type"] == "PNORI2"
        assert data_dict["head_id"] == "Test"


class TestPNORITag:
    """Test PNORI tag parsing helper."""

    def test_parse_valid_tagged_field(self):
        """Test parsing valid tagged field."""
        tag, value = PNORITag.parse_tagged_field("IT=4")
        assert tag == "IT"
        assert value == "4"

    def test_parse_field_with_whitespace(self):
        """Test parsing field with whitespace."""
        tag, value = PNORITag.parse_tagged_field("  IT = 4  ")
        assert tag == "IT"
        assert value == "4"

    def test_invalid_tag_raises_error_deferred(self):
        """Test that invalid tag raises ValueError in from_nmea (deferred from helper)."""
        # PNORITag.parse_tagged_field no longer raises for unknown tags
        # but from_nmea DOES.
        sentence = "$PNORI2,IT=4,SN=Test,NB=4,NC=20,BD=0.20,CS=1.00,CY=ENU,XX=99*00"
        with pytest.raises(ValueError, match="Unknown tags"):
            PNORI2.from_nmea(sentence)

    def test_missing_equals_raises_error(self):
        """Test that missing '=' raises ValueError."""
        with pytest.raises(ValueError, match="must contain '='"):
            PNORITag.parse_tagged_field("IT4")
