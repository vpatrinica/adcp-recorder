[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORS Family](README.md)

# PNORS4 Specification

**Minimal sensor data format** with core measurements only.

## Format

```
$PNORS4,Battery,SoundSpeed,Heading,Pitch,Roll,Pressure,Temperature*CHECKSUM
```

**Field Count**: 8 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORS4` |
| 1 | Battery | float | DECIMAL(4,1) | Volts | 0-30 | Battery voltage |
| 2 | Sound Speed | float | DECIMAL(6,1) | m/s | 1400-1600 | Speed of sound |
| 3 | Heading | float | DECIMAL(5,1) | degrees | 0-360 | Compass heading |
| 4 | Pitch | float | DECIMAL(4,1) | degrees | -90 to +90 | Instrument pitch |
| 5 | Roll | float | DECIMAL(5,1) | degrees | -180 to +180 | Instrument roll |
| 6 | Pressure | float | DECIMAL(7,3) | decibars | 0-20000 | Water pressure |
| 7 | Temperature | float | DECIMAL(5,2) | °C | -5 to +50 | Water temperature |

## Example Sentence

```
$PNORS4,14.4,1523.0,275.9,15.7,2.3,0.000,22.45*XX
```

## Differences from PNORS

- **Minimal**: No date/time fields (usually follows PNORH4)
- **Compact**: Only common sensor parameters
- **Use**: High-rate burst recording or simple monitoring

## Validation Rules

Same field validation as PNORS for included fields.

## Related Documents

- [PNORS Family Overview](README.md)
- [PNORS Base](pnors.md)
- [PNORS3](pnors3.md) - Slightly more complete compact format

---

[⬆️ Back to PNORS Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
