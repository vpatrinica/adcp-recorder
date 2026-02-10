@echo off
setlocal

cd /d "%~dp0.."

if exist .venv\Scripts\activate.bat (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo Running Ruff Format Check...
uv run ruff format --check adcp_recorder/
if %errorlevel% neq 0 exit /b %errorlevel%

echo Running Ruff Lint Check...
uv run ruff check adcp_recorder/
if %errorlevel% neq 0 exit /b %errorlevel%

echo Running Mypy Check...
uv run mypy adcp_recorder/ --check-untyped-defs
if %errorlevel% neq 0 exit /b %errorlevel%

echo Running Tests and Coverage...
uv run pytest --cov=adcp_recorder --cov-fail-under=100 --cov-report=html --cov-report=term-missing adcp_recorder/tests/
if %errorlevel% neq 0 exit /b %errorlevel%

echo All checks passed!
