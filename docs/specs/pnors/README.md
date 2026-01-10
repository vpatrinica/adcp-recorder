[🏠 Home](../../README.md) > [📋 Specs](../README.md) > PNORS Family

# PNORS Message Family

The PNORS family contains sensor data messages reporting environmental parameters and instrument status.

## Message Variants

- **[PNORS](pnors.md)** - Base sensor data format
- **PNORS1** - Sensor data variant 1 (similar structure)
- **PNORS2** - Sensor data variant 2 (tagged format)  
- **PNORS3** - Sensor data variant 3 (extended format)
- **PNORS4** - Sensor data variant 4 (compact format)

##Common Fields

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| Date | String (MMDDYY) | - | Measurement date |
| Time | String (HHMMSS) | - | Measurement time |
| Error Code | Hex String (8 chars) | - | Error bitmask |
| Status Code | Hex String (8 chars) | - | Status bitmask |
| Battery Voltage | Float | volts | Battery voltage (0-30V) |
| Sound Speed | Float | m/s | Speed of sound in water (1400-2000 m/s) |
| Heading | Float | degrees | Compass heading (0-360°) |
| Pitch | Float | degrees | Instrument pitch (-90 to +90°) |
| Roll | Float | degrees | Instrument roll (-180 to +180°) |
| Pressure | Float | decibars | Water pressure (depth measurement) |
| Temperature | Float | °C | Water temperature (-5 to +50°C) |
| Analog Input 1 | Integer | - | First analog input value |
| Analog Input 2 | Integer | - | Second analog input value |

## Example Sentence

```
$PNORS,102115,090715,00000000,2A480000,14.4,1523.0,275.9,15.7,2.3,0.000,22.45,0,0*1C
```

## Related Documents

- [PNORS Base Specification](pnors.md)
- [Python Parsers](../../implementation/python/parsers.md)
- [DuckDB Schemas](../../implementation/duckdb/schemas.md)

---

[⬆️ Back to Specifications](../README.md) | [🏠 Home](../../README.md)
