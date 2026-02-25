@echo off
REM
REM install-windows.bat - Install ADCP Recorder on Windows using Servy
REM
REM This script installs ADCP Recorder and optionally sets up Windows service using Servy.
REM Run as Administrator for service installation.
REM
REM Layout:
REM   C:\s1000\src\adcp-recorder   - Git clone of the project
REM   C:\s1000\conf                - Configuration files
REM   C:\s1000\data                - Runtime data, parquet, db
REM   C:\s1000\data\logs           - Service log files
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

REM --------------------------------------------------------
REM  Directory layout
REM --------------------------------------------------------
set BASE_DIR=C:\s1000
set SRC_DIR=%BASE_DIR%\src
set INSTALL_DIR=%SRC_DIR%\adcp-recorder
set DATA_DIR=%BASE_DIR%\data
set CONFIG_DIR=%BASE_DIR%\conf
set LOG_DIR=%DATA_DIR%\logs
set SERVY_INSTALL_PATH=C:\Program Files\Servy
set REPO_URL=https://github.com/vpatrinica/adcp-recorder

echo Base directory:          %BASE_DIR%
echo Source directory:        %INSTALL_DIR%
echo Data directory:          %DATA_DIR%
echo Configuration directory: %CONFIG_DIR%
echo Log directory:           %LOG_DIR%
echo.

REM Create directories
if not exist "%BASE_DIR%" mkdir "%BASE_DIR%"
if not exist "%SRC_DIR%" mkdir "%SRC_DIR%"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo Directories created
echo.

REM Step 1: Check and install Git
echo [1/9] Checking Git installation...

git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Git not found, installing via winget...

    winget --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo ERROR: winget not found
        echo Please install App Installer from Microsoft Store or install Git manually
        pause
        exit /b 1
    )

    winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        echo WARNING: Git installation may have failed, checking...
    )

    REM Refresh environment
    where refreshenv >nul 2>&1
    if %errorLevel% equ 0 (
        refreshenv >nul 2>&1
    )

    REM Manually add Git to PATH for this session
    set "PATH=%PATH%;C:\Program Files\Git\bin;C:\Program Files\Git\cmd"

    git --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo ERROR: Git not found after installation
        echo Please restart your terminal and try again, or install manually from:
        echo https://git-scm.com/downloads
        pause
        exit /b 1
    )
)

for /f "tokens=*" %%i in ('git --version 2^>^&1') do set GIT_VERSION=%%i
echo %GIT_VERSION%
echo.

REM Step 2: Clone the repository
echo [2/9] Cloning ADCP Recorder repository...

if exist "%INSTALL_DIR%\.git" (
    echo.
    echo ========================================
    echo   EXISTING INSTALLATION DETECTED
    echo ========================================
    echo.
    set /p UPGRADE="Upgrade existing installation? [Y/N]: "
    if /i "!UPGRADE!" neq "Y" (
        echo Installation cancelled.
        pause
        exit /b 0
    )
    echo.
    echo Pulling latest changes...
    pushd "%INSTALL_DIR%"
    git pull
    popd
) else (
    echo Cloning from %REPO_URL%...
    git clone "%REPO_URL%" "%INSTALL_DIR%"
    if %errorLevel% neq 0 (
        echo ERROR: Failed to clone repository
        pause
        exit /b 1
    )
)
echo Repository ready
echo.

REM Step 3: Check and install Python 3.13
echo [3/9] Checking Python installation...

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
    echo Python 3.13+ not found, installing via winget...

    winget --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo ERROR: winget not found
        echo Please install App Installer from Microsoft Store or Windows 11
        echo Or manually install Python 3.13+ from https://www.python.org/downloads/
        pause
        exit /b 1
    )

    winget install --id Python.Python.3.13 -e --silent --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        echo WARNING: Python installation may have failed, checking if Python is available...
    )

    REM Refresh environment
    where refreshenv >nul 2>&1
    if %errorLevel% equ 0 (
        refreshenv >nul 2>&1
    )

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

REM Step 4: Check and install VC++ Redistributables
echo [4/9] Checking Visual C++ Redistributables...

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

