"""NMEA protocol core utilities.

Implements NMEA 0183 sentence parsing, checksum validation, and binary data detection.
"""


def compute_checksum(sentence: str) -> str:
    """Compute NMEA checksum (XOR of characters between $ and *).

    Args:
        sentence: NMEA sentence, with or without checksum

    Returns:
        Two-character uppercase hex checksum (e.g., "2E")

    Example:
        >>> compute_checksum("$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E")
        '2E'
    """
    # Remove $ prefix and everything after * (including checksum)
    if sentence.startswith("$"):
        sentence = sentence[1:]

    if "*" in sentence:
        sentence = sentence.split("*", 1)[0]

    # XOR all characters
    checksum = 0
    for char in sentence:
        checksum ^= ord(char)

    return f"{checksum:02X}"


def validate_checksum(sentence: str) -> bool:
    """Validate NMEA sentence checksum.

    Args:
        sentence: Complete NMEA sentence with checksum (e.g., "$PNORI,...*2E")

    Returns:
        True if checksum is valid, False otherwise

    Raises:
        ValueError: If sentence doesn't contain a checksum
    """
    if "*" not in sentence:
        raise ValueError("Sentence must contain checksum separator '*'")

    data_part, provided_checksum = sentence.rsplit("*", 1)
    provided_checksum = provided_checksum.strip().upper()

    computed = compute_checksum(sentence)

    return computed == provided_checksum


def extract_prefix(sentence: str) -> str:
    """Extract message prefix from NMEA sentence.

    Args:
        sentence: NMEA sentence starting with $

    Returns:
        Message prefix without $ (e.g., "PNORI")

    Raises:
        ValueError: If sentence doesn't start with $ or has no comma

    Example:
        >>> extract_prefix("$PNORI,4,Signature1000900001,...")
        'PNORI'
    """
    sentence = sentence.strip()

    if not sentence.startswith("$"):
        raise ValueError("NMEA sentence must start with '$'")

    if "," not in sentence:
        raise ValueError("NMEA sentence must contain fields separated by ','")

    prefix = sentence[1:].split(",", 1)[0].upper()

    return prefix


def split_sentence(sentence: str) -> tuple[list[str], str | None]:
    """Split NMEA sentence into fields and checksum.

    Args:
        sentence: Complete NMEA sentence

    Returns:
        Tuple of (fields_list, checksum_string)
        Fields list includes the $PREFIX as first element
        Checksum is None if not present

    Example:
        >>> split_sentence("$PNORI,4,Test,4,20,0.20,1.00,0*2E")
        (['$PNORI', '4', 'Test', '4', '20', '0.20', '1.00', '0'], '2E')
    """
    sentence = sentence.strip()

    # Extract checksum if present
    checksum = None
    if "*" in sentence:
        data_part, checksum = sentence.rsplit("*", 1)
        checksum = checksum.strip().upper()
    else:
        data_part = sentence

    # Split fields and trim whitespace
    fields = [f.strip() for f in data_part.split(",")]

    return fields, checksum


def is_binary_data(data: bytes, threshold: int = 1024) -> bool:
    """Detect if data contains binary (non-NMEA) content.

    NMEA sentences should be printable ASCII (0x20-0x7E) plus CR/LF.
    This function detects binary blobs by counting non-printable characters.

    Args:
        data: Bytes to check
        threshold: Max bytes to scan before detection (default 1024)

    Returns:
        True if data appears to be binary, False if it looks like NMEA

    Note:
        Per spec, if more than MAX_NON_NMEA_CHARS_PER_LINE non-printable
        characters are found, we consider it binary data.
    """
    # NMEA valid characters: printable ASCII (0x20-0x7E) + CR (0x0D) + LF (0x0A)
    scan_length = min(len(data), threshold)
    non_nmea_count = 0

    # Count non-NMEA characters
    for byte in data[:scan_length]:
        # Allow printable ASCII, CR, LF
        if not (0x20 <= byte <= 0x7E or byte in (0x0D, 0x0A)):
            non_nmea_count += 1

    # If more than 10% of scanned bytes are non-NMEA, treat as binary
    max_allowed = scan_length // 10

    return non_nmea_count > max_allowed
