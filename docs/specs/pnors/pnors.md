[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORS Family](README.md)

# PNORS Specification

**Sensor data** (DF=100) with environmental parameters and instrument diagnostics.

## Format

```nmea
$PNORS,Date,Time,ErrorHex,StatusHex,Battery,SoundSpeed,Heading,Pitch,Roll,Pressure,Temperature,Analog1,Analog2*CHECKSUM
```

**Field Count**: 14 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|----------|-------|-------------|-------------|------|--------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | "$PNORS" | - | Always `$PNORS` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | - | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | - | Measurement time |
| 3 | Error Code | str | CHAR(8) | - | hh | - | Error code (hex) |
| 4 | Status Code | str | CHAR(8) | - | hh | - | Status code (hex) |
| 5 | Battery Voltage | float | DECIMAL(4,1) | V | dd.d | 0-99 | Battery voltage |
| 6 | Sound Speed | float | DECIMAL(6,1) | m/s | dddd.d | 1400-2000 | Speed of sound |
| 7 | Heading | float | DECIMAL(5,1) | deg | ddd.d | 0-360 | Compass heading |
| 8 | Pitch | float | DECIMAL(4,1) | deg | dd.d | -90 to +90 | Instrument pitch |
| 9 | Roll | float | DECIMAL(4,1) | deg | dd.d | -90 to +90 | Instrument roll |
| 10 | Pressure | float | DECIMAL(7,3) | dBar | ddd.ddd | 0-999 | Water pressure |
| 11 | Temperature | float | DECIMAL(5,2) | °C | dd.dd | -5 to +50 | Water temperature |
| 12 | Analog Input 1 | int | SMALLINT | - | n/a | 0-65535 | First analog input |
| 13 | Analog Input 2 | int | SMALLINT | - | n/a | 0-65535 | Second analog input |

## Example Sentence

```nmea
$PNORS,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,2.3,0.000,22.45,0,0*1C
```

**Parsed**:

- Date: October 21, 2015 (MMDDYY = 102115), Time: 09:07:15
- Error Code: 00000000 (no errors), Status Code: 2A480000
- Battery: 14.4 V, Sound Speed: 1523.0 m/s
- Heading: 275.9°, Pitch: 15.7°, Roll: 2.3°
- Pressure: 0.000 dBar, Temperature: 22.45°C
- Analog inputs: 0, 0

## Related Documents

- [PNORS1](pnors1.md) / [PNORS2](pnors2.md) - With uncertainty fields
- [PNORS3](pnors3.md) / [PNORS4](pnors4.md) - Minimal sensor data
- [PNORS Family Overview](README.md)

---

[⬆️ Back to PNORS Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
