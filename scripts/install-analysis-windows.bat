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
echo(

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
where servy-cli >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Servy CLI not found.
    echo Please ensure Servy is installed: winget install -e --id aelassas.Servy
    pause
    exit /b 1
)

echo [1/3] Installing analysis dependencies...
"%INSTALL_DIR%\venv\Scripts\pip.exe" install --quiet "adcp-recorder[analysis]"
if %errorLevel% neq 0 (
    echo ERROR: Failed to install analysis dependencies.
    pause
    exit /b 1
)
echo Analysis dependencies installed.
echo(

echo [2/3] Installing ADCP API Service...
set "API_PARAMS=adcp_recorder.api.main:app --host 0.0.0.0 --port 8000"
servy-cli install --quiet --name="ADCP-API" --displayName="ADCP Recorder API" --description="REST API for ADCP Recorder data access" --path="%INSTALL_DIR%\venv\Scripts\uvicorn.exe" --startupDir="%INSTALL_DIR%" --params="!API_PARAMS!" --startupType="Automatic" --stdout="%LOG_DIR%\api_stdout.log" --stderr="%LOG_DIR%\api_stderr.log" --enableDateRotation --dateRotationType="Daily"

if %errorLevel% equ 0 (
    echo API Service installed successfully.
    servy-cli start --name="ADCP-API" --quiet
    echo API Service started on port 8000.
) else (
    echo WARNING: API Service installation failed.
)

echo(
echo [3/3] Installing ADCP Dashboard Service...
REM Get the site-packages path for the dashboard module
for /f "delims=" %%i in ('"%INSTALL_DIR%\venv\Scripts\python.exe" -c "import adcp_recorder.ui.dashboard as d; print(d.__file__)"') do set DASH_PATH=%%i
REM Disable telemetry prompt that blocks service startup
set "DASH_PARAMS=run \"!DASH_PATH!\" --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats false --server.headless true"
servy-cli install --quiet --name="ADCP-Dashboard" --displayName="ADCP Recorder Dashboard" --description="Interactive Streamlit dashboard for ADCP analysis" --path="%INSTALL_DIR%\venv\Scripts\streamlit.exe" --startupDir="%INSTALL_DIR%" --params="!DASH_PARAMS!" --startupType="Automatic" --stdout="%LOG_DIR%\dashboard_stdout.log" --stderr="%LOG_DIR%\dashboard_stderr.log" --enableDateRotation --dateRotationType="Daily"

if %errorLevel% equ 0 (
    echo Dashboard Service installed successfully.
    servy-cli start --name="ADCP-Dashboard" --quiet
    echo Dashboard Service started on port 8501.
) else (
    echo WARNING: Dashboard Service installation failed.
)

echo(
echo ========================================
echo Setup Complete!
echo ========================================
echo API:       http://localhost:8000
echo Dashboard: http://localhost:8501
echo(
pause
