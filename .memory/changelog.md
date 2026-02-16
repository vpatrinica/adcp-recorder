# Changelog

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
