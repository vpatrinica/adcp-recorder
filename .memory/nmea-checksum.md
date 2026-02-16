# NMEA Checksum Reference

## How NMEA Checksums Work

An NMEA checksum is a two-character hex value appended after `*` at the end of a sentence.
It's computed by XOR-ing all ASCII characters between `$` and `*` (exclusive of both).

```
$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*1A
 ^--- XOR these characters ---^                ^^
                                                checksum
```

### Core Functions (`adcp_recorder/core/nmea.py`)

```python
compute_checksum("$PNORI,4,Test,4,20,0.20,1.00,0")
# Returns: "51"

validate_checksum("$PNORI,4,Test,4,20,0.20,1.00,0*51")
# Returns: True
```

## How Checksum Validation Works in Parsers

All parsers call `parse_nmea_sentence()` which:
1. If `*` is present → validates checksum, raises `ValueError` if invalid
2. If `*` is absent → skips validation (checksum is optional)

This means:

| Input | Behavior |
|-------|----------|
| `$PNORI,...*1A` | ✅ Validates, checksum=`"1A"` |
| `$PNORI,...*XX` | ❌ Raises `ValueError("Invalid NMEA checksum")` |
| `$PNORI,...` | ✅ Skips validation, checksum=`None` |

## fix_tests.py — Checksum Fixing Tool

Run `python scripts/utils/fix_tests.py` from the project root to auto-fix checksums in test files.

### What it does
- Finds NMEA sentences in test files (quoted strings starting with `$PNOR`)
- Recomputes correct checksums and replaces existing ones
- Handles both single-line and multi-line concatenated strings
- Skips f-strings with dynamic expressions (can't pre-compute)

### When to use it
- After manually editing NMEA test data
- After changing parser field counts or formats

### Known Limitations
1. **Cannot fix f-strings** with `{variables}` — the checksum depends on runtime values.
   Solution: omit the checksum from f-string test data.
2. **Multi-line strings with 3+ parts** may not be caught by the regex.
   Solution: join concatenated strings to fewer parts, or omit checksum.
3. **Test sentences with intentionally wrong prefixes** (e.g., `$NOTRB,...*XX`):
   remove the checksum so the prefix error triggers before checksum validation.

### Common Pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| `Invalid NMEA checksum` in tests | Wrong or `*XX` placeholder checksum | Run `fix_tests.py` or remove checksum |
| `Invalid prefix` test fails | Checksum validated before prefix check | Remove checksum from wrong-prefix sentence |
| f-string test has wrong checksum | Checksum depends on loop variable | Remove `*XX` from f-string |
| Assertion `assert checksum == "00"` fails | Old code didn't validate checksum | Update assertion to actual computed value |
