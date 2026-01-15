[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORH Family](README.md)

# PNORH4 Specification

**Positional header data** (DF=104) for measurement series with date/time and status information.

## Format

```nmea
$PNORH4,YYMMDD,HHMMSS,ErrorCode,StatusCode*CHECKSUM
```

**Field Count**: 5 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|----------|-------|-------------|-------------|------|--------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | "$PNORH4" | - | Always `$PNORH4` |
| 1 | Date | str | CHAR(6) | - | YYMMDD | - | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | - | Measurement time |
| 3 | Error Code | int | INTEGER | - | N | 0+ | Error status (0=no error) |
| 4 | Status Code | str | CHAR(8) | - | hhhhhhhh | - | System status bitfield (hex) |

## Example Sentence

```nmea
$PNORH4,141112,083149,0,2A4C0000*4A68
```

**Parsed**:

- Date: November 12, 2014 (YYMMDD = 141112)
- Time: 08:31:49
- Error Code: 0 (no error)
- Status Code: 2A4C0000

## Usage

PNORH4 precedes a series of PNORC/PNORS messages:

```nmea
$PNORH4,141112,083149,0,2A4C0000*4A68    ← Header
$PNORC4,27.5,1.815,322.6,4,28*70         ← Cell 1 data
```

## Related Documents

- [PNORH3](pnorh3.md) - Same data, tagged format
- [PNORC Family](../pnorc/README.md)
- [PNORS Family](../pnors/README.md)

---

[⬆️ Back to PNORH Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
