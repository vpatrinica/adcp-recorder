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
