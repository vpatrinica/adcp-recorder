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

REM Step 1: Check and install Python 3.13
echo [1/9] Checking Python installation...

REM Check if Python 3.13+ is already available
set PYTHON_OK=0
py -3.13 --version >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=2" %%i in ('py -3.13 --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo Python 3.13+ already installed: %PYTHON_VERSION%
    set PYTHON_OK=1
) else (
    REM Check if any python is available and check version
    python --version >nul 2>&1
    if %errorLevel% equ 0 (
        python -c "import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)" >nul 2>&1
        if %errorLevel% equ 0 (
            for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
            echo Python 3.13+ already installed: %PYTHON_VERSION%
            set PYTHON_OK=1
        )
    )
)

REM Install Python 3.13 if not present or version too old
if %PYTHON_OK% equ 0 (
    echo Python 3.13+ not found, installing...
    
    REM Check if winget is available
    winget --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo ERROR: winget not found
        echo Please install App Installer from Microsoft Store or Windows 11
        echo Or manually install Python 3.13+ from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    echo Installing Python 3.13 via winget...
    winget install --id Python.Python.3.13 -e --silent --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        echo WARNING: Python installation may have failed, checking if Python is available...
    )
    
    REM Refresh environment (note: refreshenv may not be available in all environments)
    where refreshenv >nul 2>&1
    if %errorLevel% equ 0 (
        refreshenv >nul 2>&1
    )
    
    REM Verify Python 3.13 is now available
    py -3.13 --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo ERROR: Python 3.13 not found after installation
        echo Please restart your terminal and try again, or install manually from:
        echo https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    for /f "tokens=2" %%i in ('py -3.13 --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo Python installed successfully: %PYTHON_VERSION%
)
echo.

REM Step 2: Check and install VC++ Redistributables
echo [2/9] Checking Visual C++ Redistributables...

REM Check if winget is available
winget --version >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: winget not found, skipping VC++ redistributable check
    echo You may need to install Visual C++ Redistributables manually
    echo Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
) else (
    echo Installing/updating Visual C++ Redistributables...
    echo Processing x64...
    winget install --id Microsoft.VCRedist.2015+.x64 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    echo Processing x86...
    winget install --id Microsoft.VCRedist.2015+.x86 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    echo VC++ Redistributables checked/installed
)
echo.

REM Step 3: Set installation directories
echo [3/9] Setting up directories...
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

REM Step 4: Create virtual environment
echo [4/9] Creating virtual environment...
if exist "%INSTALL_DIR%\venv" (
    echo Removing existing virtual environment...
    rmdir /s /q "%INSTALL_DIR%\venv"
)
py -3.13 -m venv "%INSTALL_DIR%\venv"
if %errorLevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created
echo.

REM Step 5: Install package and dependencies
echo [5/9] Installing ADCP Recorder and dependencies...
py -3.13 -m pip install --upgrade pip --quiet

REM Install package with Windows extras (includes pywin32)
"%INSTALL_DIR%\venv\Scripts\pip.exe" install --quiet "adcp-recorder[win]"
if %errorLevel% neq 0 (
    echo ERROR: Failed to install package
    pause
    exit /b 1
)

REM Run pywin32 post-install script to register service components
echo Configuring pywin32 for Windows services...
"%INSTALL_DIR%\venv\Scripts\python.exe" "%INSTALL_DIR%\venv\Scripts\pywin32_postinstall.py" -install >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: pywin32 post-install script failed, trying alternative method...
    REM Try to find and run the script in the pywin32_system32 directory
    for /f "delims=" %%i in ('dir /b /s "%INSTALL_DIR%\venv\Lib\site-packages\pywin32_system32" 2^>nul') do (
        if exist "%%i\pywin32_postinstall.py" (
            "%INSTALL_DIR%\venv\Scripts\python.exe" "%%i\pywin32_postinstall.py" -install >nul 2>&1
        )
    )
)

echo Package and dependencies installed
echo.

REM Step 6: Configure application
echo [6/9] Creating configuration...

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

REM Step 7: Install Windows service (if admin)
echo [7/9] Windows service setup...
if %ADMIN%==1 (
    REM pywin32 should already be installed via [win] extras
    "%INSTALL_DIR%\venv\Scripts\python.exe" -c "import win32serviceutil" >nul 2>&1
    if %errorLevel% neq 0 (
        echo ERROR: pywin32 not found (should have been installed automatically)
        echo Attempting manual installation...
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

REM Step 8: Create shortcuts
echo [8/9] Creating shortcuts...

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

REM Step 9: Verify installation
echo [9/9] Verifying installation...
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
