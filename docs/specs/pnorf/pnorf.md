[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORF Specification

**Frequency data message** with acoustic frequency measurements and diagnostics.

## Format

```
$PNORF,MMDDYY,HHMMSS,Frequency,Bandwidth,TransmitPower*CHECKSUM
```

**Field Count**: 6 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORF` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Frequency | float | DECIMAL(7,1) | kHz | 50-2000 | Acoustic operating frequency |
| 4 | Bandwidth | float | DECIMAL(5,1) | kHz | 1-100 | Signal bandwidth |
| 5 | Transmit Power | float | DECIMAL(5,1) | watts | 0-100 | Acoustic transmit power |

## Example Sentence

```
$PNORF,102115,090715,600.0,15.0,25.5*XX
```

**Parsed**:
- Date: October 21, 2015
- Time: 09:07:15
- Frequency: 600.0 kHz
- Bandwidth: 15.0 kHz
- Transmit Power: 25.5 W

## Related Documents

- [All Specifications](../README.md)

---

[📋 All Specs](../README.md) | [🏠 Home](../../README.md)
