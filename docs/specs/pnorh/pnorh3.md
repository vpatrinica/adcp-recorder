[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORH Family](README.md)

# PNORH3 Specification

**Header data variant 3** for current velocity measurement series.

## Format

```
$PNORH3,MMDDYY,HHMMSS,NumCells,FirstCell,PingCount*CHECKSUM
```

**Field Count**: 6 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORH3` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement series date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement series time |
| 3 | Number of Cells | int | SMALLINT | - | 1-1000 | Total cells in this series |
| 4 | First Cell | int | SMALLINT | - | 1-1000 | Index of first cell |
| 5 | Ping Count | int | INTEGER | - | 1-10000 | Number of pings averaged |

## Example Sentence

```
$PNORH3,102115,090715,20,1,50*XX
```

**Parsed**:
- Date: October 21, 2015
- Time: 09:07:15
- Number of Cells: 20
- First Cell: 1
- Ping Count: 50

## Usage

PNORH3 precedes a series of PNORC/PNORC1-4 messages:

```
$PNORH3,102115,090715,20,1,50*XX    ← Header
$PNORC,102115,090715,1,...*XX       ← Cell 1 data
$PNORC,102115,090715,2,...*XX       ← Cell 2 data
...
$PNORC,102115,090715,20,...*XX      ← Cell 20 data
```

## Validation Rules

1. Date/time format validation
2. Number of cells: 1-1000
3. First cell: 1 to number of cells
4. Ping count: ≥ 1

## Related Documents

- [PNORH Family Overview](README.md)
- [PNORC Family](../pnorc/README.md)

---

[⬆️ Back to PNORH Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
