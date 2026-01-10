[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORE Specification

**Echo intensity data message** with acoustic backscatter measurements.

## Format

```
$PNORE,MMDDYY,HHMMSS,CellIndex,Echo1,Echo2,Echo3,Echo4*CHECKSUM
```

**Field Count**: 8 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORE` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Cell Index | int | SMALLINT | - | 1-1000 | Measurement cell number |
| 4 | Echo Beam 1 | int | TINYINT | counts | 0-255 | Echo intensity from beam 1 |
| 5 | Echo Beam 2 | int | TINYINT | counts | 0-255 | Echo intensity from beam 2 |
| 6 | Echo Beam 3 | int | TINYINT | counts | 0-255 | Echo intensity from beam 3 |
| 7 | Echo Beam 4 | int | TINYINT | counts | 0-255 | Echo intensity from beam 4 (if present) |

## Example Sentence

```
$PNORE,102115,090715,1,145,152,148,150*XX
```

**Parsed**:
- Date: October 21, 2015
- Time: 09:07:15
- Cell Index: 1
- Echo intensities: 145, 152, 148, 150 counts

## Usage

Echo intensity data is useful for:
- Detecting suspended sediment
- Identifying particle concentrations
- Quality assessment of velocity data
- Oceanographic research

## Related Documents

- [PNORC - Current Velocity](../pnorc/README.md)
- [All Specifications](../README.md)

---

[📋 All Specs](../README.md) | [🏠 Home](../../README.md)