REM Step 5: Create virtual environment
echo [5/9] Creating virtual environment...
if exist "%INSTALL_DIR%\.venv" (
    echo Stopping any running ADCP Recorder processes...

    REM Try to stop Servy-managed service first
    set "SERVY_PATH=%SERVY_INSTALL_PATH%\servy-cli.exe"
    if exist "!SERVY_PATH!" (
        "!SERVY_PATH!" stop --name="ADCPRecorder" --quiet 2>nul
    ) else (
        servy-cli stop --name="ADCPRecorder" --quiet 2>nul
    )

    REM Kill any running adcp-recorder processes
    taskkill /IM adcp-recorder.exe /F >nul 2>&1

    REM Wait for file handles to be released
    echo Waiting for processes to terminate...
    timeout /t 3 /nobreak >nul

    echo Removing existing virtual environment...
    rmdir /s /q "%INSTALL_DIR%\.venv" 2>nul
    if exist "%INSTALL_DIR%\.venv" (
        echo WARNING: Could not fully remove old virtual environment
        echo Some files may be locked. Please close any programs using ADCP Recorder.
        echo.
        set /p FORCE_CONTINUE="Continue anyway? [Y/N]: "
        if /i "!FORCE_CONTINUE!" neq "Y" (
            echo Installation cancelled.
            pause
            exit /b 1
        )
    )
)
py -3.13 -m venv "%INSTALL_DIR%\.venv"
if %errorLevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created
echo.

REM Step 6: Install package and dependencies
echo [6/9] Installing ADCP Recorder and dependencies...
py -3.13 -m pip install --upgrade pip --quiet

REM Install package from local clone
"%INSTALL_DIR%\.venv\Scripts\pip.exe" install --quiet "%INSTALL_DIR%"
if %errorLevel% neq 0 (
    echo ERROR: Failed to install package
    pause
    exit /b 1
)

echo Package and dependencies installed
echo.

REM Step 7: Configure application
echo [7/9] Creating configuration...

REM List available COM ports
echo Available COM ports:
"%INSTALL_DIR%\.venv\Scripts\adcp-recorder.exe" list-ports
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
echo     "output_dir": "C:\\s1000\\data",
echo     "log_level": "INFO",
echo     "db_path": null
echo }
) > "%CONFIG_DIR%\config.json"

echo Configuration created at: %CONFIG_DIR%\config.json
echo.

