[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORS Family](README.md)

# PNORS3 Specification

**Compact sensor data format** with reduced fields.

## Format

```
$PNORS3,MMDDYY,HHMMSS,Battery,Heading,Pitch,Roll,Pressure,Temperature*CHECKSUM
```

**Field Count**: 9 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORS3` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Battery Voltage | float | DECIMAL(4,1) | volts | 0-30 | Battery voltage |
| 4 | Heading | float | DECIMAL(5,1) | degrees | 0-360 | Compass heading |
| 5 | Pitch | float | DECIMAL(4,1) | degrees | -90 to +90 | Instrument pitch |
| 6 | Roll | float | DECIMAL(5,1) | degrees | -180 to +180 | Instrument roll |
| 7 | Pressure | float | DECIMAL(7,3) | decibars | 0-20000 | Water pressure |
| 8 | Temperature | float | DECIMAL(5,2) | °C | -5 to +50 | Water temperature |

## Example Sentence

```
$PNORS3,102115,090715,14.4,275.9,15.7,2.3,0.000,22.45*XX
```

## Differences from PNORS

- **Removed**: Error codes, status codes, sound speed, analog inputs
- **Compact**: Essential sensor data only
- **Use**: Bandwidth-constrained applications

## Validation Rules

Same field validation as PNORS for included fields.

## Related Documents

- [PNORS Family Overview](README.md)
- [PNORS Base](pnors.md)

---

[⬆️ Back to PNORS Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
