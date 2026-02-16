---
description: Run commands with auto-approval for this project
---
// turbo-all

## Running Tests
1. Run all parser tests:
```
uv run pytest adcp_recorder/tests/parsers/ -v
```

2. Run full test suite:
```
uv run pytest
```

3. Run quality checks:
```
scripts\check_quality.bat
```

4. Run fix_tests.py to recompute NMEA checksums in test files:
```
python fix_tests.py
```