REM Step 8: Install Windows service using Servy (if admin)
echo [8/9] Windows service setup using Servy...
if %ADMIN% equ 1 (
    REM Define Servy CLI path - use direct path for same-session reliability
    set "SERVY_CLI=%SERVY_INSTALL_PATH%\servy-cli.exe"
    set "SERVY_FOUND=0"

    REM Check if Servy is already installed (try direct path first)
    if exist "!SERVY_CLI!" (
        set "SERVY_FOUND=1"
    ) else (
        REM Try PATH-based servy-cli
        servy-cli --version >nul 2>&1
        if !errorLevel! equ 0 (
            set "SERVY_CLI=servy-cli"
            set "SERVY_FOUND=1"
        )
    )

    if !SERVY_FOUND! equ 0 (
        echo Installing Servy service manager via winget...
        winget install -e --id aelassas.Servy --silent --accept-package-agreements --accept-source-agreements
        if !errorLevel! neq 0 (
            echo WARNING: Servy installation may have failed
            echo You can install it manually: winget install -e --id aelassas.Servy
        ) else (
            REM After installation, use direct path
            set "SERVY_CLI=%SERVY_INSTALL_PATH%\Servy\servy-cli.exe"
            if exist "!SERVY_CLI!" set "SERVY_FOUND=1"
        )
    )

    REM Verify Servy is available
    if !SERVY_FOUND! equ 0 (
        echo WARNING: Servy CLI not found
        echo Please restart your terminal after Servy installation and run this script again.
        echo Or install Servy manually from: https://github.com/aelassas/servy/releases
        echo.
        echo You can run the recorder manually with: adcp-recorder start
        goto :skip_service
    )

    echo Servy is available: !SERVY_CLI!

    REM Check if service already exists and remove it
    "!SERVY_CLI!" status --name="ADCPRecorder" --quiet >nul 2>&1
    if !errorLevel! equ 0 (
        echo Removing existing ADCPRecorder service...
        "!SERVY_CLI!" stop --name="ADCPRecorder" --quiet >nul 2>&1
        timeout /t 2 /nobreak >nul
        "!SERVY_CLI!" uninstall --name="ADCPRecorder" --quiet
        timeout /t 2 /nobreak >nul
    )

    echo Installing Windows service via Servy...
    "!SERVY_CLI!" install --quiet ^
        --name="ADCPRecorder" ^
        --displayName="ADCP Recorder Service" ^
        --description="NMEA Telemetry Recorder for Nortek ADCP Instruments" ^
        --path="%INSTALL_DIR%\.venv\Scripts\python.exe" ^
        --startupDir="%INSTALL_DIR%" ^
        --params="-m adcp_recorder.service.supervisor" ^
        --env="PROGRAMDATA=%PROGRAMDATA%" ^
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

    if !errorLevel! neq 0 (
        echo WARNING: Service installation failed
        echo You can run the recorder manually with: adcp-recorder start
    ) else (
        echo Service installed successfully via Servy
    )

    REM Generate Servy JSON configs for API and Dashboard
    echo.
    echo Generating Servy configuration files...

    REM Get dashboard.py path
    for /f "delims=" %%i in ('"%INSTALL_DIR%\.venv\Scripts\python.exe" -c "import adcp_recorder.ui.dashboard as d; print(d.__file__)"') do set DASH_PATH=%%i

    REM adcp-recorder.json
    (
    echo {
    echo   "Name": "ADCPRecorder",
    echo   "DisplayName": "ADCP Recorder Service",
    echo   "Description": "NMEA Telemetry Recorder for Nortek ADCP Instruments",
    echo   "ExecutablePath": "%INSTALL_DIR:\=\\%\\.venv\\Scripts\\python.exe",
    echo   "StartupDirectory": "%INSTALL_DIR:\=\\%",
    echo   "Parameters": "-m adcp_recorder.service.supervisor",
    echo   "StartupType": 2,
    echo   "Priority": 2,
    echo   "StdoutPath": "%DATA_DIR:\=\\%\\logs\\stdout.log",
    echo   "StderrPath": "%DATA_DIR:\=\\%\\logs\\stderr.log",
    echo   "EnableRotation": false,
    echo   "RotationSize": 10,
    echo   "EnableDateRotation": true,
    echo   "DateRotationType": 0,
    echo   "MaxRotations": 30,
    echo   "EnableHealthMonitoring": true,
    echo   "HeartbeatInterval": 30,
    echo   "MaxFailedChecks": 3,
    echo   "RecoveryAction": 1,
    echo   "MaxRestartAttempts": 5,
    echo   "EnvironmentVariables": "PROGRAMDATA=C:\\\\ProgramData",
    echo   "RunAsLocalSystem": true,
    echo   "PreLaunchTimeoutSeconds": 30,
    echo   "PreLaunchRetryAttempts": 0,
    echo   "PreLaunchIgnoreFailure": false,
    echo   "EnableDebugLogs": false,
    echo   "StartTimeout": 10,
    echo   "StopTimeout": 10
    echo }
    ) > "%CONFIG_DIR%\adcp-recorder.json"

    REM adcp-api.json
    (
    echo {
    echo   "Name": "ADCP-API",
    echo   "DisplayName": "ADCP Recorder API",
    echo   "Description": "REST API for ADCP Recorder data access",
    echo   "ExecutablePath": "%INSTALL_DIR:\=\\%\\.venv\\Scripts\\uvicorn.exe",
    echo   "StartupDirectory": "%INSTALL_DIR:\=\\%",
    echo   "Parameters": "adcp_recorder.api.main:app --host 0.0.0.0 --port 8000",
    echo   "StartupType": 2,
    echo   "Priority": 2,
    echo   "StdoutPath": "%DATA_DIR:\=\\%\\logs\\api_stdout.log",
    echo   "StderrPath": "%DATA_DIR:\=\\%\\logs\\api_stderr.log",
    echo   "EnableRotation": false,
    echo   "RotationSize": 10,
    echo   "EnableDateRotation": true,
    echo   "DateRotationType": 0,
    echo   "MaxRotations": 0,
    echo   "EnableHealthMonitoring": false,
    echo   "HeartbeatInterval": 30,
    echo   "MaxFailedChecks": 3,
    echo   "RecoveryAction": 1,
    echo   "MaxRestartAttempts": 3,
    echo   "RunAsLocalSystem": true,
    echo   "PreLaunchTimeoutSeconds": 30,
    echo   "PreLaunchRetryAttempts": 0,
    echo   "PreLaunchIgnoreFailure": false,
    echo   "EnableDebugLogs": false,
    echo   "StartTimeout": 10,
    echo   "StopTimeout": 5
    echo }
    ) > "%CONFIG_DIR%\adcp-api.json"

    REM adcp-dashboard.json
    (
    echo {
    echo   "Name": "ADCP-Dashboard",
    echo   "DisplayName": "ADCP Recorder Dashboard",
    echo   "Description": "Interactive Streamlit dashboard for ADCP analysis",
    echo   "ExecutablePath": "%INSTALL_DIR:\=\\%\\.venv\\Scripts\\streamlit.exe",
    echo   "StartupDirectory": "%INSTALL_DIR:\=\\%",
    echo   "Parameters": "run \"%INSTALL_DIR:\=\\%\\adcp_recorder\\ui\\dashboard.py\" --browser.gatherUsageStats false --server.headless true",
    echo   "StartupType": 2,
    echo   "Priority": 2,
    echo   "StdoutPath": "%DATA_DIR:\=\\%\\logs\\dashboard_stdout.log",
    echo   "StderrPath": "%DATA_DIR:\=\\%\\logs\\dashboard_stderr.log",
    echo   "EnableRotation": false,
    echo   "RotationSize": 10,
    echo   "EnableDateRotation": true,
    echo   "DateRotationType": 0,
    echo   "MaxRotations": 0,
    echo   "EnableHealthMonitoring": true,
    echo   "HeartbeatInterval": 30,
    echo   "MaxFailedChecks": 3,
    echo   "RecoveryAction": 1,
    echo   "MaxRestartAttempts": 3,
    echo   "RunAsLocalSystem": true,
    echo   "PreLaunchTimeoutSeconds": 30,
    echo   "PreLaunchRetryAttempts": 0,
    echo   "PreLaunchIgnoreFailure": false,
    echo   "EnableDebugLogs": false,
    echo   "StartTimeout": 10,
    echo   "StopTimeout": 5
    echo }
    ) > "%CONFIG_DIR%\adcp-dashboard.json"

    echo Servy configs generated in: %CONFIG_DIR%
    goto :after_service_setup
)
echo Skipping service installation (requires Administrator)
echo To install service later, run as Administrator:
echo   servy-cli install --name="ADCPRecorder" --path="%INSTALL_DIR%\.venv\Scripts\python.exe" --params="-m adcp_recorder.service.supervisor"

