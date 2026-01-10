[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORS Family](README.md)

# PNORS Specification

**Base sensor data message** with environmental parameters and instrument diagnostics.

## Format

```
$PNORS,MMDDYY,HHMMSS,ErrorHex,StatusHex,Battery,SoundSpeed,Heading,Pitch,Roll,Pressure,Temperature,Analog1,Analog2*CHECKSUM
```

**Field Count**: 15 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORS` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Error Code | str | CHAR(8) | - | 8 hex chars | Error code bitmask |
| 4 | Status Code | str | CHAR(8) | - | 8 hex chars | Status code bitmask |
| 5 | Battery Voltage | float | DECIMAL(4,1) | volts | 0-30 | Battery voltage |
| 6 | Sound Speed | float | DECIMAL(6,1) | m/s | 1400-2000 | Speed of sound in water |
| 7 | Heading | float | DECIMAL(5,1) | degrees | 0-360 | Compass heading |
| 8 | Pitch | float | DECIMAL(4,1) | degrees | -90 to +90 | Instrument pitch |
| 9 | Roll | float | DECIMAL(5,1) | degrees | -180 to +180 | Instrument roll |
| 10 | Pressure | float | DECIMAL(7,3) | decibars | 0-20000 | Water pressure |
| 11 | Temperature | float | DECIMAL(5,2) | °C | -5 to +50 | Water temperature |
| 12 | Analog Input 1 | int | SMALLINT | - | 0-65535 | First analog input |
| 13 | Analog Input 2 | int | SMALLINT | - | 0-65535 | Second analog input |

## Example Sentence

```
$PNORS,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,2.3,0.000,22.45,0,0*1C
```

**Parsed**:
- Date: October 21, 2015
- Time: 09:07:15
- Error Code: 00000000 (no errors)
- Status Code: 2A480000
- Battery: 14.4 V
- Sound Speed: 1523.0 m/s
- Heading: 275.9°
- Pitch: 15.7°
- Roll: 2.3°
- Pressure: 0.000 dBar (surface)
- Temperature: 22.45°C
- Analog inputs: 0, 0

## Validation Rules

1. **Date Format**: 6 digits, valid month (01-12) and day (01-31)
2. **Time Format**: 6 digits, valid hour (00-23), minute (00-59), second (00-59)
3. **Error/Status Codes**: Exactly 8 hexadecimal characters
4. **Battery**: 0-30 V
5. **Sound Speed**: 1400-2000 m/s
6. **Heading**: 0-360° (exclusive upper bound)
7. **Pitch**: -90 to +90°
8. **Roll**: -180 to +180°
9. **Pressure**: 0-20000 dBar
10. **Temperature**: -5 to +50°C

## Related Documents

- [PNORS Family Overview](README.md)
- [Python Validation](../../nmea/validation.md)

---

[⬆️ Back to PNORS Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
