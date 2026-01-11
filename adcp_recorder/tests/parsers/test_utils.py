"""Unit tests for parser utility functions.
"""

import pytest
from adcp_recorder.parsers.utils import (
    validate_date_mm_dd_yy,
    validate_date_yy_mm_dd,
    validate_time_string,
    validate_hex_string,
    validate_range,
    parse_optional_float
)


class TestParserUtils:
    def test_validate_date_mm_dd_yy_valid(self):
        validate_date_mm_dd_yy("102115")
        validate_date_mm_dd_yy("010120")

    def test_validate_date_mm_dd_yy_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date_mm_dd_yy("12345")
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date_mm_dd_yy("1234567")
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date_mm_dd_yy("abcdef")

    def test_validate_date_mm_dd_yy_invalid_date(self):
        with pytest.raises(ValueError, match="Invalid date:"):
            validate_date_mm_dd_yy("999999")
        with pytest.raises(ValueError, match="Invalid date:"):
            validate_date_mm_dd_yy("130120")
        with pytest.raises(ValueError, match="Invalid date:"):
            validate_date_mm_dd_yy("013220")

    def test_validate_date_yy_mm_dd_valid(self):
        validate_date_yy_mm_dd("151021")
        validate_date_yy_mm_dd("200101")

    def test_validate_time_string_valid(self):
        validate_time_string("090715")
        validate_time_string("235959")
        validate_time_string("000000")

    def test_validate_time_string_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid time format"):
            validate_time_string("12345")
        with pytest.raises(ValueError, match="Invalid time format"):
            validate_time_string("abcdef")

    def test_validate_time_string_invalid_time(self):
        with pytest.raises(ValueError, match="Invalid time:"):
            validate_time_string("240000")
        with pytest.raises(ValueError, match="Invalid time:"):
            validate_time_string("006000")
        with pytest.raises(ValueError, match="Invalid time:"):
            validate_time_string("000060")

    def test_validate_hex_string_valid(self):
        validate_hex_string("00000000", 8)
        validate_hex_string("ABCDEF01", 8)
        validate_hex_string("FF", 2)

    def test_validate_hex_string_invalid(self):
        with pytest.raises(ValueError, match="Invalid hex string"):
            validate_hex_string("00G00000", 8)
        with pytest.raises(ValueError, match="Invalid hex string"):
            validate_hex_string("ABC", 4)

    def test_validate_range_valid(self):
        validate_range(10.0, "test", 0.0, 20.0)
        validate_range(0.0, "test", 0.0, 20.0)
        validate_range(20.0, "test", 0.0, 20.0)

    def test_validate_range_invalid(self):
        with pytest.raises(ValueError, match="out of range"):
            validate_range(-0.1, "test", 0.0, 20.0)
        with pytest.raises(ValueError, match="out of range"):
            validate_range(20.1, "test", 0.0, 20.0)

    def test_parse_optional_float(self):
        assert parse_optional_float("1.23") == 1.23
        assert parse_optional_float("-9.000") is None
        assert parse_optional_float("") is None
        assert parse_optional_float("invalid") is None
