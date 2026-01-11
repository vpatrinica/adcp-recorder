[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORH Family](README.md)

# PNORH3 Specification

**Header data variant 3** with tags for current velocity measurement series.

## Format

```
$PNORH3,DATE=YYMMDD,TIME=HHMMSS,EC=ErrorCode,SC=StatusCode*CHECKSUM
```

**Field Count**: 5 fields (including prefix)

## Field Definitions

| Position | Field | Tag | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-----|-------------|-------------|------|-------|-------------|
| 0 | Prefix | - | str | VARCHAR(10) | - | - | Always `$PNORH3` |
| 1 | Date | DATE | str | CHAR(6) | - | YYMMDD | Measurement date |
| 2 | Time | TIME | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Error Code | EC | int | INTEGER | - | - | Error status code (0=no error) |
| 4 | Status Code | SC | str | CHAR(8) | - | 8 hex digits | System status bitfield |

## Example Sentence

```
$PNORH3,DATE=141112,TIME=081946,EC=0,SC=2A4C0000*5F
```

**Parsed**:
- Date: November 12, 2014
- Time: 08:19:46
- Error Code: 0
- Status Code: 2A4C0000

## Usage

PNORH3 precedes a series of PNORC/PNORC1-4 messages:

```
$PNORH3,DATE=141112,TIME=081946,EC=0,SC=2A4C0000*5F    ← Header
$PNORC,141112,081946,1,...*XX                         ← Cell 1 data
$PNORC,141112,081946,2,...*XX                         ← Cell 2 data
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
