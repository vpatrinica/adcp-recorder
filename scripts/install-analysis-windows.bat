@echo off
REM
REM install-analysis-windows.bat - Install ADCP Analysis Platform on Windows
REM
REM This script installs the FastAPI and Streamlit components as Windows services using Servy.
REM Run as Administrator.
REM

setlocal enabledelayedexpansion

echo ========================================
echo ADCP Analysis Platform - Windows Setup
echo ========================================
echo.

REM Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator.
    pause
    exit /b 1
)

set INSTALL_DIR=C:\Program Files\ADCP-Recorder
set DATA_DIR=C:\ADCP_Data
set LOG_DIR=%DATA_DIR%\logs

if not exist "%INSTALL_DIR%\venv" (
    echo ERROR: ADCP Recorder must be installed first.
    echo Please run scripts\install-windows.bat first.
    pause
    exit /b 1
)

REM Verify Servy is installed
servy-cli --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Servy CLI not found. 
    echo Please ensure Servy is installed (winget install -e --id aelassas.Servy).
    pause
    exit /b 1
)

echo [1/2] Installing ADCP API Service...
servy-cli install --quiet ^
    --name="ADCP-API" ^
    --displayName="ADCP Recorder API" ^
    --description="REST API for ADCP Recorder data access" ^
    --path="%INSTALL_DIR%\venv\Scripts\uvicorn.exe" ^
    --startupDir="%INSTALL_DIR%" ^
    --params="adcp_recorder.api.main:app --host 0.0.0.0 --port 8000" ^
    --startupType="Automatic" ^
    --stdout="%LOG_DIR%\api_stdout.log" ^
    --stderr="%LOG_DIR%\api_stderr.log" ^
    --enableDateRotation --dateRotationType="Daily"

if %errorLevel% equ 0 (
    echo API Service installed successfully.
    servy-cli start --name="ADCP-API" --quiet
    echo API Service started on port 8000.
) else (
    echo WARNING: API Service installation failed.
)

echo.
echo [2/2] Installing ADCP Dashboard Service...
servy-cli install --quiet ^
    --name="ADCP-Dashboard" ^
    --displayName="ADCP Recorder Dashboard" ^
    --description="Interactive Streamlit dashboard for ADCP analysis" ^
    --path="%INSTALL_DIR%\venv\Scripts\streamlit.exe" ^
    --startupDir="%INSTALL_DIR%" ^
    --params="run adcp_recorder/ui/dashboard.py --server.port 8501 --server.address 0.0.0.0" ^
    --startupType="Automatic" ^
    --stdout="%LOG_DIR%\dashboard_stdout.log" ^
    --stderr="%LOG_DIR%\dashboard_stderr.log" ^
    --enableDateRotation --dateRotationType="Daily"

if %errorLevel% equ 0 (
    echo Dashboard Service installed successfully.
    servy-cli start --name="ADCP-Dashboard" --quiet
    echo Dashboard Service started on port 8501.
) else (
    echo WARNING: Dashboard Service installation failed.
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo API:       http://localhost:8000
echo Dashboard: http://localhost:8501
echo.
pause
