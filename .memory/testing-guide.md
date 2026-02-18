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
    format, so the sentinel is `"-99.0"` or `"-999.0"` or `"-9.00"` or `"-9"`.
    PNORF/PNORWD use `dddd.dddd`, so sentinels are `"-99.0"` or `"-999.0"` or `"-9.00"` or `"-9"` or `"-9999.0"`.
3.  **`parse_optional_float()`** takes care of the invalid floats, only `""`, `"nan"`, and unparseable strings return `None`.
4.  **Integer sentinels**: PNORW/PNORE integer fields have sentinels too (`"-9"`, `"-99"`, `"-999"`).
    The parser already takes them into account `parse_optional_int(value)`.

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

## UI Component Testing Patterns

UI tests mock Streamlit and Plotly to test rendering logic without a browser.

### Standard Setup
```python
pytest.importorskip("plotly")
pytest.importorskip("streamlit")

from adcp_recorder.ui.components.wave_rose import render_wave_rose
```

### Mocking Streamlit
Patch `st` at the component's module path:
```python
with patch("adcp_recorder.ui.components.wave_rose.st") as mock_st:
    mock_st.session_state = {}
    mock_st.columns.return_value = [MagicMock(), MagicMock()]
```

### Mocking DataLayer
Use a plain `MagicMock()` — no real DuckDB needed:
```python
mock_data_layer = MagicMock()
mock_data_layer.query_wave_rose_data.return_value = [...]
render_wave_rose(mock_data_layer)
```

### Mocking Auto-Detection
Components using `detect_current_profile_view()` need it mocked on the data layer:
```python
mock_data_layer.detect_current_profile_view.return_value = "current_profile_12"
```

### Mocking Local Imports
When a function uses a local import (e.g., `from adcp_recorder.ui.config import
DashboardConfig` inside `_render_save_panel_ui`), patch at the **source module**,
not the importing module:
```python
@patch("adcp_recorder.ui.config.DashboardConfig")  # correct
# NOT: @patch("adcp_recorder.ui.pages.plot_builder.DashboardConfig")
```

### Testing Plot Builder Save Logic
Mock `st.button.return_value = True` and `st.selectbox.side_effect = [...]` to
simulate user interactions through the full `render_plot_builder()` flow:
```python
mock_st.selectbox.side_effect = ["Wave Rose", "test_dashboard"]
mock_dc.list_dashboards.return_value = ["test_dashboard"]
```
