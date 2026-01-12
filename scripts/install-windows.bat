@echo off
REM
REM install-windows.bat - Install ADCP Recorder on Windows
REM
REM This script installs ADCP Recorder and optionally sets up Windows service.
REM Run as Administrator for service installation.
REM

setlocal enabledelayedexpansion

echo ========================================
echo ADCP Recorder - Windows Installation
echo ========================================
echo.

REM Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Not running as Administrator
    echo Service installation will be skipped
    echo.
    set ADMIN=0
) else (
    echo Running as Administrator
    set ADMIN=1
    echo.
)

REM Step 1: Check Python installation
echo [1/8] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python not found
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%
echo.

REM Step 2: Set installation directories
echo [2/8] Setting up directories...
set INSTALL_DIR=C:\Program Files\ADCP-Recorder
set DATA_DIR=C:\ADCP_Data
set CONFIG_DIR=%PROGRAMDATA%\ADCP-Recorder

echo Installation directory: %INSTALL_DIR%
echo Data directory: %DATA_DIR%
echo Configuration directory: %CONFIG_DIR%
echo.

REM Create directories
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
echo Directories created
echo.

REM Step 3: Create virtual environment
echo [3/8] Creating virtual environment...
if exist "%INSTALL_DIR%\venv" (
    echo Removing existing virtual environment...
    rmdir /s /q "%INSTALL_DIR%\venv"
)
python -m venv "%INSTALL_DIR%\venv"
if %errorLevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created
echo.

REM Step 4: Install package
echo [4/8] Installing ADCP Recorder...
"%INSTALL_DIR%\venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
"%INSTALL_DIR%\venv\Scripts\pip.exe" install --quiet adcp-recorder
if %errorLevel% neq 0 (
    echo ERROR: Failed to install package
    pause
    exit /b 1
)
echo Package installed
echo.

REM Step 5: Configure application
echo [5/8] Creating configuration...

REM List available COM ports
echo Available COM ports:
"%INSTALL_DIR%\venv\Scripts\adcp-recorder.exe" list-ports
echo.

set /p SERIAL_PORT="Enter COM port (e.g., COM3): "
if "%SERIAL_PORT%"=="" set SERIAL_PORT=COM3

set /p BAUD_RATE="Enter baud rate (default: 9600): "
if "%BAUD_RATE%"=="" set BAUD_RATE=9600

REM Create configuration file
(
echo {
echo     "serial_port": "%SERIAL_PORT%",
echo     "baudrate": %BAUD_RATE%,
echo     "timeout": 1.0,
echo     "output_dir": "C:\\ADCP_Data",
echo     "log_level": "INFO",
echo     "db_path": null
echo }
) > "%CONFIG_DIR%\config.json"

echo Configuration created at: %CONFIG_DIR%\config.json
echo.

REM Step 6: Install Windows service (if admin)
echo [6/8] Windows service setup...
if %ADMIN%==1 (
    REM Check if pywin32 is installed
    "%INSTALL_DIR%\venv\Scripts\python.exe" -c "import win32serviceutil" >nul 2>&1
    if %errorLevel% neq 0 (
        echo Installing pywin32 for service support...
        "%INSTALL_DIR%\venv\Scripts\pip.exe" install --quiet pywin32
    )
    
    echo Installing Windows service...
    "%INSTALL_DIR%\venv\Scripts\python.exe" -m adcp_recorder.service.win_service install
    if %errorLevel% neq 0 (
        echo WARNING: Service installation failed
        echo You can run the recorder manually with: adcp-recorder start
    ) else (
        echo Configuring service to start automatically...
        sc config adcp-recorder start= auto
        echo Service installed successfully
    )
) else (
    echo Skipping service installation (requires Administrator)
    echo To install service later, run as Administrator:
    echo   "%INSTALL_DIR%\venv\Scripts\python.exe" -m adcp_recorder.service.win_service install
)
echo.

REM Step 7: Create shortcuts
echo [7/8] Creating shortcuts...

REM Create start script
(
echo @echo off
echo "%INSTALL_DIR%\venv\Scripts\adcp-recorder.exe" start
echo pause
) > "%INSTALL_DIR%\Start ADCP Recorder.bat"

REM Create configuration script
(
echo @echo off
echo "%INSTALL_DIR%\venv\Scripts\adcp-recorder.exe" configure
echo pause
) > "%INSTALL_DIR%\Configure ADCP Recorder.bat"

REM Create status script
(
echo @echo off
echo "%INSTALL_DIR%\venv\Scripts\adcp-recorder.exe" status
echo pause
) > "%INSTALL_DIR%\Check Status.bat"

echo Shortcuts created in: %INSTALL_DIR%
echo.

REM Step 8: Verify installation
echo [8/8] Verifying installation...
"%INSTALL_DIR%\venv\Scripts\adcp-recorder.exe" --help >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Installation verification failed
    pause
    exit /b 1
)
echo Installation verified
echo.

echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Configuration:
echo   Config file: %CONFIG_DIR%\config.json
echo   Data directory: %DATA_DIR%
echo   Serial port: %SERIAL_PORT%
echo   Baud rate: %BAUD_RATE%
echo.
echo Shortcuts:
echo   %INSTALL_DIR%\Start ADCP Recorder.bat
echo   %INSTALL_DIR%\Configure ADCP Recorder.bat
echo   %INSTALL_DIR%\Check Status.bat
echo.
if %ADMIN%==1 (
    echo Service Management:
    echo   Start service:   sc start adcp-recorder
    echo   Stop service:    sc stop adcp-recorder
    echo   Service status:  sc query adcp-recorder
    echo.
    set /p START_SERVICE="Start service now? (Y/N): "
    if /i "!START_SERVICE!"=="Y" (
        sc start adcp-recorder
        echo Service started
    )
) else (
    echo To run the recorder:
    echo   Double-click: %INSTALL_DIR%\Start ADCP Recorder.bat
    echo   Or run: "%INSTALL_DIR%\venv\Scripts\adcp-recorder.exe" start
)
echo.
echo Next Steps:
echo   1. Verify configuration: %INSTALL_DIR%\Check Status.bat
echo   2. Start recording (if not using service)
echo   3. Check data: %DATA_DIR%
echo.
pause
