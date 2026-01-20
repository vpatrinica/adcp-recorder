import pytest

from adcp_recorder.parsers.pnora import PNORA
from adcp_recorder.parsers.pnorc import PNORC, PNORC1, PNORC2, PNORC3, PNORC4
from adcp_recorder.parsers.pnore import PNORE
from adcp_recorder.parsers.pnorf import PNORF
from adcp_recorder.parsers.pnorh import PNORH3, _validate_common_header
from adcp_recorder.parsers.pnors import PNORS1, PNORS2, PNORS3, PNORS4
from adcp_recorder.parsers.pnorwd import PNORWD
from adcp_recorder.parsers.utils import (
    parse_optional_float,
    validate_date_yy_mm_dd,
    validate_hex_string,
    validate_time_string,
)


class TestParserCoverage:
    def test_pnora_df201_errors(self):
        """Cover pnora.py lines 75-78 and validation."""
        # Missing required tag
        with pytest.raises(ValueError, match="Missing required tag"):
            PNORA.from_nmea("$PNORA,DATE=230101,TIME=120000,P=10.5")  # Missing others

        # Invalid data type
        with pytest.raises(ValueError, match="Invalid data type"):
            # P is not a float
            PNORA.from_nmea(
                "$PNORA,DATE=230101,TIME=120000,P=NOT_FLOAT,A=1.0,Q=1,ST=00,PI=0.0,R=0.0"
            )

    def test_pnora_coverage_gaps(self):
        """Cover remaining PNORA gaps."""
        # Line 52: Invalid prefix
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORA.from_nmea("$INVALID,1,2,3")

        # Line 81-82: Expected 9 fields (DF=200)
        with pytest.raises(ValueError, match="Expected 9 fields"):
            PNORA.from_nmea("$PNORA,230101,120000,10.5,1.0,1,00,0.0")  # 8 fields

        # Line 34-40: Validation errors (__post_init__)
        # Invalid date
        with pytest.raises(ValueError, match="Invalid date"):
            PNORA.from_nmea("$PNORA,999999,120000,10.5,1.0,1,00,0.0,0.0")

        # Invalid time
        with pytest.raises(ValueError, match="Invalid time"):
            PNORA.from_nmea("$PNORA,230101,999999,10.5,1.0,1,00,0.0,0.0")

        # Invalid pressure range
        with pytest.raises(ValueError, match="Pressure"):
            PNORA.from_nmea("$PNORA,230101,120000,1000.0,1.0,1,00,0.0,0.0")

        # Lines 47-48: Checksum splitting (valid case covers this, but ensure we use *)
        msg = "$PNORA,230101,120000,10.5,1.0,1,00,0.0,0.0*CHECKSUM"
        # We don't validate checksum in from_nmea, just strip it.
        # But if we want to valid object creation:
        p = PNORA.from_nmea(msg)
        assert p.checksum == "CHECKSUM"

        # Line 97: to_dict
        d = p.to_dict()
        assert d["sentence_type"] == "PNORA"
        assert d["pressure"] == 10.5

    def test_pnorc_coverage(self):
        """Cover pnorc.py gaps."""
        # Line 82: Invalid amplitude unit
        with pytest.raises(ValueError, match="Invalid amplitude unit"):
            PNORC.from_nmea("$PNORC,010123,120000,1,0,0,0,0,0,0,X,0,0,0,0,0,0,0,0")

        # Line 198: Invalid prefix PNORC1
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORC1.from_nmea("$INVALID,010123,120000,1,0,0,0,0,0,0,0,0,0,0,0,0,0")

        # Line 334: Unknown tag in PNORC2
        with pytest.raises(ValueError, match="Unknown tag"):
            PNORC2.from_nmea("$PNORC2,DATE=010123,TIME=120000,UNKNOWN=1")

        # Line 355-356: Missing tags in PNORC2
        with pytest.raises(ValueError, match="Missing required tags"):
            PNORC2.from_nmea("$PNORC2,DATE=010123")

        # Line 421: Invalid prefix PNORC3
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORC3.from_nmea("$INVALID,CP=0,SP=0,DIR=0,AA=0,AC=0")

        # Line 427: Unknown tag in PNORC3
        with pytest.raises(ValueError, match="Unknown tag"):
            PNORC3.from_nmea("$PNORC3,CP=0,SP=0,DIR=0,AA=0,AC=0,UNKNOWN=1")

        # Line 435-436: Missing tags in PNORC3
        with pytest.raises(ValueError, match="Missing required tags"):
            PNORC3.from_nmea("$PNORC3,CP=0")

        # Line 484: Invalid prefix PNORC4
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORC4.from_nmea("$INVALID,0,0,0,0,0")

    def test_pnorh_coverage(self):
        """Cover pnorh.py gaps."""
        # Lines 28-34: _validate_common_header (unused but needs coverage)
        _validate_common_header(0, 1, 1, 0.0, 0.0, "BEAM")
        with pytest.raises(ValueError, match="Invalid coordinate system"):
            _validate_common_header(0, 1, 1, 0.0, 0.0, "INVALID")

        # Line 72: Unknown tag PNORH3
        with pytest.raises(ValueError, match="Unknown tag"):
            PNORH3.from_nmea("$PNORH3,DATE=230101,TIME=120000,EC=0,SC=00000000,UNKNOWN=1")

        # Line 81-82: Missing tags PNORH3
        with pytest.raises(ValueError, match="Missing required tags"):
            PNORH3.from_nmea("$PNORH3,DATE=230101")

    def test_pnors_coverage(self):
        """Cover pnors.py gaps."""
        # Line 190: Invalid prefix PNORS1
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORS1.from_nmea("$INVALID," + ",".join(["0"] * 15))

        # Line 298: Invalid prefix PNORS2 (Wait, coverage said 298 is invalid prefix?)
        # Actually 298 is raise ValueError(f"Invalid prefix: {fields[0]}")
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORS2.from_nmea("$INVALID")

        # Line 403: Unknown tag PNORS3
        with pytest.raises(ValueError, match="Unknown tag"):
            PNORS3.from_nmea("$PNORS3,BV=12.0,SS=1500,H=0,PI=0,R=0,P=0,T=20,UNKNOWN=1")

        # Line 407-408: Missing tags PNORS3
        with pytest.raises(ValueError, match="Missing required tags"):
            PNORS3.from_nmea("$PNORS3,BV=12.0")

        # Line 462: Invalid prefix PNORS4
        with pytest.raises(ValueError, match="Invalid prefix"):
            PNORS4.from_nmea("$INVALID,0,0,0,0,0,0,0")

    def test_variable_length_parsers(self):
        """Cover pnore, pnorf, pnorwd length checks."""
        # PNORE line 38: num_frequencies mismatch
        # We need to bypass from_nmea validation to hit __post_init__ or construct manually
        # But from_nmea also checks length.
        # Lines 38 is inside __post_init__.
        # We can trigger it by manually instantiating or finding a case where
        # from_nmea passes but __post_init__ fails.
        # However, from_nmea implementation in PNORE/PNORF/PNORWD creates the list
        # based on num_freq, so it usually matches.
        # The only way it doesn't match is if we instantiate directly.
        with pytest.raises(ValueError, match="Missing energy density values"):
            PNORE(
                date="010123",
                time="120000",
                spectrum_basis=1,
                start_frequency=0.0,
                step_frequency=0.1,
                num_frequencies=2,
                energy_densities=[1.0],  # Only 1 value, expected 2
            )

        # PNORF line 41
        with pytest.raises(ValueError, match="Coefficient count mismatch"):
            PNORF(
                coefficient_flag="A1",
                date="010123",
                time="120000",
                spectrum_basis=1,
                start_frequency=0.0,
                step_frequency=0.1,
                num_frequencies=2,
                coefficients=[1.0],
            )

        # PNORWD line 41
        with pytest.raises(ValueError, match="Value count mismatch"):
            PNORWD(
                direction_type="MD",
                date="010123",
                time="120000",
                spectrum_basis=1,
                start_frequency=0.0,
                step_frequency=0.1,
                num_frequencies=2,
                values=[1.0],
            )

    def test_utils_coverage(self):
        """Cover utils.py lines."""
        # validate_date_yy_mm_dd
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date_yy_mm_dd("123")
        with pytest.raises(ValueError, match="Invalid date"):
            validate_date_yy_mm_dd("999999")

        # validate_hex_string
        with pytest.raises(ValueError, match="Invalid hex string"):
            validate_hex_string("00", 3, 3)
        with pytest.raises(ValueError, match="Invalid hex string"):
            validate_hex_string("GG", 2, 2)

        # validate_time_string
        with pytest.raises(ValueError, match="Invalid time format"):
            validate_time_string("1200")
        with pytest.raises(ValueError, match="Invalid time"):
            validate_time_string("999999")

        # parse_optional_float
        assert parse_optional_float("") is None
        assert parse_optional_float("   ") is None
        assert parse_optional_float("1.5") == 1.5

        # validate_date_mm_dd_yy
        from adcp_recorder.parsers.utils import parse_tagged_field, validate_date_mm_dd_yy

        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date_mm_dd_yy("123")
        with pytest.raises(ValueError, match="Invalid date"):
            validate_date_mm_dd_yy("999999")

        # parse_tagged_field
        with pytest.raises(ValueError, match="must contain '='"):
            parse_tagged_field("TAG_WITHOUT_VALUE")
