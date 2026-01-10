[🏠 Home](../README.md) > [NMEA Protocol](overview.md)

# NMEA Checksum Calculation

NMEA sentences include a checksum for data integrity verification. The checksum is a 2-character hexadecimal value computed using an XOR algorithm.

## Checksum Format

The checksum appears after the `*` delimiter at the end of the sentence:

```
$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E
                                               └─ Checksum
```

## Calculation Algorithm

### XOR Algorithm

The checksum is the XOR of all characters **between** (but not including) the `$` and `*`:

```
1. Initialize checksum = 0
2. For each character between $ and *:
   a. checksum = checksum XOR character_code
3. Convert result to 2-digit hexadecimal
```

### Example Calculation

Sentence: `$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E`

Characters to XOR: `PNORI,4,Signature1000900001,4,20,0.20,1.00,0`

```python
data = "PNORI,4,Signature1000900001,4,20,0.20,1.00,0"
checksum = 0

for char in data:
    checksum ^= ord(char)

# Result: checksum = 46 (decimal) = 0x2E (hex)
```

## Implementation

### Python

```python
def compute_checksum(sentence: str) -> str:
    """
    Compute NMEA checksum for sentence.
    
    Args:
        sentence: Full NMEA sentence or data portion
        
    Returns:
        Two-character uppercase hexadecimal checksum
    """
    # Remove $ prefix and everything after * (if present)
    if sentence.startswith('$'):
        sentence = sentence[1:]
    if '*' in sentence:
        sentence = sentence.split('*')[0]
    
    # XOR all characters
    checksum = 0
    for char in sentence:
        checksum ^= ord(char)
    
    # Format as 2-digit uppercase hex
    return f"{checksum:02X}"


def validate_checksum(sentence: str) -> bool:
    """
    Validate checksum of complete NMEA sentence.
    
    Args:
        sentence: Complete sentence including checksum
        
    Returns:
        True if checksum is valid, False otherwise
    """
    if '*' not in sentence:
        return False
    
    # Split data and checksum
    data_part, checksum_part = sentence.rsplit('*', 1)
    expected_checksum = checksum_part.strip().upper()[:2]
    
    # Compute actual checksum
    sentence_for_check = data_part + '*'  # Include data up to *
    computed_checksum = compute_checksum(sentence_for_check)
    
    return computed_checksum.upper() == expected_checksum.upper()
```

### Usage

```python
# Compute checksum for new sentence
data = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0"
checksum = compute_checksum(data)
complete_sentence = f"{data}*{checksum}"
# Result: "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E"

# Validate received sentence
received = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E"
is_valid = validate_checksum(received)
# Result: True
```

## Validation Rules

### Required Validation

1. **Checksum present**: Sentence must contain `*` delimiter
2. **Correct format**: Two hexadecimal characters after `*`
3. **Matching value**: Computed checksum equals provided checksum

### Case Insensitivity

Checksums are case-insensitive for validation:

```python
"$PNORI,4,...*2E"  # Valid
"$PNORI,4,...*2e"  # Also valid
"$PNORI,4,...*2E\r\n"  # Valid (trailing CRLF ignored)
```

### Error Handling

When checksum validation fails:

1. Log the error with details
2. Record sentence to error table
3. Do not insert into record type table
4. Continue processing next sentence

```python
try:
    if not validate_checksum(sentence):
        log_error(f"Checksum mismatch: {sentence}")
        record_to_error_table(sentence, "CHECKSUM_MISMATCH")
        return None
except Exception as e:
    log_error(f"Checksum validation error: {e}")
    record_to_error_table(sentence, "CHECKSUM_ERROR")
    return None
```

## Common Issues

### Missing Checksum

Some instruments may omit checksums:

```
$PNORI,4,Signature1000900001,4,20,0.20,1.00,0
```

**Handling**: Accept sentence but log warning, set `checksum_valid = FALSE`

### Truncated Checksum

Incomplete checksum (1 character instead of 2):

```
$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2
```

**Handling**: Treat as checksum error, record to error table

### Incorrect Delimiters

Checksum not preceded by `*`:

```
$PNORI,4,Signature1000900001,4,20,0.20,1.00,0#2E
```

**Handling**: Treat as malformed sentence, record to error table

### Extra Characters

Characters between checksum and line terminator:

```
$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E EXTRA
```

**Handling**: Ignore trailing characters, validate checksum only

## Performance Optimization

### Pre-compiled Patterns

```python
import re

CHECKSUM_PATTERN = re.compile(r'\*([0-9A-Fa-f]{2})')

def extract_checksum(sentence: str) -> str:
    """Extract checksum using regex."""
    match = CHECKSUM_PATTERN.search(sentence)
    if match:
        return match.group(1).upper()
    return None
```

### Lookup Table

For high-performance applications, use XOR lookup table:

```python
# Pre-compute XOR lookup table
XOR_TABLE = [[i ^ j for j in range(256)] for i in range(256)]

def compute_checksum_fast(data: bytes) -> str:
    """Fast checksum using lookup table."""
    checksum = 0
    for byte in data:
        checksum = XOR_TABLE[checksum][byte]
    return f"{checksum:02X}"
```

## Testing

### Test Cases

```python
test_cases = [
    ("$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E", True),
    ("$PNORS,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,2.3,0.000,22.45,0,0*1C", True),
    ("$PNORC,102115,090715,1,12.34,56.78,90.12*XX", False),  # Invalid checksum
    ("$PNORI,4,Test*", False),  # Missing checksum value
]

for sentence, expected in test_cases:
    result = validate_checksum(sentence)
    assert result == expected, f"Failed for: {sentence}"
```

### Round-Trip Validation

```python
# Verify compute and validate are inverses
data = "$PNORI,4,Signature1000900001,4,20,0.20,1.00,0"
checksum = compute_checksum(data)
complete = f"{data}*{checksum}"
assert validate_checksum(complete) == True
```

## Related Documents

- [NMEA Overview](overview.md)
- [Data Validation](validation.md)
- [Parser Implementation](../implementation/python/parsers.md)

---

[⬆️ Back to NMEA Protocol](overview.md) | [🏠 Home](../README.md)
