@echo off
setlocal enabledelayedexpansion

echo ========================================
echo ADCP Recorder - FULL INSTALLER
echo ========================================

REM --- Check for Administrator privileges ---
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] WARNING: Not running as Administrator.
    echo Service installation will be SKIPPED.
    set ADMIN=0
) else (
    echo [OK] Running as Administrator.
    set ADMIN=1
)

REM --- Directory Layout ---
set "BASE_DIR=C:\s1000"
set "SRC_DIR=%BASE_DIR%\src"
set "INSTALL_DIR=%SRC_DIR%\adcp-recorder"
set "DATA_DIR=%BASE_DIR%\data"
set "CONFIG_DIR=%BASE_DIR%\conf"
set "LOG_DIR=%DATA_DIR%\logs"
set "REPO_URL=https://github.com/vpatrinica/adcp-recorder"
set "SERVY_INSTALL_PATH=C:\Program Files\Servy"
set "SERVY_VERSION=6.8"

REM Create directories
echo [1/9] Creating Directories...
for %%d in ("%BASE_DIR%" "%SRC_DIR%" "%DATA_DIR%" "%CONFIG_DIR%" "%LOG_DIR%") do (
    if not exist "%%~d" (
        mkdir "%%~d"
        if !errorLevel! neq 0 (
            echo [!] ERROR: Failed to create %%~d
            pause & exit /b 1
        )
    )
)
echo [OK] Directories ready.

REM --- Step 2: Force Git ---
echo [2/9] Checking Git...
where git >nul 2>&1
if %errorLevel% neq 0 (
    git --version >nul 2>&1
    if !errorLevel! neq 0 (
        echo Git missing. Downloading installer...
        set "GIT_INSTALLER=%TEMP%\git_setup.exe"
        powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-64-bit.exe' -OutFile '!GIT_INSTALLER!'"
        if not exist "!GIT_INSTALLER!" (
            echo [!] ERROR: Failed to download Git installer.
            pause & exit /b 1
        )
        echo Installing Git silently...
        start /wait "" "!GIT_INSTALLER!" /VERYSILENT /NORESTART
        del "!GIT_INSTALLER!" 2>nul
        set "PATH=%PATH%;C:\Program Files\Git\cmd"
        echo [OK] Git installed.
    )
) else (
    echo [OK] Git found.
)

REM --- Step 3: Clone/Update Repo ---
echo [3/9] Handling Repository...
if exist "%INSTALL_DIR%\.git" (
    echo Updating existing repository...
    pushd "%INSTALL_DIR%" && git pull && popd
) else (
    echo Cloning repository...
    git clone "%REPO_URL%" "%INSTALL_DIR%"
)
if %errorLevel% neq 0 (
    echo [!] WARNING: Repository operation had issues.
)

REM --- Step 4: Check and install VC++ Redistributables ---
echo [4/10] Checking Visual C++ Redistributables...
where winget >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: winget not found, skipping VC++ redistributable check
    echo You may need to install Visual C++ Redistributables manually
    echo Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
) else (
    echo Installing/updating Visual C++ Redistributables...
    winget install --id Microsoft.VCRedist.2015+.x64 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    winget install --id Microsoft.VCRedist.2015+.x86 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    echo VC++ Redistributables checked/installed
)

REM --- Step 5: Python 3.13 ---
echo [5/10] Checking Python 3.13...
py -3.13 --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Python 3.13 missing. Downloading...
    set "PY_INSTALLER=%TEMP%\python_setup.exe"
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe' -OutFile '!PY_INSTALLER!'"
    if not exist "!PY_INSTALLER!" (
        echo [!] ERROR: Failed to download Python installer.
        pause & exit /b 1
    )
    start /wait "" "!PY_INSTALLER!" /quiet InstallAllUsers=1 PrependPath=1
    del "!PY_INSTALLER!" 2>nul
    echo [!] Python installed. PLEASE RE-RUN THIS SCRIPT to pick up new PATH.
    pause & exit /b 1
) else (
    echo [OK] Python 3.13 found.
)

REM --- Step 6: Virtual Env ---
echo [6/10] Creating Virtual Environment...
if exist "%INSTALL_DIR%\.venv" rmdir /s /q "%INSTALL_DIR%\.venv"
py -3.13 -m venv "%INSTALL_DIR%\.venv"
if %errorLevel% neq 0 (
    echo [!] ERROR: Failed to create virtual environment.
    pause & exit /b 1
)
echo Upgrading pip...
"%INSTALL_DIR%\.venv\Scripts\python.exe" -m pip install --upgrade pip
echo Installing ADCP Recorder...
"%INSTALL_DIR%\.venv\Scripts\pip.exe" install "%INSTALL_DIR%"
if %errorLevel% neq 0 (
    echo [!] ERROR: pip install failed.
    pause & exit /b 1
)
echo [OK] Virtual environment ready.

