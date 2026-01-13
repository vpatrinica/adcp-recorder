# Ruff Quality Report - 2026-01-13

## Summary
The `adcp-recorder` project has undergone a comprehensive linting and formatting cleanup and has been migrated to Python 3.13+. All 271 logic errors and style discrepancies were resolved.

## Quality Metrics

| Check | Result |
|-------|--------|
| `ruff check` | PASSED (0 errors) |
| `ruff format --check` | PASSED (75 files formatted) |
| `pytest` | PASSED (367 / 367) |
| **Min. Python** | **3.13** |

## Changes Overview

### Automated Cleanup
- Standardized typing annotations (`typing.Dict` -> `dict`, etc.)
- Removed unused imports
- Applied project-wide formatting via `ruff format`

### Manual Interventions
- Refactored complex SQL queries in `db/operations.py` for readability and length
- Adjusted test data in the test suite to comply with line length limits
- Suppressed framework-required naming violations in Windows Service modules
- Fixed logic in `SerialConsumer` for mock-compatible binary logging

---
