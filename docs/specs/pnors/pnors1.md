[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORS Family](README.md)

# PNORS1 Specification

**Sensor data variant 1** with extended format.

## Format

```
$PNORS1,MMDDYY,HHMMSS,ErrorHex,StatusHex,Battery,SoundSpeed,Heading,Pitch,Roll,Pressure,Temperature,Analog1,Analog2,Salinity*CHECKSUM
```

**Field Count**: 16 fields (including prefix)

## Field Definitions

Same as PNORS base, plus:

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 14 | Salinity | float | DECIMAL(4,1) | PSU | 0-50 | Water salinity (Practical Salinity Units) |

## Example Sentence

```
$PNORS1,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,2.3,0.000,22.45,0,0,35.5*XX
```

**Differences from PNORS**:
- **Added**: Salinity field

## Validation Rules

Same as PNORS, plus:
- **Salinity**: 0-50 PSU (typical ocean: 30-37 PSU)

## Related Documents

- [PNORS Family Overview](README.md)
- [PNORS Base](pnors.md)

---

[⬆️ Back to PNORS Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
