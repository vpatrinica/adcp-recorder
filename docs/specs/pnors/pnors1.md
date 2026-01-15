[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORS Family](README.md)

# PNORS1 Specification

**Positional sensor data with uncertainty** (DF=101) including standard deviation fields.

## Format

```nmea
$PNORS1,Date,Time,ErrCode,StatusCode,Battery,SoundSpeed,HeadSD,Heading,Pitch,PitchSD,Roll,RollSD,Press,PressSD,Temp*CS
```

**Field Count**: 16 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|----------|-------|-------------|-------------|------|--------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | "$PNORS1" | - | Always `$PNORS1` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | - | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | - | Measurement time |
| 3 | Error Code | int | INTEGER | - | N | 0+ | Error identifier (0=no error) |
| 4 | Status Code | str | CHAR(8) | - | hhhhhhhh | - | Status bitmask (hex) |
| 5 | Battery | float | DECIMAL(4,1) | V | dd.d | 0-99 | Battery voltage |
| 6 | Sound Speed | float | DECIMAL(6,1) | m/s | dddd.d | 1400-2000 | Speed of sound |
| 7 | Heading StdDev | float | DECIMAL(5,2) | deg | dd.dd | 0-99 | Heading standard deviation |
| 8 | Heading | float | DECIMAL(5,1) | deg | ddd.d | 0-360 | Compass heading |
| 9 | Pitch | float | DECIMAL(4,1) | deg | dd.d | -90 to +90 | Instrument pitch |
| 10 | Pitch StdDev | float | DECIMAL(5,2) | deg | dd.dd | 0-99 | Pitch standard deviation |
| 11 | Roll | float | DECIMAL(4,1) | deg | dd.d | -90 to +90 | Instrument roll |
| 12 | Roll StdDev | float | DECIMAL(5,2) | deg | dd.dd | 0-99 | Roll standard deviation |
| 13 | Pressure | float | DECIMAL(7,3) | dBar | ddd.ddd | 0-999 | Water pressure |
| 14 | Pressure StdDev | float | DECIMAL(5,2) | dBar | dd.dd | 0-99 | Pressure standard deviation |
| 15 | Temperature | float | DECIMAL(5,2) | °C | dd.dd | -5 to +50 | Water temperature |

## Example Sentence

```nmea
$PNORS1,083013,132455,0,34000034,22.9,1500.0,0.02,123.4,45.6,0.02,23.4,0.02,123.456,0.02,24.56*39
```

**Parsed**:

- Date: August 30, 2013 (MMDDYY = 083013), Time: 13:24:55
- Error Code: 0, Status: 34000034
- Battery: 22.9 V, Sound Speed: 1500.0 m/s
- Heading: 123.4° (±0.02°)
- Pitch: 45.6° (±0.02°), Roll: 23.4° (±0.02°)
- Pressure: 123.456 dBar (±0.02), Temperature: 24.56°C

## Related Documents

- [PNORS2](pnors2.md) - Same data, tagged format
- [PNORS Family Overview](README.md)

---

[⬆️ Back to PNORS Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
