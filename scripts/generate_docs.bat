@echo off
setlocal

cd /d "%~dp0.."

if exist .venv\Scripts\activate.bat (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo Generating API documentation...
uv run pdoc -o docs/api adcp_recorder.core adcp_recorder.db adcp_recorder.parsers adcp_recorder.serial adcp_recorder.export adcp_recorder.cli adcp_recorder.service adcp_recorder.config
if %errorlevel% neq 0 (
    echo [ERROR] Failed to generate documentation.
    exit /b %errorlevel%
)

echo [SUCCESS] Documentation generated in docs/api/
