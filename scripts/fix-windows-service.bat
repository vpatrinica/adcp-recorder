@echo off
REM Fix script to reinstall Windows service with correct Python path

echo ========================================
echo ADCP Recorder Service Reinstallation
echo ========================================
echo.

REM Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    pause
    exit /b 1
)

set INSTALL_DIR=C:\Program Files\ADCP-Recorder

echo [1/4] Stopping and removing existing service...
sc stop ADCPRecorder >nul 2>&1
timeout /t 2 /nobreak >nul
"%INSTALL_DIR%\venv\Scripts\python.exe" -m adcp_recorder.service.win_service remove >nul 2>&1
sc delete ADCPRecorder >nul 2>&1
echo Service removed
echo.

echo [2/4] Verifying pywin32 installation...
"%INSTALL_DIR%\venv\Scripts\python.exe" -c "import servicemanager; print('OK: servicemanager available')"
if %errorLevel% neq 0 (
    echo ERROR: servicemanager not available
    echo Please run: "%INSTALL_DIR%\venv\Scripts\python.exe" "%INSTALL_DIR%\venv\Scripts\pywin32_postinstall.py" -install
    pause
    exit /b 1
)
echo.

echo [3/4] Installing service with explicit Python path...
REM Use --startup auto to set automatic startup
"%INSTALL_DIR%\venv\Scripts\python.exe" -m adcp_recorder.service.win_service --startup auto install
if %errorLevel% neq 0 (
    echo ERROR: Service installation failed
    echo.
    echo Trying alternative method...
    REM Try using pywin32's InstallService directly with PythonService
    "%INSTALL_DIR%\venv\Scripts\python.exe" "%INSTALL_DIR%\venv\Scripts\pywin32_postinstall.py" -install
    "%INSTALL_DIR%\venv\Scripts\python.exe" -m adcp_recorder.service.win_service install
)
echo.

echo [4/4] Configuring service...
sc config ADCPRecorder start= auto
sc config ADCPRecorder binPath= "\"%INSTALL_DIR%\venv\Scripts\python.exe\" -m adcp_recorder.service.win_service"
echo Service configured
echo.

echo ========================================
echo Service Reinstallation Complete
echo ========================================
echo.
echo To start the service:
echo   sc start ADCPRecorder
echo.
echo To check service status:
echo   sc query ADCPRecorder
echo.
echo To view service logs:
echo   Check Event Viewer or C:\ADCP_Data\logs\service.log
echo.
pause
