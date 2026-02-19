# ADCP Recorder - Agent Guide

This document provides instructions and guidelines for AI agents working on the `adcp-recorder` repository.
It merges project standards with the internal knowledge base found in `.memory/`.

## Project Overview

**ADCP Recorder** is a Python-based NMEA telemetry recorder for Nortek ADCP instruments.
It acts as a robust middleware between serial hardware and data analysis, featuring:
*   **Asynchronous I/O**: Threaded Producer/Consumer pattern for non-blocking serial communication.
*   **DuckDB Backend**: High-performance embedded SQL storage with a consolidated schema.
*   **Resilience**: Automatic connection recovery and graceful error handling.

## Architecture & Data Flow

### Data Flow
```text
Serial Port → consumer.py → Parser.from_nmea(sentence) → Dataclass → .to_dict() → DB/CSV
```
1.  **Serial consumer** reads raw NMEA sentences.
2.  **Parsers** validate and parse sentences into frozen `@dataclass` objects.
3.  **is_valid Field**: Every parsed record includes an `is_valid` boolean (default `True`).
4.  **Database Manager** stores raw lines immediately and parsed data after validation.
5.  **Exporters** write daily CSV/Parquet files.

### Key Design Decisions
*   **Frozen Dataclasses**: All parser outputs are immutable.
*   **is_valid**: Every record must have an `is_valid: bool = True` field.
*   **Optional Fields**: NMEA fields are often optional; use `float | None` and `parse_optional_float()`.
*   **NaN Handling**: Strings like `"nan"`, `"-9.0000"`, or `""` must be converted to `None`.
*   **Checksum Validation**: Centralized in `adcp_recorder.parsers.utils.parse_nmea_sentence()`.

## Development Environment

- **Python**: 3.13+
- **Package Manager**: `uv` (preferred) or `pip`.
- **Key Dependencies**: `pyserial`, `duckdb`, `click`, `pydantic`.

## Build, Lint & Test Commands

### Testing
Tests are located in `adcp_recorder/tests/`. The `conftest.py` fixture `isolate_test_env` protects the host system.

*   **Run all tests**:
    ```bash
    uv run pytest
    # OR
    pytest
    ```
*   **Run with coverage**:
    ```bash
    pytest --cov=adcp_recorder --cov-report=term-missing
    ```

### Checksum Rules for Tests (CRITICAL)
**Never use placeholder checksums like `*XX` in tests.**
1.  **Normal Tests**: Use valid, computed checksums.
2.  **No-Checksum Tests**: Omit the `*CS` entirely to test optional handling.
3.  **Dynamic Values**: If using f-strings with changing data, omit the checksum.
4.  **Fixing Checksums**: Run `python scripts/utils/fix_tests.py` to automatically update checksums in test files.

### Code Quality
The project uses `ruff` for linting/formatting and `mypy` for static analysis. **All checks must pass.**

*   **Lint (Ruff)**:
    ```bash
    ruff check adcp_recorder/
    ```
*   **Format (Ruff)**:
    ```bash
    ruff format adcp_recorder/
    ```
*   **Type Check (MyPy)**:
    ```bash
    mypy adcp_recorder/
    ```
*   **Documentation Check**:
    ```bash
    python scripts/check_docs.py
    ```
*   **Generate Docs**:
    ```bash
    scripts/generate_docs.bat
    ```
*   **Security Scan**:
    ```bash
    safety check
    bandit -r adcp_recorder/
    ```
*   **Full Check Suite**:
    ```bash
    scripts/check_quality.bat
    ```

## Database Schema Strategy

The database uses **DuckDB** with a "Consolidated Schema" approach:
*   **Raw Data**: `raw_lines` table.
*   **Errors**: `Errors` view (aliasing `parse_errors` table).
*   **Consolidation**: Related NMEA sentences (e.g., `PNORS1`, `PNORS2`) map to unified tables (e.g., `pnors12`).
*   **Views**: SQL Views normalize access across NMEA versions.
*   **Migration**: Always update `adcp_recorder/db/schema.py` when changing data structures.

## Documentation System

The project uses a dual approach for documentation:
1.  **Validation**: `scripts/check_docs.py` verifies docstring coverage (currently >80%).
2.  **Generation**: `scripts/generate_docs.bat` uses `pdoc` to build HTML API documentation in `docs/api/`.

## Workflow for Agents

1.  **Analyze**:
    *   Check `.memory/` for architectural context.
    *   Use `grep` to find code.
2.  **Safe Testing**:
    *   Run `pytest` to ensure a clean state.
3.  **Implement**:
    *   Follow the Frozen Dataclass pattern for parsers.
    *   Use `SerialConnectionManager` for comms.
4.  **Verify**:
    *   Run `scripts/check_quality.bat` to run all linters and tests.
    *   **Run `python scripts/utils/fix_tests.py`** if you modified test data to fix checksums.
5.  **Documentation**:
    *   Update docstrings.
    *   If you change architecture, update `.memory/` files.
    *   Run `scripts/generate_docs.bat` to verify documentation builds.
