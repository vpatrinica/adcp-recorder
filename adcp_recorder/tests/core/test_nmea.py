"""Tests for core NMEA protocol utilities."""

import pytest
from adcp_recorder.core.nmea import (
    compute_checksum,
    validate_checksum,
    extract_prefix,
    split_sentence,
    is_binary_data,
)


class TestComputeChecksum:
    """Tests for compute_checksum function."""

    def test_valid_checksum_calculation(self):
        """Test checksum calculation for known valid sentence."""
        sentence = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0"
        checksum = compute_checksum(sentence)
        assert checksum == "1A"

    def test_checksum_with_existing_checksum(self):
        """Test that existing checksum is ignored in calculation."""
        sentence = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*FF"
        checksum = compute_checksum(sentence)
        assert checksum == "1A"  # Should match correct checksum, not FF

    def test_checksum_without_dollar(self):
        """Test checksum calculation when sentence lacks $ prefix."""
        sentence = "PNORI,4,Signature1000900001,4,20,0.20,1.00,0"
        checksum = compute_checksum(sentence)
        # Should still compute correctly
        assert len(checksum) == 2
        assert checksum.isupper()

    def test_checksum_empty_data(self):
        """Test checksum for minimal sentence."""
        sentence = "$"
        checksum = compute_checksum(sentence)
        assert checksum == "00"

    def test_checksum_returns_uppercase(self):
        """Test that checksum is always uppercase hex."""
        sentence = "$PNORI,4,Test,4,20,0.20,1.00,0"
        checksum = compute_checksum(sentence)
        assert checksum == checksum.upper()
        assert len(checksum) == 2


class TestValidateChecksum:
    """Tests for validate_checksum function."""

    def test_valid_checksum_passes(self):
        """Test that valid checksum validates successfully."""
        sentence = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*1A"
        assert validate_checksum(sentence) is True

    def test_invalid_checksum_fails(self):
        """Test that invalid checksum fails validation."""
        sentence = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*FF"
        assert validate_checksum(sentence) is False

    def test_lowercase_checksum_validates(self):
        """Test that lowercase checksum is handled correctly."""
        sentence = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*1a"
        assert validate_checksum(sentence) is True

    def test_missing_checksum_raises_error(self):
        """Test that sentence without checksum raises ValueError."""
        sentence = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0"
        with pytest.raises(ValueError, match="checksum"):
            validate_checksum(sentence)

    def test_checksum_with_whitespace(self):
        """Test checksum validation with trailing whitespace."""
        sentence = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*1A"
        assert validate_checksum(sentence) is True


class TestExtractPrefix:
    """Tests for extract_prefix function."""

    def test_extract_pnori_prefix(self):
        """Test extracting PNORI prefix."""
        sentence = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*50"
        assert extract_prefix(sentence) == "PNORI"

    def test_extract_pnors_prefix(self):
        """Test extracting PNORS prefix."""
        sentence = "$PNORS,20250110,120530,0,12.5,1500.0,45.2*XX"
        assert extract_prefix(sentence) == "PNORS"

    def test_extract_lowercase_prefix(self):
        """Test that prefix is returned uppercase."""
        sentence = "$pnori,4,Test*50"
        assert extract_prefix(sentence) == "PNORI"

    def test_missing_dollar_raises_error(self):
        """Test that sentence without $ raises ValueError."""
        sentence = "PNORI,4,Test*50"
        with pytest.raises(ValueError, match="\\$"):
            extract_prefix(sentence)

    def test_missing_comma_raises_error(self):
        """Test that sentence without comma raises ValueError."""
        sentence = "$PNORI"
        with pytest.raises(ValueError, match=","):
            extract_prefix(sentence)

    def test_extract_with_whitespace(self):
        """Test prefix extraction with leading/trailing whitespace."""
        sentence = "  $PNORI,4,Test*50  "
        assert extract_prefix(sentence) == "PNORI"


class TestSplitSentence:
    """Tests for split_sentence function."""

    def test_split_sentence_with_checksum(self):
        """Test splitting sentence with checksum."""
        sentence = "$PNORI,4,Test,4,20,0.20,1.00,0*50"
        fields, checksum = split_sentence(sentence)

        assert fields == ["$PNORI", "4", "Test", "4", "20", "0.20", "1.00", "0"]
        assert checksum == "50"

    def test_split_sentence_without_checksum(self):
        """Test splitting sentence without checksum."""
        sentence = "$PNORI,4,Test,4,20,0.20,1.00,0"
        fields, checksum = split_sentence(sentence)

        assert fields == ["$PNORI", "4", "Test", "4", "20", "0.20", "1.00", "0"]
        assert checksum is None

    def test_split_sentence_trims_whitespace(self):
        """Test that field whitespace is trimmed."""
        sentence = "$PNORI , 4 , Test , 4 * 50"
        fields, checksum = split_sentence(sentence)

        assert fields == ["$PNORI", "4", "Test", "4"]
        assert checksum == "50"

    def test_split_minimal_sentence(self):
        """Test splitting minimal sentence."""
        sentence = "$PNORI*50"
        fields, checksum = split_sentence(sentence)

        assert fields == ["$PNORI"]
        assert checksum == "50"

    def test_split_preserves_field_count(self):
        """Test that all fields are preserved."""
        sentence = "$PNORS,20250110,120530,0,12.5,1500.0,45.2,2.1,-1.3,5.2,15.8,0.0*XX"
        fields, _ = split_sentence(sentence)

        assert len(fields) == 12


class TestIsBinaryData:
    """Tests for is_binary_data function."""

    def test_valid_nmea_not_binary(self):
        """Test that valid NMEA sentence is not detected as binary."""
        data = b"$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E\r\n"
        assert is_binary_data(data) is False

    def test_printable_ascii_not_binary(self):
        """Test that printable ASCII is not detected as binary."""
        data = b"Hello World! This is printable ASCII with numbers 12345.\r\n"
        assert is_binary_data(data) is False

    def test_binary_blob_detected(self):
        """Test that binary blob is detected."""
        data = b"\x00\x01\x02\xff\xfe\xfd" * 100  # 600 bytes of binary
        assert is_binary_data(data) is True

    def test_mixed_mostly_binary_detected(self):
        """Test that mostly-binary content is detected."""
        # 90% binary, 10% ASCII
        data = (b"\x00" * 900) + (b"A" * 100)
        assert is_binary_data(data) is True

    def test_mixed_mostly_ascii_not_detected(self):
        """Test that mostly-ASCII content with some binary is not flagged."""
        # 95% ASCII, 5% binary (within tolerance)
        data = (b"A" * 950) + (b"\x00" * 50)
        assert is_binary_data(data) is False

    def test_empty_data_not_binary(self):
        """Test that empty data is not considered binary."""
        data = b""
        assert is_binary_data(data) is False

    def test_crlf_only_not_binary(self):
        """Test that CRLF-only data is not binary."""
        data = b"\r\n\r\n\r\n"
        assert is_binary_data(data) is False

    def test_threshold_parameter(self):
        """Test that threshold parameter limits scan length."""
        # Create 2000 bytes: first 500 ASCII, then binary
        data = (b"A" * 500) + (b"\x00" * 1500)

        # With threshold=500, should see only ASCII
        assert is_binary_data(data, threshold=500) is False

        # With threshold=2000, should detect binary
        assert is_binary_data(data, threshold=2000) is True
