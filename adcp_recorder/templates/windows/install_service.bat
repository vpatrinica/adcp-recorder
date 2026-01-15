@echo off
REM ADCP Recorder - Windows Service Installation Script using Servy
REM
REM This script installs the ADCP Recorder as a Windows service using Servy.
REM Run as Administrator.
REM
REM Prerequisites:
REM   - Python 3.13+ installed
REM   - ADCP Recorder installed in a virtual environment
REM   - Servy installed (winget install -e --id aelassas.Servy)
REM

setlocal enabledelayedexpansion

echo ========================================
echo ADCP Recorder - Windows Service Setup
echo (Using Servy Service Manager)
echo ========================================
echo.

REM Configuration - Modify these paths as needed
set INSTALL_DIR=C:\Program Files\ADCP-Recorder
set DATA_DIR=C:\ADCP_Data
set LOG_DIR=%DATA_DIR%\logs
set SERVICE_NAME=ADCPRecorder

REM Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires Administrator privileges
    echo Please run as Administrator
    pause
    exit /b 1
)

REM Check if Servy is installed
servy-cli --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Servy CLI not found
    echo Please install Servy first: winget install -e --id aelassas.Servy
    pause
    exit /b 1
)

REM Check if Python is available
if not exist "%INSTALL_DIR%\venv\Scripts\python.exe" (
    echo ERROR: Python not found at %INSTALL_DIR%\venv\Scripts\python.exe
    echo Please run the main install script first.
    pause
    exit /b 1
)

REM Create log directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Remove existing service if present
echo Checking for existing service...
servy-cli status --name="%SERVICE_NAME%" --quiet >nul 2>&1
if %errorLevel% equ 0 (
    echo Removing existing service...
    servy-cli stop --name="%SERVICE_NAME%" --quiet >nul 2>&1
    timeout /t 2 /nobreak >nul
    servy-cli uninstall --name="%SERVICE_NAME%" --quiet
    timeout /t 2 /nobreak >nul
)

REM Install service via Servy
echo Installing ADCP Recorder service via Servy...
servy-cli install --quiet ^
    --name="%SERVICE_NAME%" ^
    --displayName="ADCP Recorder Service" ^
    --description="NMEA Telemetry Recorder for Nortek ADCP Instruments" ^
    --path="%INSTALL_DIR%\venv\Scripts\python.exe" ^
    --startupDir="%INSTALL_DIR%" ^
    --params="-m adcp_recorder.service.supervisor" ^
    --startupType="Automatic" ^
    --priority="Normal" ^
    --stdout="%LOG_DIR%\stdout.log" ^
    --stderr="%LOG_DIR%\stderr.log" ^
    --enableDateRotation ^
    --dateRotationType="Daily" ^
    --maxRotations=30 ^
    --enableHealth ^
    --heartbeatInterval=30 ^
    --maxFailedChecks=3 ^
    --recoveryAction="RestartService" ^
    --maxRestartAttempts=5 ^
    --stopTimeout=10

if %errorLevel% neq 0 (
    echo ERROR: Service installation failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Service installed successfully!
echo ========================================
echo.
echo Service Management:
echo   Start:    servy-cli start --name="%SERVICE_NAME%"
echo   Stop:     servy-cli stop --name="%SERVICE_NAME%"
echo   Status:   servy-cli status --name="%SERVICE_NAME%"
echo   Restart:  servy-cli restart --name="%SERVICE_NAME%"
echo.
echo Log files:
echo   stdout:   %LOG_DIR%\stdout.log
echo   stderr:   %LOG_DIR%\stderr.log
echo.

set /p START_NOW="Start service now? (Y/N): "
if /i "%START_NOW%"=="Y" (
    servy-cli start --name="%SERVICE_NAME%" --quiet
    echo Service started
)
echo.
pause
