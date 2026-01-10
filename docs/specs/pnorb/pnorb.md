[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORB Specification

**Bottom tracking data message** with velocity relative to seabed.

## Format

```
$PNORB,MMDDYY,HHMMSS,VelEast,VelNorth,VelUp,BottomDist,Quality*CHECKSUM
```

**Field Count**: 8 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORB` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Velocity East | float | DECIMAL(8,4) | m/s | -10 to +10 | Eastward velocity relative to bottom |
| 4 | Velocity North | float | DECIMAL(8,4) | m/s | -10 to +10 | Northward velocity relative to bottom |
| 5 | Velocity Up | float | DECIMAL(8,4) | m/s | -10 to +10 | Upward velocity relative to bottom |
| 6 | Bottom Distance | float | DECIMAL(6,2) | meters | 0-1000 | Distance to seabed |
| 7 | Quality | int | TINYINT | % | 0-100 | Bottom track quality |

## Example Sentence

```
$PNORB,102115,090715,0.523,-0.312,0.001,45.20,88*XX
```

**Parsed**:
- Date: October 21, 2015
- Time: 09:07:15
- Velocity East: 0.523 m/s
- Velocity North: -0.312 m/s
- Velocity Up: 0.001 m/s
- Bottom Distance: 45.20 m
- Quality: 88%

## Related Documents

- [PNORC - Water Track Velocity](../pnorc/README.md)
- [All Specifications](../README.md)

---

[📋 All Specs](../README.md) | [🏠 Home](../../README.md)
