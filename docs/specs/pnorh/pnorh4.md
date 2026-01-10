[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORH Family](README.md)

# PNORH4 Specification

**Header data variant 4** with extended metadata for current velocity measurement series.

## Format

```
$PNORH4,MMDDYY,HHMMSS,NumCells,FirstCell,PingCount,CoordSystem,ProfileInterval*CHECKSUM
```

**Field Count**: 8 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORH4` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement series date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement series time |
| 3 | Number of Cells | int | SMALLINT | - | 1-1000 | Total cells in this series |
| 4 | First Cell | int | SMALLINT | - | 1-1000 | Index of first cell |
| 5 | Ping Count | int | INTEGER | - | 1-10000 | Number of pings averaged |
| 6 | Coordinate System | str | VARCHAR(10) | - | - | ENU, XYZ, or BEAM |
| 7 | Profile Interval | float | DECIMAL(7,1) | seconds | 0.1-3600 | Time between profiles |

## Example Sentence

```
$PNORH4,102115,090715,20,1,50,ENU,60.0*XX
```

**Parsed**:
- Date: October 21, 2015
- Time: 09:07:15
- Number of Cells: 20
- First Cell: 1
- Ping Count: 50
- Coordinate System: ENU
- Profile Interval: 60.0 seconds

## Differences from PNORH3

- **Added**: Coordinate system specification
- **Added**: Profile interval timing
- **Use**: More complete profiling metadata

## Usage

PNORH4 precedes a series of PNORC/PNORC1-4 messages:

```
$PNORH4,102115,090715,20,1,50,ENU,60.0*XX  ← Header
$PNORC3,102115,090715,1,...*XX             ← Cell 1 data
$PNORC3,102115,090715,2,...*XX             ← Cell 2 data
...
$PNORC3,102115,090715,20,...*XX            ← Cell 20 data
```

## Validation Rules

1. Date/time format validation
2. Number of cells: 1-1000
3. First cell: 1 to number of cells
4. Ping count: ≥ 1
5. Coordinate system: ENU, XYZ, or BEAM
6. Profile interval: > 0 seconds

## Related Documents

- [PNORH Family Overview](README.md)
- [PNORH3](pnorh3.md)
- [PNORC Family](../pnorc/README.md)
- [PNORI Configuration](../pnori/README.md)

---

[⬆️ Back to PNORH Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
