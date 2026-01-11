[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORS Family](README.md)

# PNORS1 Specification

**Sensor data variant 1** with extended format.

## Format

```
$PNORS1,MMDDYY,HHMMSS,ErrorHex,StatusHex,Battery,SoundSpeed,HeadStdDev,Heading,Pitch,PitchStdDev,Roll,RollStdDev,Press,PressStdDev,Temp*CHECKSUM
```

**Field Count**: 16 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORS1` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Error Code | int | INTEGER | - | - | Error identifier |
| 4 | Status Code | str | CHAR(8) | - | 8 hex chars | Status bitmask |
| 5 | Battery | float | DECIMAL(4,1) | V | 0-30 | Battery voltage |
| 6 | Sound Speed | float | DECIMAL(6,1) | m/s | 1400-1600 | Speed of sound |
| 7 | Heading StdDev | float | DECIMAL(5,1) | deg | 0-99.9 | Heading standard deviation |
| 8 | Heading | float | DECIMAL(5,1) | deg | 0-360 | Compass heading |
| 9 | Pitch | float | DECIMAL(4,1) | deg | -90 to +90 | Instrument pitch |
| 10 | Pitch StdDev | float | DECIMAL(4,1) | deg | 0-99.9 | Pitch standard deviation |
| 11 | Roll | float | DECIMAL(5,1) | deg | -180 to +180 | Instrument roll |
| 12 | Roll StdDev | float | DECIMAL(5,1) | deg | 0-99.9 | Roll standard deviation |
| 13 | Pressure | float | DECIMAL(7,3) | dBar | 0-20000 | Water pressure |
| 14 | Pressure StdDev | float | DECIMAL(7,3) | dBar | 0-99.9 | Pressure standard deviation |
| 15 | Temperature | float | DECIMAL(5,2) | °C | -5 to +50 | Water temperature |

## Example Sentence

```
$PNORS1,083013,132455,0,34000034,22.9,1500.0,0.02,123.4,45.6,0.02,23.4,0.02,123.456,0.02,24.56*39
```

**Differences from PNORS**:
- **Added**: Standard deviation fields for Heading, Pitch, Roll, and Pressure
- **Removed**: Analog inputs 1 & 2
- **Fields**: 16 positional fields

## Validation Rules

Same as PNORS, plus:
- Standard deviations generally small (0.0-10.0)

## Related Documents

- [PNORS Family Overview](README.md)
- [PNORS Base](pnors.md)

---

[⬆️ Back to PNORS Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
