# Changelog

## 2026-02-16: Sentinel Tuples Narrowed (customer modification)

### What Changed
Customer removed small-magnitude sentinels (`-9.x`) from multi-digit format tuples.
Only the larger-magnitude sentinels remain. For example `_D3_2` (format `ddd.dd`)
went from `("-9.00", "-9.99", "-99.99", "-999.99", ...)` to just
`("-99.99", "-999.99", "99.99", "999.99")`.

### Rationale
For a format with N integer digits, only sentinels that fill at least 2 digit
positions are considered unambiguous. `-9.00` is a plausible real value for a
`ddd.dd` field, but `-99.99` is not.

### Tuples affected
| Tuple | Format | Removed | Kept |
|-------|--------|---------|------|
| `_D3_1` | `ddd.d` | `-9.0`, `-9.9`, `9.0`, `9.9` | `-99.9`, `-999.9`, `99.9`, `999.9` |
| `_D3_2` | `ddd.dd` | `-9.00`, `-9.99`, `9.00`, `9.99` | `-99.99`, `-999.99`, `99.99`, `999.99` |
| `_D3_3` | `ddd.ddd` | `-9.000`, `-9.999`, `9.000`, `9.999` | `-99.999`, `-999.999`, `99.999`, `999.999` |
| `_D4_1` | `dddd.d` | `-9.0`, `-9.9`, `-99.9`, `9.0`, `9.9`, `99.9` | `-999.9`, `-9999.9`, `999.9`, `9999.9` |
| `_D4_3` | `dddd.ddd` | `-9.000`, `-9.999`, `-99.999`, `9.000`, `9.999`, `99.999` | `-999.999`, `-9999.x`, `999.999`, `9999.x` |
| `_D4_4` | `dddd.dddd` | `-9.0000`, `-9.9999`, `-99.9999`, `9.0000`, `9.9999`, `99.9999` | `-999.9999`, `-9999.9999`, `999.9999`, `9999.9999` |

### Tests updated (10 failures fixed)
- Tests using `-9.00` as sentinel for `ddd.dd` fields → changed to `-99.99`
- Tests using `-9.0000` as sentinel for `dddd.dddd` fields → changed to `-999.9999`
- Files: `test_pnorb.py`, `test_pnorw.py`, `test_pnorf.py`, `test_pnorwd.py`,
  `test_e2e_real_data.py` (6 functions)

## 2026-02-16: Per-Field Sentinel Value Registry

### What Changed
Replaced the hardcoded default `invalid_values` tuple in `parse_optional_float()` and
`parse_optional_int()` with a per-field sentinel registry (`parsers/sentinels.py`).
Each NMEA field now has its own set of sentinel strings derived from its spec format
(number of integer digits + decimal places).

### Why
- **Correctness**: The old code applied the same sentinels to every field regardless of
  format. Fields with format `dd.d` emit `-9.0` as sentinel, but `"-9.0"` was NOT in the
  old default tuple — so sentinels were silently passed through as valid data.
- **Precision**: Fields with format `ddd.dd` should NOT match `"-9.0000"` (4 decimals).
  The old code over-matched some fields and under-matched others.
- **Spec compliance**: Nortek documentation specifies that each field format has
  deterministic sentinel values (every digit position filled with 9).

### Sentinel Pattern
Every digit position in the field format is filled with `9` (or `-9`), preserving decimal
precision. Both negative and positive variants are registered:

| Format | Example sentinels |
|--------|------------------|
| `d.d`  | `-9.0`, `-9.9`, `9.0`, `9.9` |
| `dd.dd`| `-9.00`, `-9.99`, `-99.99`, `9.00`, `9.99`, `99.99` |
| `ddd.dd`| `-9.00`, `-9.99`, `-99.99`, `-999.99`, `9.00`, `9.99`, `99.99`, `999.99` |

### Design Decisions
- **Per-field registry**: Dict mapping `(parser_prefix, field_name)` → sentinel tuple.
  Lookup via `get_float_sentinels("PNORS", "battery")`.
- **Positive sentinels kept**: Values like `999.99` are treated as sentinel/invalid,
  even though the spec only documents negative sentinels explicitly.
- **PNORA pitch/roll**: `-9.0` used as sentinel despite falling within the valid range
  `[-9.9, +9.9]` — user decision to prefer sentinel detection over edge-case accuracy.
- **Integer sentinels**: `parse_optional_int()` also supports sentinels for PNORW/PNORE
  integer fields (`-9`, `-999`, etc.).

### Files Created
- `adcp_recorder/parsers/sentinels.py` — Registry module (~340 lines). Contains
  `FLOAT_SENTINELS` dict (~90 entries), `INT_SENTINELS` dict (3 entries),
  `get_float_sentinels()` and `get_int_sentinels()` lookup functions, and
  format-derived sentinel tuples (`_D1_1` through `_D4_4`, `_INT_WAVE`).

### Files Modified
- `parsers/utils.py` — `parse_optional_float()` and `parse_optional_int()` signatures
  changed: removed old `invalid_values` default, added `sentinels: tuple[str, ...] = ()`
- All 9 parser files wired with sentinels: `pnors.py`, `pnorc.py`, `pnorb.py`,
  `pnorw.py`, `pnore.py`, `pnorf.py`, `pnorwd.py`, `pnora.py`, `pnori.py`
- `pnorh.py` — No changes (no float/sentinel-eligible fields)
- 5 test files updated: `test_utils.py`, `test_global_nan.py`, `test_pnorb.py`,
  `test_pnorb_extended.py`, `test_pnorw.py`

