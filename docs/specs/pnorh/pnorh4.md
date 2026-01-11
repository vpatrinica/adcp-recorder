[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORH Family](README.md)

# PNORH4 Specification

**Header data variant 4** (positional) for current velocity measurement series.

## Format

```
$PNORH4,YYMMDD,HHMMSS,ErrorCode,StatusCode*CHECKSUM
```

**Field Count**: 5 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORH4` |
| 1 | Date | str | CHAR(6) | - | YYMMDD | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Error Code | int | INTEGER | - | - | Error status code (0=no error) |
| 4 | Status Code | str | CHAR(8) | - | 8 hex digits | System status bitfield |

## Example Sentence

```
$PNORH4,141112,083149,0,2A4C0000*4A
```

**Parsed**:
- Date: November 12, 2014
- Time: 08:31:49
- Error Code: 0
- Status Code: 2A4C0000

## Usage

PNORH4 precedes a series of PNORC/PNORC1-4 messages:

```
$PNORH4,141112,083149,0,2A4C0000*4A    ← Header
$PNORC,141112,083149,1,...*XX         ← Cell 1 data
```

## Validation Rules

1. Date/time format validation
2. Status code: Must be 8-digit hexadecimal
3. Error code: Integer value (0 or higher)

## Related Documents

- [PNORH Family Overview](README.md)
- [PNORC Family Overview](../pnorc/README.md)

---

[⬆️ Back to PNORH Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
