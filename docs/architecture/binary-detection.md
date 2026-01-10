[🏠 Home](../README.md) > [Architecture](overview.md)

# Binary Detection and Blob Recording

NMEA sentences are expected to contain only printable ASCII characters (plus CRLF). When the serial port unexpectedly receives binary data, the system detects this condition and switches to blob recording mode.

## Binary Data Detection

### Detection Criteria

Non-printable characters outside the expected NMEA character set:

**Valid NMEA Characters**:
- Printable ASCII: `0x20` (space) to `0x7E` (`~`)
- Line terminators: `CR` (`0x0D`), `LF` (`0x0A`)
- NMEA delimiters: `$`, `*`, `,`

**Invalid (Binary) Characters**:
- Control characters: `0x00` to `0x1F` (except CR, LF)
- Extended ASCII: `0x80` to `0xFF`
- NULL bytes: `0x00`

### Detection Threshold

```python
MAX_NON_NMEA_CHARS_PER_LINE = 10  # Configurable
MIN_CHARS_TO_CHECK = 1024          # Start checking after this many chars

non_nmea_chars = scan_for_nonnmea(payload)

if non_nmea_chars > MAX_NON_NMEA_CHARS_PER_LINE:
    switch_to_blob_recording_mode()
```

### Scan Implementation

```python
def scan_for_nonnmea(payload: bytes) -> int:
    """
    Count non-NMEA characters in payload.
    
    Returns:
        Number of invalid characters found
    """
    non_nmea_count = 0
    
    for byte in payload:
        # Allow printable ASCII (0x20-0x7E) and CR/LF
        if byte == 0x0D or byte == 0x0A:  # CR or LF
            continue
        elif byte >= 0x20 and byte <= 0x7E:  # Printable ASCII
            continue
        else:
            non_nmea_count += 1
    
    return non_nmea_count
```

## Blob Recording Mode

When binary data is detected, the system switches from line-based NMEA parsing to raw binary blob recording.

### Mode Transition

1. Detect excessive non-NMEA characters
2. Log mode transition warning
3. Stop NMEA parsing
4. Start blob recording
5. Continue until data returns to valid NMEA format

### Blob File Output

Binary data is saved to timestamped files in the error directory:

```
./data_folder/errors_binary/YYYYMMDD_HHMMSS_bin_<identifier>.dat
```

**Example Filenames**:
```
./data_folder/errors_binary/20250110_143522_bin_001.dat
./data_folder/errors_binary/20250110_143645_bin_002.dat
```

### File Naming Components

- **YYYYMMDD**: Date of first binary data detection
- **HHMMSS**: Time of first binary data detection
- **identifier**: Sequential counter within the same timestamp

### Recording Implementation

```python
import os
from datetime import datetime

def record_binary_blob(data: bytes, output_folder: str):
    """
    Record binary data to timestamped file.
    
    Args:
        data: Raw binary data
        output_folder: Base folder for binary error files
    """
    # Create errors_binary folder if not exists
    binary_folder = os.path.join(output_folder, 'errors_binary')
    os.makedirs(binary_folder, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Find next available identifier
    identifier = 1
    while True:
        filename = f"{timestamp}_bin_{identifier:03d}.dat"
        filepath = os.path.join(binary_folder, filename)
        if not os.path.exists(filepath):
            break
        identifier += 1
    
    # Write binary data
    with open(filepath, 'wb') as f:
        f.write(data)
    
    log_warning(f"Binary blob saved to {filepath} ({len(data)} bytes)")
```

## Recovery from Binary Mode

### Automatic Recovery

The system continuously monitors incoming data for valid NMEA patterns:

```python
def check_nmea_recovery(buffer: bytes) -> bool:
    """
    Check if buffer contains valid NMEA sentence start pattern.
    
    Returns:
        True if NMEA-like pattern detected
    """
    # Look for NMEA start pattern: $PNOR
    if b'$PNOR' in buffer:
        # Verify next characters are printable
        start_idx = buffer.find(b'$PNOR')
        sample = buffer[start_idx:start_idx+50]
        
        non_nmea = scan_for_nonnmea(sample)
        if non_nmea <= 2:  # Allow small number of errors
            return True
    
    return False
```

### Recovery Procedure

1. Detect NMEA pattern in binary stream
2. Log recovery event
3. Flush any remaining binary data to blob file
4. Resume NMEA parsing mode
5. Reset non-NMEA character counters

## Tracking and Logging

### Counters

```python
# Module-level state
non_nmea_rx_counter = 0      # Total non-NMEA chars received
non_nmea_cons_recs = 0       # Consecutive records with binary data
binary_blob_counter = 0      # Number of blob files created
```

### Logging Events

```python
# Detection
log_warning(f"Binary data detected: {non_nmea_chars} non-NMEA chars in {len(payload)} bytes")

# Mode switch
log_error("Switching to binary blob recording mode")

# File creation
log_info(f"Created binary blob file: {filepath}")

# Recovery
log_info("Valid NMEA pattern detected, resuming NMEA parsing mode")
```

## Error Analysis

### Post-Processing Binary Blobs

Binary blob files can be analyzed offline to diagnose issues:

```python
def analyze_binary_blob(filepath: str):
    """
    Analyze binary blob for patterns indicating source of corruption.
    """
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Character distribution
    char_counts = {}
    for byte in data:
        char_counts[byte] = char_counts.get(byte, 0) + 1
    
    # Look for partial NMEA fragments
    nmea_fragments = []
    for i in range(len(data) - 5):
        if data[i:i+5] == b'$PNOR':
            nmea_fragments.append(i)
    
    # Report
    print(f"Blob size: {len(data)} bytes")
    print(f"Unique byte values: {len(char_counts)}")
    print(f"NMEA fragments found: {len(nmea_fragments)}")
    
    # Check if it's actually compressed data
    entropy = calculate_entropy(data)
    if entropy > 7.5:
        print("High entropy - possibly compressed or encrypted data")
```

## Configuration

### Adjustable Parameters

```python
# Detection thresholds
MAX_NON_NMEA_CHARS_PER_LINE = 10   # Trigger threshold
MIN_CHARS_TO_CHECK = 1024           # Buffer size before checking

# Recovery thresholds
RECOVERY_CHECK_INTERVAL = 100       # Check every N bytes
RECOVERY_NMEA_THRESHOLD = 2         # Max errors to consider recovered

# File management
BINARY_BLOB_MAX_SIZE = 10_000_000   # 10MB max per blob file
```

### Output Directory

```python
# Configurable via CLI
data_folder = "./data_report"  # Default
binary_error_folder = os.path.join(data_folder, "errors_binary")
```

## Common Causes of Binary Data

1. **Baud Rate Mismatch**: Incorrect serial port configuration
2. **Instrument Firmware Upgrade**: Binary transfer mode activated
3. **Data Corruption**: Electrical interference on serial line
4. **Buffer Overflow**: Instrument sending binary diagnostic data
5. **Configuration Mode**: Instrument in non-NMEA output mode

## Related Documents

- [System Overview](overview.md)
- [Serial Processing](serial-processing.md)
- [NMEA Overview](../nmea/overview.md)
- [Data Validation](../nmea/validation.md)

---

[⬆️ Back to Architecture](overview.md) | [🏠 Home](../README.md)
