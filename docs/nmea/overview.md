[🏠 Home](../README.md) > NMEA Protocol

# NMEA Protocol Overview

The ADCP Recorder processes NMEA 0183-style sentences with Nortek-specific message types (PNOR* family).

## Sentence Structure

NMEA sentences follow this general format:

```
$PREFIX,field1,field2,field3,...,fieldN*CHECKSUM\r\n
```

### Components

1. **Start delimiter**: `$`
2. **Prefix**: Message type identifier (e.g., `PNORI`, `PNORS`, `PNORC`)
3. **Fields**: Comma-separated data values
4. **Checksum delimiter**: `*`
5. **Checksum**: Two hexadecimal characters
6. **Line terminator**: `\r\n` (CRLF) - optional, not relied upon for parsing

### Example

```
$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E
│ │    │ │                  │ │  │    │    │ └─ Checksum
│ │    │ │                  │ │  │    │    └─ Coordinate system
│ │    │ │                  │ │  │    └─ Cell size (m)
│ │    │ │                  │ │  └─ Blanking distance (m)
│ │    │ │                  │ └─ Cell count
│ │    │ │                  └─ Beam count
│ │    │ └─ Head ID (serial number)
│ │    └─ Instrument type code
│ └─ Prefix (PNORI)
└─ Start delimiter
```

## Valid Prefixes

The system recognizes these NMEA message prefixes:

### Configuration Messages
- `PNORI` - Instrument configuration (base)
- `PNORI1` - Instrument configuration (untagged)
- `PNORI2` - Instrument configuration (tagged)

### Sensor Data Messages
- `PNORS` - Sensor data (base)
- `PNORS1` - Sensor data variant 1
- `PNORS2` - Sensor data variant 2
- `PNORS3` - Sensor data variant 3
- `PNORS4` - Sensor data variant 4

### Current Velocity Messages
- `PNORC` - Current velocity (base)
- `PNORC1` - Current velocity variant 1
- `PNORC2` - Current velocity variant 2
- `PNORC3` - Current velocity variant 3
- `PNORC4` - Current velocity variant 4

### Header Messages
- `PNORH3` - Header data variant 3
- `PNORH4` - Header data variant 4

### Additional Data Messages
- `PNORA` - Altitude/range data
- `PNORW` - Wave data
- `PNORB` - Bottom tracking data
- `PNORE` - Echo intensity data
- `PNORF` - Frequency data
- `PNORWD` - Wave directional data

## Field Formats

### Positional Format

Fields appear in a fixed order without tags:

```
$PREFIX,value1,value2,value3,...,valueN*CHECKSUM
```

**Example**:
```
$PNORI1,4,123456,4,30,1.00,5.00,BEAM*5B
```

### Tagged Format

Fields use `TAG=VALUE` pairs, order-independent:

```
$PREFIX,TAG1=value1,TAG2=value2,...,TAGN=valueN*CHECKSUM
```

**Example**:
```
$PNORI2,IT=4,SN=123456,NB=4,NC=30,BD=1.00,CS=5.00,CY=BEAM*68
```

## Data Types

### Numeric Types

- **Integer**: `123`, `4`, `30`
- **Decimal**: `1.00`, `0.20`, `15.7`
- **Hexadecimal**: `00000000`, `2A480000` (error/status codes)

### String Types

- **Alphanumeric**: `Signature1000900001`, `AQD12345`
- **Enumeration**: `BEAM`, `ENU`, `XYZ`
- **Date**: `MMDDYY` (e.g., `102115` = October 21, 2015)
- **Time**: `HHMMSS` (e.g., `143052` = 14:30:52)

## Character Set

### Valid Characters

NMEA sentences use printable ASCII only:

- **Printable ASCII**: `0x20` (space) to `0x7E` (`~`)
- **Delimiters**: `$`, `*`, `,`
- **Line terminators**: `\r` (CR), `\n` (LF)

### Invalid Characters

- Control characters (except CR/LF): `0x00` to `0x1F`
- Extended ASCII: `0x80` to `0xFF`
- NULL bytes: `0x00`

When invalid characters are detected, the system switches to [binary blob recording mode](../architecture/binary-detection.md).

## Sentence Length

- **Minimum**: ~15 characters (shortest valid sentence)
- **Maximum**: 2048 characters (buffer limit)
- **Typical**: 50-200 characters

## Line Termination

### Standard Termination

NMEA standard specifies `\r\n` (CRLF) after checksum:

```
$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E\r\n
```

### Flexible Parsing

The parser **does not rely on line terminators** because:

1. **Redundant CRLF**: Multiple terminators may appear
2. **Missing CRLF**: Some instruments omit terminators
3. **Inconsistent terminators**: Mix of `\r\n`, `\n`, or `\r`

Instead, sentence boundaries are detected by:
- `$` prefix (start)
- `*` delimiter (end of data)
- Checksum (2 hex chars after `*`)

## Sentence Variants

### Family Numbering

Many message types have numbered variants (e.g., PNORI, PNORI1, PNORI2):

- **Base** (no suffix): Original format
- **Variant 1** (suffix 1): Extended or alternative format
- **Variant 2** (suffix 2): Tagged format or additional variant
- **Variant 3, 4** (suffix 3, 4): Further specialized formats

### Format Differences

Variants may differ in:
- Number of fields
- Field order
- Tagged vs. positional fields
- Data precision
- Additional metadata

## Related Documents

- [Checksum Calculation](checksum.md)
- [Data Validation](validation.md)
- [Message Specifications](../specs/README.md)
- [Binary Detection](../architecture/binary-detection.md)

---

[⬆️ Back to NMEA Protocol](README.md) | [🏠 Home](../README.md)
