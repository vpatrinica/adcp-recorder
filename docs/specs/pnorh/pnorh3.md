[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORH Family](README.md)

# PNORH3 Specification

**Tagged header data** (DF=103) for measurement series with date/time and status information.

## Format

```nmea
$PNORH3,DATE=YYMMDD,TIME=HHMMSS,EC=ErrorCode,SC=StatusCode*CHECKSUM
```

**Field Count**: 5 fields (including prefix)

## Field Definitions

| Tag | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|-----|-------|-------------|-------------|------|--------|-------|-------------|
| - | Prefix | str | VARCHAR(10) | - | "$PNORH3" | - | Always `$PNORH3` |
| DATE | Date | str | CHAR(6) | - | YYMMDD | - | Measurement date |
| TIME | Time | str | CHAR(6) | - | HHMMSS | - | Measurement time |
| EC | Error Code | int | INTEGER | - | N | 0+ | Error status (0=no error) |
| SC | Status Code | str | CHAR(8) | - | hhhhhhhh | - | System status bitfield (hex) |

## Example Sentence

```nmea
$PNORH3,DATE=141112,TIME=081946,EC=0,SC=2A4C0000*5F
```

**Parsed**:

- Date: November 12, 2014 (YYMMDD = 141112)
- Time: 08:19:46
- Error Code: 0 (no error)
- Status Code: 2A4C0000

## Usage

PNORH3 precedes a series of PNORC/PNORS messages:

```nmea
$PNORH3,DATE=141112,TIME=081946,EC=0,SC=2A4C0000*5F    ← Header
$PNORC3,CP=4.5,SP=3.519,DIR=110.9,AC=6,AA=28*3B       ← Cell 1 data
```

## Related Documents

- [PNORH4](pnorh4.md) - Same data, positional format
- [PNORC Family](../pnorc/README.md)
- [PNORS Family](../pnors/README.md)

---

[⬆️ Back to PNORH Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
