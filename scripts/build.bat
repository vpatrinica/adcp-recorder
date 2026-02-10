@echo off
setlocal enabledelayedexpansion

echo ========================================
echo ADCP Recorder - Build Script (Windows)
echo ========================================
echo.

cd /d "%~dp0.."

if exist .venv\Scripts\activate.bat (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo [1/8] Cleaning previous builds...
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist *.egg-info rd /s /q *.egg-info
if exist adcp_recorder.egg-info rd /s /q adcp_recorder.egg-info
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo Done.
echo.

echo [2/8] Checking Python version...
uv run python --version
if %errorlevel% neq 0 (
    echo X uv/python check failed.
    exit /b 1
)
uv run python -c "import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)"
if %errorlevel% neq 0 (
    echo X Python 3.13+ is required.
    exit /b 1
)
echo Done.
echo.

echo [3/8] Synchronizing dependencies...
uv sync --all-extras
if %errorlevel% neq 0 (
    echo [WARNING] uv sync failed. This is often due to the application being running.
    echo Trying to proceed with existing environment...
) else (
    echo Done.
)
echo.

echo [4/8] Running quality checks...
call scripts\check_quality.bat
if %errorlevel% neq 0 (
    echo X Quality checks failed.
    exit /b 1
)
echo Done.
echo.

echo [5/8] Running test suite...
if exist adcp_recorder\tests (
    uv run pytest adcp_recorder/tests -v --tb=short
    if %errorlevel% neq 0 (
        echo X Tests failed.
        exit /b 1
    )
    echo Done.
) else (
    echo ! No tests directory found, skipping.
)
echo.

echo [6/8] Building distributions...
uv run python -m build
if %errorlevel% neq 0 (
    echo X Build failed.
    exit /b 1
)
echo Done.
echo.

echo [7/8] Verifying package integrity...
for %%f in (dist\*.whl) do (
    uv run pip install --quiet --force-reinstall "%%f"
)
uv run python -c "import adcp_recorder; print(f'Package version: {adcp_recorder.__version__}')" 2>nul
uv run python -c "from adcp_recorder.cli.main import cli; print('CLI import: OK')"
echo Done.
echo.

echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Build artifacts in dist/
dir dist /b
echo.
echo To install: pip install dist\adcp_recorder-*.whl
echo.
