# Changelog

## 2026-02-19: Implementation of `is_valid` and Quality Metrics Overhaul

### What Changed
- Implemented `is_valid: bool = True` field across all ADCP recorder parsers.
- Updated database schema with an `Errors` view (aliasing `parse_errors`).
- Enhanced `DataLayer.get_quality_metrics()` to differentiate between "Parse Errors" and "Invalid Data".
- Updated Dashboad UI (**Data Explorer**) to display comprehensive quality statistics.

### Why
- **Data Integrity**: Differentiates between records that failed NMEA parsing vs. those that failed data validation rules.
- **UI Consistency**: Unifies error tracking under a more user-friendly "Errors" name.
- **Improved Monitoring**: Allows users to quickly assess the health of the data stream.

### Key Changes
- **Parser Standards**: every parsed dataclass now includes `is_valid`.
- **Schema Evolution**: `adcp_recorder/db/schema.py` now includes the `Errors` view and `is_valid` columns.
- **UI Refinement**: "Quick Action" buttons now route to the unified `Errors` view.

### Files Modified
- `adcp_recorder/parsers/*.py` — Added `is_valid` field and updated `to_dict()`.
- `adcp_recorder/db/schema.py` — Added `Errors` view.
- `adcp_recorder/ui/data_layer.py` — Improved `get_quality_metrics`.
- `adcp_recorder/ui/dashboard.py` — Updated quick actions.
- `adcp_recorder/ui/pages/data_explorer.py` — Updated quality overview display.

### Test Results
129 parser tests passed. UI regressions resolved after manual fixes.

## 2026-02-17: Soft Validation - No More Record Dropping

### What Changed
Changed validation behavior from "raise error, drop record" to "validate and store anyway".
Records with out-of-range or invalid values are now stored with their raw values intact.
The `is_valid` flag in the database can be used to filter invalid records downstream.

### Why
- **Data Preservation**: Invalid data is better than missing data - users can inspect and decide.
- **Downstream Processing**: ETL pipelines can apply their own validation rules.
- **Debugging**: Easier to diagnose sensor issues when all data is available.

### Key Changes

#### 1. `validate_range()` No Longer Raises
- Changed `validate_range()` from `-> None` (raise on invalid) to `-> bool` (return True/False).
- Callers can now check the return value instead of catching exceptions.
- Out-of-range values are stored as-is.

#### 2. Removed Sentinel-to-None Conversion
- `parse_optional_float()` and `parse_optional_int()` no longer convert sentinel values to `None`.
- Sentinels like `-9.0`, `-999.0` are now stored as their float values.
- Only `"nan"`, `""`, and unparseable strings become `None`.

#### 3. Validation Helpers Return Bool
- `_validate_battery()`, `_validate_sound_speed()`, `_validate_heading()`, etc. in `pnors.py`
  now return `bool` instead of raising `ValueError`.

#### 4. Updated Tests
- 50+ tests updated to expect stored values instead of `None` for sentinels.
- Database constraint tests updated: constraints no longer enforced by code.
- All validation tests updated: no more `pytest.raises(ValueError, match="out of range")`.

### Files Modified
- `adcp_recorder/parsers/utils.py` — `validate_range()` returns bool
- `adcp_recorder/parsers/pnors.py` — All `_validate_*` helpers return bool
- `adcp_recorder/parsers/pnorb.py`, `pnorw.py` — Import sort fixes
- 15+ test files — Updated expectations for soft validation

### Breaking Changes
- Validation errors no longer raise exceptions; values are stored anyway.
- Database CHECK constraints may still reject values at the DB level (unchanged).

### Test Results
1084 passed, 1 skipped. Coverage: 99.47%.

## 2026-02-16: Dashboard Visualization Rework (auto-detect + plot builder)

### What Changed
Reworked the Streamlit visualization dashboard to remove free-form source selection,
replace manual burst selection with automated detection, and add 4 new plot types to
the plot builder.

### Why
- **Usability**: Users should not need to know DuckDB table names to create plots.
- **Correctness**: Each plot type has a fixed, known data source based on the schema.
- **Consistency**: Parquet and DuckDB backends must produce identical visualizations.

### Key Changes

#### 1. Auto-Detection of Current Profile Views
Added `DataLayer.detect_current_profile_view()` method that checks views in priority
order and returns the first with data:
`current_profile_12 > current_profile_df100 > current_profile_34 > pnorc12 > pnorc_df100 > pnorc34`

Updated 4 components to use auto-detect instead of `config.get("data_source", ...)`:
- `velocity_profile.py` — Removed `st.selectbox("Data Source", ...)`
- `current_profile_plots.py` — Both `render_current_speed_heatmap()` and `render_current_direction_polar()`
- `spectrum_plots.py` — `render_amplitude_heatmap()`

#### 2. Plot Builder Expansion
Added 4 new plot types to `pages/plot_builder.py`:
- Wave Rose (`PanelType.WAVE_ROSE`)
- Current Speed Heatmap (`PanelType.CURRENT_SPEED_HEATMAP`)
- Current Direction Polar (`PanelType.CURRENT_DIRECTION_POLAR`)
- Amplitude Heatmap (`PanelType.AMPLITUDE_HEATMAP`)

Each has: builder function, description, dispatch entry, and save-panel handler.

#### 3. Config Cleanup
Marked `data_source` fields in panel configs as "Ignored (auto-detected)" for
backward YAML compatibility. Removed `data_source` from default dashboard templates.

### Files Modified
- `ui/data_layer.py` — Added `detect_current_profile_view()`
- `ui/components/velocity_profile.py` — Auto-detect, removed source selectbox
- `ui/components/current_profile_plots.py` — Auto-detect for both render functions
- `ui/components/spectrum_plots.py` — Auto-detect for amplitude heatmap
- `ui/config.py` — Updated docstrings, removed dead `data_source` from templates
- `ui/pages/plot_builder.py` — 4 new plot types + builders + save handlers

### Files Created
- `tests/ui/test_plot_builder.py` — 20 tests (descriptions, builders, dispatch, save)

### Tests Updated
- `tests/ui/test_spectrum_plots.py` — Fixed amplitude heatmap tests for auto-detect
- `tests/ui/test_velocity_profile.py` — Rewrote source selection test
- `tests/ui/test_data_layer_extended.py` — Added 7 `detect_current_profile_view` tests,
  fixed pre-existing E501 lint error

### Test Results
1002 passed, 1 skipped, 0 failures. ruff + format clean.

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

## 2026-02-17: Parquet DataLayer improvements and agent policy

### What Changed
- Improved `ParquetDataLayer.resolve_source_name()` to robustly map DuckDB-style
  and user-supplied source names to `pq_...` views, preserving numeric suffixes
  (e.g., `pnors1` -> `pq_pnors1`) and preferring exact suffix matches when present.
- Added fallback heuristics to match legacy patterns like `pnorc12` and
  'pnorwdata_something'.

### Why
- UI components and tests expect `_1` and numbered parquet view names to be
  resolvable; previous implementation sometimes returned the base type only
  (losing suffixes) which caused mismatches and test failures.

### Files Modified
- `adcp_recorder/ui/parquet_data_layer.py` — improved `resolve_source_name()`

### Notes for Agents
- Agents must always update `.memory/*` when making behavior changes so the
  knowledge base stays in sync. This commit includes the changelog entry.

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
