@echo off
setlocal

cd /d "%~dp0.."

if exist .venv\Scripts\activate.bat (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
)

python scripts\utils\check_quality.py
if %errorlevel% neq 0 exit /b %errorlevel%