REM --- Step 6: Skip (reserved) ---

REM --- Step 8: Config ---
echo [8/10] Creating Config...
set /p PORT="Enter COM port (e.g. COM3): "
if "!PORT!"=="" set PORT=COM3
(
echo { "serial_port": "!PORT!", "baudrate": 9600, "output_dir": "C:\\s1000\\data" }
) > "%CONFIG_DIR%\config.json"
echo [OK] Config written to %CONFIG_DIR%\config.json

REM --- Step 8: Servy Service Setup ---
if %ADMIN% equ 1 (
    echo [9/10] Installing Windows Services via Servy...

    REM Check if Servy CLI is already available
    set "SERVY_EXE="
    where servy-cli >nul 2>&1
    if !errorLevel! equ 0 (
        echo [OK] Servy CLI found in PATH.
        set "SERVY_EXE=servy-cli"
    ) else if exist "!SERVY_INSTALL_PATH!\servy-cli.exe" (
        echo [OK] Servy CLI found at !SERVY_INSTALL_PATH!
        set "SERVY_EXE=!SERVY_INSTALL_PATH!\servy-cli.exe"
    )

    REM Get dashboard.py path
    for /f "delims=" %%i in ('"%INSTALL_DIR%\.venv\Scripts\python.exe" -c "import adcp_recorder.ui.dashboard as d; print(d.__file__)"') do set DASH_PATH=%%i

    REM If not found, install Servy using the official installer
    if "!SERVY_EXE!"=="" (
        echo Servy not found. Downloading Servy v!SERVY_VERSION! installer...
        set "SERVY_INSTALLER=%TEMP%\servy-installer.exe"
        set "SERVY_URL=https://github.com/aelassas/servy/releases/download/v!SERVY_VERSION!/servy-!SERVY_VERSION!-net48-x64-installer.exe"

        echo Download URL: !SERVY_URL!
        powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '!SERVY_URL!' -OutFile '!SERVY_INSTALLER!' -UseBasicParsing"

        if not exist "!SERVY_INSTALLER!" (
            echo [!] ERROR: Failed to download Servy installer.
            echo.
            echo Manual install options:
            echo   1. Download from: https://github.com/aelassas/servy/releases
            echo   2. Or run: winget install -e --id aelassas.Servy
            echo.
            echo After installing Servy, re-run this script.
            goto :skip_service
        )

        echo Installing Servy silently...
        start /wait "" "!SERVY_INSTALLER!" /VERYSILENT /NORESTART
        set "INSTALL_RESULT=!errorLevel!"
        del "!SERVY_INSTALLER!" 2>nul

        if !INSTALL_RESULT! neq 0 (
            echo [!] WARNING: Servy installer returned error code !INSTALL_RESULT!
            echo Trying alternative: winget install...
            winget install -e --id aelassas.Servy --silent >nul 2>&1
        )

        REM Refresh PATH to pick up newly installed Servy
        set "PATH=%PATH%;C:\Program Files\Servy"

        REM Re-check for servy-cli
        where servy-cli >nul 2>&1
        if !errorLevel! equ 0 (
            set "SERVY_EXE=servy-cli"
        ) else if exist "C:\Program Files\Servy\servy-cli.exe" (
            set "SERVY_EXE=C:\Program Files\Servy\servy-cli.exe"
        ) else (
            echo [!] ERROR: Servy installation failed. servy-cli.exe not found.
            echo.
            echo Please install Servy manually:
            echo   1. Visit: https://github.com/aelassas/servy/releases
            echo   2. Download servy-!SERVY_VERSION!-net48-x64-installer.exe
            echo   3. Run the installer
            echo   4. Re-run this script
            goto :skip_service
        )
        echo [OK] Servy installed successfully.
    )

    REM Remove existing service if present
    echo Checking for existing ADCP Recorder service...
    "!SERVY_EXE!" status --name="ADCPRecorder" --quiet >nul 2>&1
    if !errorLevel! equ 0 (
        echo Removing existing service...
        "!SERVY_EXE!" stop --name="ADCPRecorder" --quiet >nul 2>&1
        timeout /t 2 /nobreak >nul
        "!SERVY_EXE!" uninstall --name="ADCPRecorder" --quiet >nul 2>&1
        timeout /t 2 /nobreak >nul
    )

    REM Register ADCP Recorder Service
    echo Registering ADCP Recorder Service...
    "!SERVY_EXE!" install --quiet ^
        --name="ADCPRecorder" ^
        --displayName="ADCP Recorder Service" ^
        --description="NMEA Telemetry Recorder for Nortek ADCP Instruments" ^
        --path="%INSTALL_DIR%\.venv\Scripts\python.exe" ^
        --startupDir="%INSTALL_DIR%" ^
        --params="-m adcp_recorder.service.supervisor" ^
        --stdout="%LOG_DIR%\stdout.log" ^
        --stderr="%LOG_DIR%\stderr.log" ^
        --enableDateRotation ^
        --dateRotationType="Daily" ^
        --startupType="Automatic"

    REM Register ADCP API Service
    echo Registering ADCP API Service...
    "!SERVY_EXE!" install --quiet ^
        --name="ADCP-API" ^
        --displayName="ADCP Recorder API" ^
        --description="REST API for ADCP Recorder data access" ^
        --path="%INSTALL_DIR%\.venv\Scripts\uvicorn.exe" ^
        --startupDir="%INSTALL_DIR%" ^
        --params="adcp_recorder.api.main:app --host 0.0.0.0 --port 8000" ^
        --stdout="%LOG_DIR%\api_stdout.log" ^
        --stderr="%LOG_DIR%\api_stderr.log" ^
        --enableDateRotation ^
        --dateRotationType="Daily" ^
        --startupType="Automatic"

    REM Register ADCP Dashboard Service
    echo Registering ADCP Dashboard Service...
    "!SERVY_EXE!" install --quiet ^
        --name="ADCP-Dashboard" ^
        --displayName="ADCP Recorder Dashboard" ^
        --description="Interactive Streamlit dashboard for ADCP analysis" ^
        --path="%INSTALL_DIR%\.venv\Scripts\streamlit.exe" ^
        --startupDir="%INSTALL_DIR%" ^
        --params="run \"!DASH_PATH!\" --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats false --server.headless true" ^
        --stdout="%LOG_DIR%\dashboard_stdout.log" ^
        --stderr="%LOG_DIR%\dashboard_stderr.log" ^
        --enableDateRotation ^
        --dateRotationType="Daily" ^
        --startupType="Automatic"

    REM Generate Servy JSON configs
    echo Generating Servy configuration files...
    
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
    echo   "StdoutPath": "%DATA_DIR:\=\\%\\logs\\stdout.log",
    echo   "StderrPath": "%DATA_DIR:\=\\%\\logs\\stderr.log",
    echo   "EnableDateRotation": true,
    echo   "DateRotationType": 0,
    echo   "EnvironmentVariables": "PROGRAMDATA=C:\\\\ProgramData"
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
    echo   "StdoutPath": "%DATA_DIR:\=\\%\\logs\\api_stdout.log",
    echo   "StderrPath": "%DATA_DIR:\=\\%\\logs\\api_stderr.log",
    echo   "EnableDateRotation": true,
    echo   "DateRotationType": 0
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
    echo   "Parameters": "run \"!DASH_PATH:\=\\%\\\" --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats false --server.headless true",
    echo   "StartupType": 2,
    echo   "StdoutPath": "%DATA_DIR:\=\\%\\logs\\dashboard_stdout.log",
    echo   "StderrPath": "%DATA_DIR:\=\\%\\logs\\dashboard_stderr.log",
    echo   "EnableDateRotation": true,
    echo   "DateRotationType": 0
    echo }
    ) > "%CONFIG_DIR%\adcp-dashboard.json"

    if !errorLevel! equ 0 (
        echo [OK] Service installed successfully.
        echo.
        echo Service Management:
        echo   Start:    servy-cli start --name="ADCPRecorder"
        echo   Stop:     servy-cli stop --name="ADCPRecorder"
        echo   Status:   servy-cli status --name="ADCPRecorder"
        echo   Restart:  servy-cli restart --name="ADCPRecorder"
    ) else (
        echo [!] WARNING: Service registration failed. Error code: !errorLevel!
        echo You can try manually with:
        echo   servy-cli install --name="ADCPRecorder" --path="%INSTALL_DIR%\.venv\Scripts\python.exe" --params="-m adcp_recorder.service.supervisor"
    )
) else (
    echo [9/10] SKIPPED - Service install requires Administrator.
)
:skip_service

REM --- Step 10: Shortcuts ---
echo [10/10] Creating Shortcuts...
(
echo @echo off
echo "%INSTALL_DIR%\.venv\Scripts\adcp-recorder.exe" start
echo pause
) > "%BASE_DIR%\START_RECORDER.bat"

echo.
echo ========================================
echo INSTALLATION COMPLETE
echo ========================================
echo.
echo Base directory:  %BASE_DIR%
echo Config:          %CONFIG_DIR%\config.json
echo Logs:            %LOG_DIR%
echo Start recorder:  %BASE_DIR%\START_RECORDER.bat
echo.
pause