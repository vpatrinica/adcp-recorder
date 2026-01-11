[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORA Specification

**Altitude/range data message** for distance to surface or bottom.

This specification covers two distinct formats for the `$PNORA` sentence:
1.  **Standard (Untagged)**: Field-position based format (DF=200)
2.  **Tagged (DF=201)**: Key-value pair format

---

## PNORA - Standard (Untagged / DF=200)

### Format

```
$PNORA,Date,Time,Pressure,Distance,Quality,Status,Pitch,Roll*CHECKSUM
```

**Field Count**: 9 fields (including prefix)

### Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORA` |
| 1 | Date | str | CHAR(6) | - | YYMMDD | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Pressure | float | DECIMAL(7,3) | decibars | 0-20000 | Water pressure |
| 4 | Distance | float | DECIMAL(7,3) | meters | 0-1000 | Vertical distance |
| 5 | Quality | int | INTEGER | - | - | Quality indicator/confidence |
| 6 | Status | str | CHAR(2) | - | - | 2 hex digits status |
| 7 | Pitch | float | DECIMAL(4,1) | degrees | -90 to +90 | Instrument pitch |
| 8 | Roll | float | DECIMAL(4,1) | degrees | -90 to +90 | Instrument roll |

### Example Sentence

```
$PNORA,141112,084201,10.123,5.678,95,01,1.2,-0.5*XX
```

### Validation Rules

1. Date/time validation
2. Distance: 0-1000m
3. Status: 2 hex digits
4. Pitch/Roll: -90 to +90 degrees

---

## PNORA - Altimeter Data with Tags (DF=201)

### Description
NMEA-formatted altimeter data with tags from Altimeter telemetry mode (Data Format 201). Always uses Leading Edge algorithm.

### Format
`$PNORA,DATE=<date>,TIME=<time>,P=<pressure>,A=<altimeter_distance>,Q=<quality>,ST=<status>,PI=<pitch>,R=<roll>*<checksum>`

### Data Fields
- Column=0, Field=Identifier, Tag=-, Data Type=String, Format="$PNORA", Unit=-, Description=Sentence identifier, Notes=Always present
- Column=1, Field=Date, Tag=DATE, Data Type=Integer, Format=YYMMDD, Unit=-, Description=Measurement date, Notes=YearMonthDay
- Column=2, Field=Time, Tag=TIME, Data Type=Integer, Format=hhmmss, Unit=-, Description=Measurement time, Notes=HourMinuteSecond
- Column=3, Field=Pressure, Tag=P, Data Type=Float, Format=ddd.ddd, Unit=dBar, Description=Water pressure, Notes=Depth equivalent
- Column=4, Field=Altimeter Distance, Tag=A, Data Type=Float, Format=ddd.ddd, Unit=m, Description=Leading edge distance, Notes=Range dependent
- Column=5, Field=Quality Parameter, Tag=Q, Data Type=Integer, Format=N, Unit=-, Description=Quality indicator, Notes=See notes
- Column=6, Field=Status, Tag=ST, Data Type=String, Format=XX, Unit=-, Description=Status code, Notes=2 hex characters
- Column=7, Field=Pitch, Tag=PI, Data Type=Float, Format=d.d, Unit=deg, Description=Instrument pitch, Notes=Signed, -9.9 to +9.9°
- Column=8, Field=Roll, Tag=R, Data Type=Float, Format=d.d, Unit=deg, Description=Instrument roll, Notes=Signed, -9.9 to +9.9°
- Column=9, Field=Checksum, Tag=-, Data Type=Hex, Format=*hh, Unit=-, Description=NMEA checksum, Notes=Always present

### Example
```
$PNORA,DATE=190902,TIME=122341,P=0.000,A=24.274,Q=13068,ST=08,PI=-2.6,R=-0.8*72
```

### Interpretation
- Date: September 2, 2019 (DATE=190902)
- Time: 12:23:41 UTC (TIME=122341)
- Pressure: 0.000 dBar (P=0.000, surface)
- Altimeter distance: 24.274 m (A=24.274)
- Quality parameter: 13068 (Q=13068)
- Status: 08 (hex, ST=08)
- Pitch: -2.6° (PI=-2.6, tilted backward)
- Roll: -0.8° (R=-0.8, slight left tilt)
- Checksum: 72

### Quality Parameter
- bitfield indicating measurement quality
- Higher values generally indicate better quality
- Specific bit definitions in instrument documentation

### Status Codes
- 2-character hex code
- 00: Normal operation
- Other values indicate specific states/errors

### Notes
- Used in Altimeter mode with DF=201
- All fields have tags
- Always uses Leading Edge algorithm
- Date format: YYMMDD
- Time format: hhmmss
- Same data as DF=200 but with tags

---

## Related Documents

- [All Specifications](README.md)

---

[📋 All Specs](README.md) | [🏠 Home](../README.md)
