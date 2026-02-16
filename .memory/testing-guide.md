# Testing Guide

## Philosophy
*   **100% Coverage**: We aim for very high coverage (currently ~99.9%).
*   **Strict Typing**: Tests must pass mypy checks.
*   **Linting**: Tests must pass ruff checks.
*   **Isolation**: Use `isolate_test_env` fixture to avoid side effects.

## Common Patterns

### Mocking Database
Use `DatabaseManager(":memory:")` for fast, isolated database tests.

```python
def test_db_insert():
    db = DatabaseManager(":memory:")
    conn = db.get_connection()
    # ...
```

### Mocking Serial
Use `unittest.mock.patch` to mock `pyserial` or `SerialConnectionManager`.

### Coverage Gaps
If you find coverage gaps:
1.  **Analyze**: Is the code reachable? If not, remove it (Dead Code).
2.  **Test**: Write a targeted test case in the appropriate test file.
3.  **Lint**: Ensure the new test passes `ruff check` and `ruff format`.

## Checksums in Tests
See `nmea-checksum.md`. **Do not manually compute checksums.**
1.  Write test with `*XX`.
2.  Run `python scripts/utils/fix_tests.py`.

## Sentinel Values in Tests

When testing that sentinel values are correctly detected as `None`:

1.  **Use the correct format** for each field. PNORB/PNORW wave fields use `ddd.dd`
    format, so the sentinel is `"-99.99"` or `"-999.99"` — NOT `"-9.00"` or `"-9.0000"`.
    PNORF/PNORWD use `dddd.dddd`, so sentinels are `"-999.9999"` or `"-9999.9999"`.
2.  **Check `parsers/sentinels.py`** to find the exact sentinel tuple for a field.
3.  **`parse_optional_float()` without sentinels** now returns the float value (not `None`).
    If you call it bare (no sentinels arg), only `""`, `"nan"`, and unparseable strings
    return `None`.
4.  **Positive sentinels are active**: `"999.99"` is a sentinel for `ddd.dd` fields.
    Don't use it as a "max valid value" in tests — use `998.99` instead.
5.  **Integer sentinels**: PNORW/PNORE integer fields have sentinels too (`"-9"`, `"-999"`).
    Pass them via `parse_optional_int(value, get_int_sentinels(prefix, field))`.

## Running Quality Checks
Use the unified script:
```bash
scripts/check_quality.bat
```
This runs:
1.  Ruff Format
2.  Ruff Lint
3.  Mypy (Strict)
4.  Pytest (with Coverage)
