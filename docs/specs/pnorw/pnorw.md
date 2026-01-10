[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORW Specification

**Wave data message** with wave height, period, and direction measurements.

## Format

```
$PNORW,MMDDYY,HHMMSS,SigWaveHeight,MaxWaveHeight,PeakPeriod,MeanDirection*CHECKSUM
```

**Field Count**: 7fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORW` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Sig. Wave Height | float | DECIMAL(5,2) | meters | 0-30 | Significant wave height (H1/3) |
| 4 | Max Wave Height | float | DECIMAL(5,2) | meters | 0-50 | Maximum wave height |
| 5 | Peak Period | float | DECIMAL(5,1) | seconds | 0-30 | Peak wave period |
| 6 | Mean Direction | float | DECIMAL(5,1) | degrees | 0-360 | Mean wave direction |

## Example Sentence

```
$PNORW,102115,090715,2.50,4.10,8.5,285.0*XX
```

**Parsed**:
- Date: October 21, 2015
- Time: 09:07:15
- Significant Wave Height: 2.50 m
- Max Wave Height: 4.10 m
- Peak Period: 8.5 s
- Mean Direction: 285.0° (from WNW)

## Related Documents

- [PNORWD - Wave Directional Data](../pnorwd/pnorwd.md)
- [All Specifications](../README.md)

---

[📋 All Specs](../README.md) | [🏠 Home](../../README.md)
