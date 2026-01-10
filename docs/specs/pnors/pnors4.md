[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORS Family](README.md)

# PNORS4 Specification

**Minimal sensor data format** with core measurements only.

## Format

```
$PNORS4,MMDDYY,HHMMSS,Heading,Pressure,Temperature*CHECKSUM
```

**Field Count**: 6 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORS4` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Heading | float | DECIMAL(5,1) | degrees | 0-360 | Compass heading |
| 4 | Pressure | float | DECIMAL(7,3) | decibars | 0-20000 | Water pressure |
| 5 | Temperature | float | DECIMAL(5,2) | °C | -5 to +50 | Water temperature |

## Example Sentence

```
$PNORS4,102115,090715,275.9,0.000,22.45*XX
```

## Differences from PNORS

- **Minimal**: Only heading, pressure, temperature
- **Removed**: All other sensor data
- **Use**: Ultra-low bandwidth or simple deployments

## Validation Rules

Same field validation as PNORS for included fields.

## Related Documents

- [PNORS Family Overview](README.md)
- [PNORS Base](pnors.md)
- [PNORS3](pnors3.md) - Slightly more complete compact format

---

[⬆️ Back to PNORS Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