:skip_service
:after_service_setup
echo.

REM Step 9: Create shortcuts
echo [9/9] Creating shortcuts...

REM Create start script
(
echo @echo off
echo "%INSTALL_DIR%\.venv\Scripts\adcp-recorder.exe" start
echo pause
) > "%INSTALL_DIR%\Start ADCP Recorder.bat"

REM Create configuration script
(
echo @echo off
echo "%INSTALL_DIR%\.venv\Scripts\adcp-recorder.exe" configure
echo pause
) > "%INSTALL_DIR%\Configure ADCP Recorder.bat"

REM Create status script
(
echo @echo off
echo "%INSTALL_DIR%\.venv\Scripts\adcp-recorder.exe" status
echo pause
) > "%INSTALL_DIR%\Check Status.bat"

echo Shortcuts created in: %INSTALL_DIR%
echo.

REM Verify installation
echo Verifying installation...
"%INSTALL_DIR%\.venv\Scripts\adcp-recorder.exe" --help >nul 2>&1
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
echo Layout:
echo   Source:         %INSTALL_DIR%
echo   Configuration: %CONFIG_DIR%
echo   Data:          %DATA_DIR%
echo   Logs:          %LOG_DIR%
echo.
echo Configuration:
echo   Config file: %CONFIG_DIR%\config.json
echo   Serial port: %SERIAL_PORT%
echo   Baud rate: %BAUD_RATE%
echo.
echo Shortcuts:
echo   %INSTALL_DIR%\Start ADCP Recorder.bat
echo   %INSTALL_DIR%\Configure ADCP Recorder.bat
echo   %INSTALL_DIR%\Check Status.bat
echo.
if %ADMIN% equ 1 (
    echo Service Management (Servy):
    echo   Start service:   servy-cli start --name="ADCPRecorder"
    echo   Stop service:    servy-cli stop --name="ADCPRecorder"
    echo   Service status:  servy-cli status --name="ADCPRecorder"
    echo   Restart:         servy-cli restart --name="ADCPRecorder"
    echo.
    echo Or use sc.exe commands:
    echo   Start:   sc start ADCPRecorder
    echo   Stop:    sc stop ADCPRecorder
    echo   Query:   sc query ADCPRecorder
    echo.
    set /p START_SERVICE="Start service now? [Y/N]: "
    if /i "!START_SERVICE!"=="Y" (
        servy-cli start --name="ADCPRecorder" --quiet
        echo Service started
    )
) else (
    echo To run the recorder:
    echo   Double-click: %INSTALL_DIR%\Start ADCP Recorder.bat
    echo   Or run: "%INSTALL_DIR%\.venv\Scripts\adcp-recorder.exe" start
)
echo.
echo Next Steps:
echo   1. Verify configuration: %INSTALL_DIR%\Check Status.bat
echo   2. Start recording (if not using service)
echo   3. Check data: %DATA_DIR%
echo.
pause