### Parser Wiring Pattern
Each parser file uses this import and call pattern:
```python
from .sentinels import get_float_sentinels as _fs
# (and get_int_sentinels as _is where needed)

_p = "PNORS"  # parser prefix
battery=parse_optional_float(fields[5], _fs(_p, "battery")),

# For list comprehensions:
_ed_sent = _fs(_p, "energy_density")
energies = [parse_optional_float(fields[i], _ed_sent) for i in range(7, len(fields))]
```

### Test Results
934 tests: 933 passed, 1 skipped, 0 failures. ruff + mypy clean.

### Prior Bugs Fixed (same session)
- **`-nan` handling**: Added `is_nan_string()` helper, `parse_optional_int()` helper,
  replaced 40+ inline NaN checks across all parser files.
- **PNORS3 spec doc checksum**: `*7A` in spec is wrong, correct is `*73`.

## 2026-02-16: Comprehensive E2E Parser Test Suite

### What Changed
Created `test_e2e_real_data.py` with 83 tests covering all 21 registered parser types,
using NMEA sentences derived from spec documentation examples and production data.

### Test Results
83 E2E tests all passing. Combined with existing tests: 246 parser tests total.

## 2026-02-16: Quality, Coverage, and Documentation Overhaul (v0.2.5)

### What Changed
Achieved 100% test coverage, enforced strict type checking, and implemented a robust documentation system.

### Why
- **Reliability**: Eliminates potential runtime errors in edge cases (checksum validation failures, DB write errors).
- **Maintainability**: Strict typing (`mypy --check-untyped-defs`) catches bugs early.
- **Developer Experience**: A unified `check_quality` script simplifies local development.
- **Compliance**: Documentation coverage checks ensure the codebase remains self-documenting.

### Key Improvements

#### 1. 100% Test Coverage
- **Closed Gaps**: Added targeted tests for unreachable code and exception handling in `consumer.py` and `utils.py`.
- **Cleanup**: Removed dead code in `pnori.py` (redundant mandatory tag checks).
- **Validation**: Verified full coverage of all core modules.

#### 2. Quality Assurance Infrastructure
- **Unified Script**: Created `scripts/utils/check_quality.py` to run lint, format, type-check, and test commands in one go.
- **Wrappers**: Updated `.bat` and `.sh` scripts to use the unified Python runner.
- **Strict Typing**: Enabled `check_untyped_defs = true` in `pyproject.toml` and fixed 40+ resulting type errors.

#### 3. Documentation System
- **Master Guide**: Created `AGENTS.md` as the single source of truth for agents and developers.
- **Automated Checks**: Added `scripts/check_docs.py` to enforce docstring coverage (>80%).
- **Generation**: Added `scripts/generate_docs.bat` to build API docs using `pdoc`.
- **CI Integration**: Integrated doc checks into GitHub Actions (`code-quality.yml`).

## 2026-02-16: NMEA Parser Standardization

### What Changed
Standardized all NMEA parsers to use the shared `parse_nmea_sentence()` utility 
from `adcp_recorder/parsers/utils.py`, replacing ad-hoc parsing in each parser's 
`from_nmea()` method.

### Why
- **Consistency**: All parsers now handle checksums, field splitting, and validation identically
- **Maintainability**: Common logic lives in one place instead of being duplicated 10 times
- **Correctness**: Checksum validation was inconsistent — some parsers validated, some didn't

### Files Modified

**Core parsers** (all `from_nmea()` methods updated to use `parse_nmea_sentence()`):
- `pnori.py` — Also fixed relative imports, standardized error messages ("Unknown tag" singular)
- `pnorb.py` — Integrated checksum validation
- `pnorc.py` — Integrated checksum validation
- `pnore.py` — Integrated checksum validation
- `pnorf.py` — Integrated checksum validation
- `pnorh.py` — Integrated checksum validation
- `pnors.py` — Corrected copy-paste error
- `pnorw.py` — Integrated checksum validation
- `pnorwd.py` — Integrated checksum validation
- `pnora.py` — Integrated checksum validation

**Shared utilities:**
- `utils.py` — Already had `parse_nmea_sentence()`; no changes needed

**Test files (updated for checksum validation):**
- `test_pnori.py` — Fixed checksum values (2E→1A, 1B→51), error patterns (plural→singular)
- `test_pnorb.py` — Removed `*XX` placeholders, fixed invalid-prefix test
- `test_pnorc.py` — Removed `*XX` from multi-line PNORC2 strings
- `test_pnore.py` — Fixed checksum assertions (00→70, 00→4B), removed f-string checksums
- `test_pnorf.py` — Fixed checksum assertions (00→17), removed f-string/multi-line checksums
- `test_pnorw.py` — Fixed multi-line `*XX`, removed checksum from invalid-prefix test
- `test_pnorwd.py` — Fixed checksum assertions (00→3C, 00→2E), removed f-string checksums
- `test_global_nan.py` — Fixed PNORE date format (MMDDYY→YYMMDD: 102115→211015)

**Tooling:**
- `fix_tests.py` — Rewrote to properly handle multi-line strings, `*XX` placeholders, f-strings

### Breaking Changes
- Parsers now **reject sentences with invalid checksums** (previously ignored).
  Sentences without checksums (no `*`) are still accepted.
- Error message `"Unknown tags: XX"` changed to `"Unknown tag in PNORI2: XX"` (singular, includes context)

### Test Results
163 parser tests pass, 0 failures.
